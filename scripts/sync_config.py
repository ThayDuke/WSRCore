import os
import sys
sys.dont_write_bytecode = True
import shutil
import argparse
import json
import wsr_common
import subprocess
import hashlib
import time

def run_doctor_preflight(package_root):
    """Run wsr_doctor.py as a subprocess to ensure the package passes health gates."""
    doctor_path = os.path.join(package_root, "scripts", "wsr_doctor.py")
    if not os.path.exists(doctor_path):
        return False, "wsr_doctor.py not found in scripts", wsr_common.EXIT_FAIL_FINDING
    
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    
    res = subprocess.run([sys.executable, doctor_path, "--path", package_root, "--source-mode"], capture_output=True, env=env)
    if res.returncode != 0:
        return False, res.stdout.decode('utf-8', errors='ignore'), res.returncode
    return True, "", wsr_common.EXIT_SUCCESS

def load_adapter_config(package_root, adapter_name, manifest):
    """Load an exact v2 adapter and reject ambiguous legacy contracts."""
    adapter_rel = f"adapters/{adapter_name}.json"
    if adapter_rel not in manifest.get("adapters", []):
        raise ValueError(f"Adapter '{adapter_name}' is not declared by the manifest")
    adapter_path = os.path.join(package_root, adapter_rel)
    if not os.path.exists(adapter_path):
        raise FileNotFoundError(f"Adapter config not found at {adapter_path}")
    with open(adapter_path, "r", encoding="utf-8") as f:
        adapter = json.load(f)
    required = {
        "schemaVersion", "adapterId", "runtimeFamily", "enabled",
        "supportLevel", "defaultTargetRoot", "targetRootEnvironmentVariable",
        "requiresExplicitTargetRoot", "logicalRoots", "discoveryPrecedence",
        "artifactMappings", "routerContract", "activeMarkerContract",
        "unsupportedFeatures"
    }
    if adapter.get("schemaVersion") != 2 or set(adapter) != required:
        raise ValueError(f"Adapter '{adapter_name}' does not satisfy the exact v2 contract")
    if adapter.get("adapterId") != adapter_name:
        raise ValueError(f"Adapter identity mismatch: expected '{adapter_name}'")
    return adapter

def get_target_root(adapter_config, cli_target_root):
    """Resolve an explicit, environment, or declared default target root."""
    if cli_target_root:
        root = os.path.realpath(os.path.abspath(os.path.expanduser(cli_target_root)))
    else:
        root = None
    env_var = adapter_config.get("targetRootEnvironmentVariable")
    if root is None and env_var:
        env_val = os.environ.get(env_var)
        if env_val:
            root = os.path.realpath(os.path.abspath(os.path.expanduser(env_val)))
    if root is None and adapter_config.get("defaultTargetRoot"):
        root = os.path.realpath(os.path.abspath(os.path.expanduser(adapter_config["defaultTargetRoot"])))
    if root is None and adapter_config.get("requiresExplicitTargetRoot", True):
        raise ValueError(f"Target root resolution failed. Adapter requires explicit target root or environment variable '{env_var}'")
    if root is None:
        raise ValueError("Target root resolution failed; implicit current-directory fallback is forbidden")
    if "user-home-install" in adapter_config.get("unsupportedFeatures", []) and root == os.path.realpath(os.path.expanduser("~")):
        raise PermissionError(f"Adapter '{adapter_config['adapterId']}' forbids deployment to the user home")
    return root

def resolve_logical_roots(target_root, adapter_config):
    """Resolve every logical root beneath the selected target boundary."""
    resolved = {}
    for name, relative_path in adapter_config.get("logicalRoots", {}).items():
        if not wsr_common.validate_relative_path(relative_path):
            raise ValueError(f"Logical root '{name}' must be target-relative: {relative_path}")
        resolved[name] = wsr_common.safe_resolve_path(target_root, relative_path)
    return resolved

def select_mapping(artifact, mappings):
    """Prefer artifact-specific mappings, then fall back to artifact type."""
    for mapping in mappings:
        if mapping.get("artifactId") == artifact.get("id"):
            return mapping
    for mapping in mappings:
        if mapping.get("artifactType") == artifact.get("type"):
            return mapping
    return None

def render_router(package_root, manifest):
    package_root = os.path.realpath(os.path.abspath(package_root))
    template_path = os.path.join(package_root, "bootstrap", "router.md.template")
    with open(template_path, "r", encoding="utf-8") as stream:
        rendered = stream.read()
    manifest_hash = wsr_common.calculate_sha256(os.path.join(package_root, "WSR_MANIFEST.json"))
    replacements = {
        "{{PACKAGE_NAME}}": manifest.get("packageName", "WSR-Core"),
        "{{VERSION}}": manifest.get("version", "unknown"),
        "{{BUILD_ID}}": manifest.get("buildId", "unknown"),
        "{{ACTIVE_SOURCE_ROOT}}": package_root.replace("\\", "/"),
        "{{MANIFEST_SHA256}}": manifest_hash,
    }
    for token, value in replacements.items():
        rendered = rendered.replace(token, str(value))
    if "{{" in rendered or "}}" in rendered:
        raise ValueError("Router template contains unresolved placeholders")
    return rendered

def compute_checksums(package_root, manifest):
    """Load or calculate checksums for manifest inventory."""
    checksums = {}
    checksums_file = manifest.get("checksumsFile", "WSR_CHECKSUMS.json")
    checksums_path = os.path.join(package_root, checksums_file)
    
    if os.path.exists(checksums_path):
        try:
            with open(checksums_path, "r", encoding="utf-8") as f:
                checksums = json.load(f)
        except:
            pass
            
    # Calculate JIT if missing
    for art in manifest.get("artifacts", []):
        src_path = os.path.join(package_root, art["source"])
        if art["source"] not in checksums and os.path.exists(src_path):
            try:
                checksums[art["source"]] = wsr_common.calculate_sha256(src_path)
            except:
                pass
    return checksums

def build_deployment_plan(package_root, target_root, manifest, adapter_config, checksums):
    """Construct a collision-free v2 plan rooted at logical destinations."""
    target_root = os.path.realpath(os.path.abspath(target_root))
    plan = []
    logical_roots = resolve_logical_roots(target_root, adapter_config)
    mappings = adapter_config.get("artifactMappings", [])
    destinations = {}

    for art in manifest.get("artifacts", []):
        mapping = select_mapping(art, mappings)
        if mapping is None:
            continue
        src_rel = art["source"]
        src_abs = os.path.join(package_root, src_rel)
        root_name = mapping.get("logicalRoot")
        if root_name not in logical_roots:
            raise ValueError(f"Unknown logical root '{root_name}' for artifact '{art['id']}'")
        dest_prefix = mapping.get("relativePath", "")
        if dest_prefix.endswith('/') or dest_prefix.endswith('\\'):
            parts = src_rel.replace('\\', '/').split('/')
            dest_rel = os.path.join(dest_prefix, *parts[1:]) if len(parts) > 1 else os.path.join(dest_prefix, parts[0])
        else:
            dest_rel = dest_prefix or os.path.basename(src_rel)
        try:
            dest_abs = wsr_common.safe_resolve_path(logical_roots[root_name], dest_rel)
        except ValueError as e:
            raise ValueError(f"Adapter '{adapter_config.get('adapterId')}' mapping containment violation for artifact '{art['id']}' (mapped: '{dest_rel}'): {e}")
        normalized_dest = os.path.normcase(os.path.realpath(dest_abs))
        if normalized_dest in destinations:
            raise ValueError(f"Destination collision: '{art['id']}' and '{destinations[normalized_dest]}' map to '{dest_abs}'")
        destinations[normalized_dest] = art["id"]
        current_state = "Missing"
        desired_state = "Unchanged"
        action = "unchanged"
        dest_checksum = "N/A"
        
        src_checksum = checksums.get(src_rel, "N/A")
        if src_checksum == "N/A" and os.path.exists(src_abs):
            src_checksum = wsr_common.calculate_sha256(src_abs)
            
        if os.path.exists(dest_abs):
            current_state = "Exists"
            dest_checksum = wsr_common.calculate_sha256(dest_abs)
            if src_checksum != dest_checksum:
                current_state = "Drift"
                desired_state = "Update"
                action = "update"
        else:
            desired_state = "Create"
            action = "create"
            
        plan.append({
            "id": art["id"],
            "source_path": src_abs,
            "destination_path": dest_abs,
            "relative_destination": os.path.relpath(dest_abs, target_root).replace('\\', '/'),
            "current_state": current_state,
            "desired_state": desired_state,
            "action": action,
            "src_checksum": src_checksum,
            "dest_checksum": dest_checksum,
            "mutable": art.get("mutable", True)
        })

    router = adapter_config.get("routerContract", {})
    if router.get("type") == "absolute":
        router_rel = router.get("path", "")
        if not wsr_common.validate_relative_path(router_rel):
            raise ValueError(f"Router path must be target-relative: {router_rel}")
        router_dest = wsr_common.safe_resolve_path(target_root, router_rel)
        normalized_dest = os.path.normcase(os.path.realpath(router_dest))
        if normalized_dest in destinations:
            raise ValueError(f"Router destination collision with '{destinations[normalized_dest]}': {router_dest}")
        rendered = render_router(package_root, manifest)
        rendered_hash = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        existing_hash = wsr_common.calculate_sha256(router_dest) if os.path.exists(router_dest) else "N/A"
        plan.append({
            "id": "active-router", "source_path": None,
            "destination_path": router_dest,
            "relative_destination": os.path.relpath(router_dest, target_root).replace('\\', '/'),
            "current_state": "Exists" if os.path.exists(router_dest) else "Missing",
            "desired_state": "Unchanged" if existing_hash == rendered_hash else ("Update" if os.path.exists(router_dest) else "Create"),
            "action": "unchanged" if existing_hash == rendered_hash else ("update" if os.path.exists(router_dest) else "create"),
            "src_checksum": rendered_hash, "dest_checksum": existing_hash,
            "mutable": True, "rendered_content": rendered
        })
    return plan

def public_operation(operation):
    """Remove internal rendered payloads from reports."""
    return {key: value for key, value in operation.items() if key != "rendered_content"}

def calculate_inventory_hash(plan):
    rows = [f"{op['id']}:{op['src_checksum']}:{op['relative_destination']}" for op in plan]
    return hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")).hexdigest()

def main():
    parser = argparse.ArgumentParser(description="WSR Configuration Deployment Synchronizer")
    parser.add_argument('--adapter', required=True, help="Target platform adapter name (e.g. gemini, codex)")
    parser.add_argument('--target-root', default=None, help="Explicit target root directory")
    parser.add_argument('--json', action='store_true', help="Output deployment plan as JSON")
    parser.add_argument('--apply', action='store_true', help="Execute changes to target configuration")
    parser.add_argument('--approval-token', default=None, help="Approval token matching manifest buildId")
    parser.add_argument('--allow-review', action='store_true', help="Bypass Review package restriction")
    
    args = parser.parse_args()
    
    is_json = args.json
    is_apply = args.apply
    
    package_root = wsr_common.get_package_root()
    
    # 1. Load manifest
    try:
        manifest = wsr_common.load_manifest(package_root)
    except Exception as e:
        if is_json:
            wsr_common.print_json_report({"status": "FAIL", "message": f"Manifest load failure: {e}"})
        else:
            print(f"[-] Error: Failed to load manifest: {e}", file=sys.stderr)
        sys.exit(wsr_common.EXIT_INVALID_ARGS)
        
    build_id = manifest.get("buildId")
    manifest_status = manifest.get("status", "Review")
    
    # 2. Run Preflight Health Doctor check
    doctor_ok, doctor_err, doc_exit_code = run_doctor_preflight(package_root)
    if not doctor_ok:
        if is_json:
            wsr_common.print_json_report({"status": "FAIL", "message": "Preflight doctor check failed", "details": doctor_err})
        else:
            print("[-] Safety Gate: Doctor check failed. Package is unhealthy!", file=sys.stderr)
            print(doctor_err, file=sys.stderr)
        sys.exit(doc_exit_code)
        
    # 3. Load Adapter
    try:
        adapter_config = load_adapter_config(package_root, args.adapter, manifest)
    except Exception as e:
        if is_json:
            wsr_common.print_json_report({"status": "FAIL", "message": str(e)})
        else:
            print(f"[-] Error: {e}", file=sys.stderr)
        sys.exit(wsr_common.EXIT_INVALID_ARGS)
        
    # Check if adapter is enabled
    if not adapter_config.get("enabled", False):
        if is_json:
            wsr_common.print_json_report({"status": "FAIL", "message": f"Adapter '{args.adapter}' is disabled"})
        else:
            print(f"[-] Safety Gate: Adapter '{args.adapter}' is disabled in configuration.", file=sys.stderr)
        sys.exit(wsr_common.EXIT_SAFETY_REJECTION)
        
    # Resolve Target Root
    try:
        target_root = get_target_root(adapter_config, args.target_root)
        if not target_root:
            raise ValueError("Target root could not be resolved.")
    except PermissionError as e:
        if is_json:
            wsr_common.print_json_report({"status": "REJECTED", "message": str(e)})
        else:
            print(f"[-] Safety Gate: {e}", file=sys.stderr)
        sys.exit(wsr_common.EXIT_SAFETY_REJECTION)
    except Exception as e:
        if is_json:
            wsr_common.print_json_report({"status": "FAIL", "message": str(e)})
        else:
            print(f"[-] Error: {e}", file=sys.stderr)
        sys.exit(wsr_common.EXIT_INVALID_ARGS)
        
    
    # 5. Build Deployment Plan
    report = {
        "status": "PLAN",
        "adapter": args.adapter,
        "target_root": target_root,
        "build_id": build_id,
        "total_operations": 0,
        "changes_count": 0,
        "plan": [],
        "execution_log": []
    }
    try:
        checksums = compute_checksums(package_root, manifest)
        plan = build_deployment_plan(package_root, target_root, manifest, adapter_config, checksums)
    except ValueError as e:
        report["status"] = "REJECTED"
        report["message"] = str(e)
        if is_json:
            wsr_common.print_json_report(report)
        else:
            print(f"[-] Safety Gate: Rejection! {e}", file=sys.stderr)
        sys.exit(wsr_common.EXIT_SAFETY_REJECTION)
    
    # Check if anything to deploy
    changes_needed = [op for op in plan if op["action"] != "unchanged"]
    
    report["total_operations"] = len(plan)
    report["changes_count"] = len(changes_needed)
    report["plan"] = [public_operation(op) for op in plan]
    
    if not is_apply:
        if is_json:
            wsr_common.print_json_report(report)
        else:
            print("="*60)
            print(f"WSR DEPLOYMENT PLAN - DRY RUN ({args.adapter.upper()})")
            print("="*60)
            print(f"Target Root: {target_root}")
            print(f"Build ID:    {build_id}")
            print(f"Changes:     {len(changes_needed)} / {len(plan)} files")
            print("-"*60)
            for op in plan:
                print(f" - [{op['action'].upper()}] {op['relative_destination']} (Id: {op['id']})")
            print("="*60)
            print("To execute changes, run with --apply --approval-token <buildId>")
            print("="*60)
        sys.exit(wsr_common.EXIT_SUCCESS)
        
    # APPLY MODE
    # 0. Manifest Status Verification (Review Package apply check)
    if manifest_status == "Review" and not args.allow_review:
        report["status"] = "REJECTED"
        report["message"] = "Applying a package in 'Review' status requires '--allow-review'"
        if is_json:
            wsr_common.print_json_report(report)
        else:
            print("[-] Safety Gate: Package is in 'Review' status. Deploying config requires '--allow-review'", file=sys.stderr)
        sys.exit(wsr_common.EXIT_SAFETY_REJECTION)

    # 1. Approval Token Verification
    if not args.approval_token or args.approval_token != build_id:
        report["status"] = "REJECTED"
        report["message"] = "Invalid or missing --approval-token"
        if is_json:
            wsr_common.print_json_report(report)
        else:
            print(f"[-] Safety Gate: Rejection! Token '{args.approval_token}' does not match buildId '{build_id}'", file=sys.stderr)
        sys.exit(wsr_common.EXIT_SAFETY_REJECTION)
        
    # 2. Start Transaction
    report["status"] = "EXECUTING"
    
    # Generate unique transaction ID using buildId and timestamp
    transaction_id = f"{build_id}_{int(time.time())}"
    staging_dir = os.path.join(target_root, f".wsr_staging_{transaction_id}")
    
    # Reject if staging folder already exists
    if os.path.exists(staging_dir):
        report["status"] = "REJECTED"
        report["message"] = f"Staging directory already exists: {staging_dir}"
        if is_json:
            wsr_common.print_json_report(report)
        else:
            print(f"[-] Safety Gate: Staging directory already exists: {staging_dir}", file=sys.stderr)
        sys.exit(wsr_common.EXIT_IO_TRANSACTION_ERROR)
        
    os.makedirs(staging_dir, exist_ok=True)
    
    staged_files = []
    backup_files = []
    
    journal_path = os.path.join(staging_dir, "transaction_journal.json")
    
    try:
        # Step 1: Copy to staging and verify source checksum JIT
        for op in changes_needed:
            src_path = op["source_path"]
            src_checksum = op["src_checksum"]
            
            stage_file = os.path.join(staging_dir, op["id"])
            if "rendered_content" in op:
                wsr_common.atomic_write_text(stage_file, op["rendered_content"])
            else:
                shutil.copy2(src_path, stage_file)
            staged_files.append((stage_file, op["destination_path"]))
            
            # Verify staging checksum
            staged_chk = wsr_common.calculate_sha256(stage_file)
            if staged_chk != src_checksum:
                raise RuntimeError(f"Checksum mismatch in staging for {op['id']}: expected {src_checksum}, got {staged_chk}")
                
        # Write initial journal
        journal_data = {
            "transaction_id": transaction_id,
            "staged_files": [{"stage": sf, "dest": dp} for sf, dp in staged_files],
            "backup_files": []
        }
        with open(journal_path, "w", encoding="utf-8") as jf:
            json.dump(journal_data, jf, indent=2)
            
        # Step 2: Backup existing files (rename)
        for stage_file, dest_path in staged_files:
            # Check target containment via realpath/commonpath before writing
            wsr_common.safe_resolve_path(target_root, os.path.relpath(dest_path, target_root))
            
            if os.path.exists(dest_path):
                # Unique backup name utilizing transaction_id
                dest_dir = os.path.dirname(dest_path)
                dest_name = os.path.basename(dest_path)
                backup_path = os.path.join(dest_dir, f"{dest_name}.wsr_backup_{transaction_id}_tmp")
                
                # Reject if backup path already exists to avoid overwriting unmanaged data
                if os.path.exists(backup_path):
                    raise RuntimeError(f"Backup file path already exists: {backup_path}")
                    
                os.replace(dest_path, backup_path)
                backup_files.append((dest_path, backup_path))
                
                # Update journal on disk immediately
                journal_data["backup_files"].append({"dest": dest_path, "backup": backup_path})
                with open(journal_path, "w", encoding="utf-8") as jf:
                    json.dump(journal_data, jf, indent=2)
                    
        # Step 3: Copy staged files to final destination and verify checksum
        for stage_file, dest_path in staged_files:
            # Revalidate containment immediately before write
            wsr_common.safe_resolve_path(target_root, os.path.relpath(dest_path, target_root))
            
            # Create subdirs if needed
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(stage_file, dest_path)
            
            # Verify destination checksum
            final_chk = wsr_common.calculate_sha256(dest_path)
            matching_op = next(op for op in plan if op["destination_path"] == dest_path)
            expected_chk = matching_op["src_checksum"]
            if final_chk != expected_chk:
                raise RuntimeError(f"Checksum verification failed at destination: {dest_path}. Expected {expected_chk}, got {final_chk}")
                
        # Step 3.5: Write the adapter-declared active marker with journal tracking
        manifest_version = manifest.get("version", "1.0.0")
        manifest_sha = wsr_common.calculate_sha256(os.path.join(package_root, "WSR_MANIFEST.json"))
        marker_relative_path = adapter_config.get("activeMarkerContract", {}).get("path", "")
        if not wsr_common.validate_relative_path(marker_relative_path):
            raise RuntimeError(f"Active marker path must be target-relative: {marker_relative_path}")
        active_marker_path = wsr_common.safe_resolve_path(target_root, marker_relative_path)
        marker_backup_path = None
        if os.path.exists(active_marker_path):
            marker_backup_path = f"{active_marker_path}.wsr_backup_{transaction_id}_tmp"
            os.replace(active_marker_path, marker_backup_path)
            journal_data["marker_backup"] = marker_backup_path
            with open(journal_path, "w", encoding="utf-8") as jf:
                json.dump(journal_data, jf, indent=2)

        logical_roots = {
            name: os.path.relpath(path, target_root).replace('\\', '/')
            for name, path in resolve_logical_roots(target_root, adapter_config).items()
        }
        router_operation = next((op for op in plan if op["id"] == "active-router"), None)
        active_marker_content = {
            "schemaVersion": 1,
            "adapterIdentity": args.adapter,
            "packageVersion": manifest_version,
            "buildId": build_id,
            "manifestHash": manifest_sha,
            "inventoryHash": calculate_inventory_hash(plan),
            "routerHash": router_operation["src_checksum"] if router_operation else "none",
            "logicalRoots": logical_roots,
            "installTimestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "transactionId": transaction_id
        }
        marker_stage_path = os.path.join(staging_dir, "active-marker.json")
        marker_json = json.dumps(active_marker_content, indent=2)
        wsr_common.atomic_write_text(marker_stage_path, marker_json)
        marker_stage_hash = wsr_common.calculate_sha256(marker_stage_path)
        journal_data["marker_stage"] = marker_stage_path
        journal_data["marker_destination"] = active_marker_path
        journal_data["marker_checksum"] = marker_stage_hash
        journal_data["marker_write_started"] = True
        with open(journal_path, "w", encoding="utf-8") as jf:
            json.dump(journal_data, jf, indent=2)
        os.makedirs(os.path.dirname(active_marker_path), exist_ok=True)
        shutil.copy2(marker_stage_path, active_marker_path)
        if wsr_common.calculate_sha256(active_marker_path) != marker_stage_hash:
            raise RuntimeError("Active marker checksum verification failed")
        journal_data["active_marker_written"] = True
        with open(journal_path, "w", encoding="utf-8") as jf:
            json.dump(journal_data, jf, indent=2)

        # Step 4: Success - clean up backups (journaled only)
        if marker_backup_path and os.path.exists(marker_backup_path):
            os.remove(marker_backup_path)
        for dest_path, backup_path in backup_files:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
        # Clean own staging directory only (not rmtree on complete destination)
        shutil.rmtree(staging_dir, ignore_errors=True)
        
        report["status"] = "SUCCESS"
        if is_json:
            wsr_common.print_json_report(report)
        else:
            print(f"[+] Successfully deployed {len(changes_needed)} changes to {target_root}")
            
    except Exception as e:
        # TRANSACTION FAILED - ROLLBACK!
        report["status"] = "ROLLBACK"
        report["error"] = str(e)
        
        rollback_errors = []
        
        # Read journal if exists to guarantee we only rollback what was recorded
        j_staged = staged_files
        j_backups = backup_files
        marker_backup = None
        marker_written = False
        if os.path.exists(journal_path):
            try:
                with open(journal_path, "r", encoding="utf-8") as jf:
                    j_dict = json.load(jf)
                j_staged = [(item["stage"], item["dest"]) for item in j_dict.get("staged_files", [])]
                j_backups = [(item["dest"], item["backup"]) for item in j_dict.get("backup_files", [])]
                marker_backup = j_dict.get("marker_backup")
                marker_written = j_dict.get("active_marker_written", False) or j_dict.get("marker_write_started", False)
            except Exception as j_err:
                report["execution_log"].append(f"Failed to read transaction journal: {j_err}")
                
        # 0. Rollback active marker if affected
        marker_relative_path = adapter_config.get("activeMarkerContract", {}).get("path", "")
        target_marker = wsr_common.safe_resolve_path(target_root, marker_relative_path)
        if marker_backup and os.path.exists(marker_backup):
            try:
                if os.path.exists(target_marker):
                    os.remove(target_marker)
                os.replace(marker_backup, target_marker)
            except Exception as mb_err:
                rollback_errors.append(f"Restore marker failed: {mb_err}")
        elif marker_written and os.path.exists(target_marker):
            try:
                os.remove(target_marker)
            except Exception as mb_err:
                rollback_errors.append(f"Cleanup marker failed: {mb_err}")

        # 1. Restore backups in REVERSE order
        for dest_path, backup_path in reversed(j_backups):
            if os.path.exists(backup_path):
                try:
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    os.replace(backup_path, dest_path)
                except Exception as rollback_err:
                    rollback_errors.append(f"Restore failed for {dest_path}: {rollback_err}")
                    
        # 2. Remove successfully copied new files that were created (not backed up) in REVERSE order
        for stage_file, dest_path in reversed(j_staged):
            was_backed_up = any(dest == dest_path for dest, _ in j_backups)
            if not was_backed_up and os.path.exists(dest_path):
                try:
                    os.remove(dest_path)
                except Exception as rm_err:
                    rollback_errors.append(f"Remove failed for newly created {dest_path}: {rm_err}")
                    
        # 3. Clean up own staging directory
        shutil.rmtree(staging_dir, ignore_errors=True)
        
        if rollback_errors:
            report["status"] = "PARTIAL_FAIL"
            report["rollback_errors"] = rollback_errors
            report["execution_log"].extend(rollback_errors)
            
        if is_json:
            wsr_common.print_json_report(report)
        else:
            print(f"[-] Transaction Error: {e}", file=sys.stderr)
            if rollback_errors:
                print(f"[-] Rollback Partial Fail: {rollback_errors}", file=sys.stderr)
            else:
                print("[-] Rollback executed successfully.", file=sys.stderr)
                
        sys.exit(wsr_common.EXIT_IO_TRANSACTION_ERROR)
        
    sys.exit(wsr_common.EXIT_SUCCESS)

if __name__ == '__main__':
    main()
