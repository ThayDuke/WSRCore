import os
import sys
sys.dont_write_bytecode = True
import shutil
import argparse
import json
import tempfile
import wsr_common
import subprocess

def run_doctor_preflight(package_root):
    """Run wsr_doctor.py as a subprocess to ensure the package passes health gates."""
    doctor_path = os.path.join(package_root, "scripts", "wsr_doctor.py")
    if not os.path.exists(doctor_path):
        return False, "wsr_doctor.py not found in scripts", wsr_common.EXIT_FAIL_FINDING
    
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    
    res = subprocess.run([sys.executable, doctor_path, "--path", package_root], capture_output=True, env=env)
    if res.returncode != 0:
        return False, res.stdout.decode('utf-8', errors='ignore'), res.returncode
    return True, "", wsr_common.EXIT_SUCCESS

def load_adapter_config(package_root, adapter_name, manifest):
    """Locate and load the specified adapter json config."""
    # Find adapter path in manifest adapters list
    adapter_rel = None
    for ad in manifest.get("adapters", []):
        if adapter_name in ad:
            adapter_rel = ad
            break
            
    if not adapter_rel:
        # Fallback assumption
        adapter_rel = f"adapters/{adapter_name}.json"
        
    adapter_path = os.path.join(package_root, adapter_rel)
    if not os.path.exists(adapter_path):
        raise FileNotFoundError(f"Adapter config not found at {adapter_path}")
        
    with open(adapter_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_target_root(adapter_config, cli_target_root):
    """Resolve target root path from CLI argument or environment variable."""
    if cli_target_root:
        return os.path.abspath(cli_target_root)
        
    env_var = adapter_config.get("targetRootEnvironmentVariable")
    if env_var:
        env_val = os.environ.get(env_var)
        if env_val:
            return os.path.abspath(env_val)
            
    if adapter_config.get("requiresExplicitTargetRoot", True):
        raise ValueError(f"Target root resolution failed. Adapter requires explicit target root or environment variable '{env_var}'")
        
    return None

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
    """Construct a deployment plan containing detailed operations for target state."""
    plan = []
    
    # We filter artifacts that target this adapter
    adapter_id = adapter_config["adapterId"]
    
    for art in manifest.get("artifacts", []):
        if adapter_id not in art.get("targets", []):
            continue
            
        # Determine destination path relative to target_root
        # Based on artifactMappings and source structure
        src_rel = art["source"]
        src_abs = os.path.join(package_root, src_rel)
        
        # Decide destination subdirectory prefix
        dest_prefix = ""
        art_type = art["type"]
        mappings = adapter_config.get("artifactMappings", {})
        
        # Map folders or names
        if art_type in mappings:
            dest_prefix = mappings[art_type]
                
        # Resolve destination path safely
        if not dest_prefix:
            dest_rel = src_rel
        elif dest_prefix.endswith('/') or dest_prefix.endswith('\\'):
            # Directory target: remove first segment of src_rel
            parts = src_rel.replace('\\', '/').split('/')
            if len(parts) > 1:
                sub_path = '/'.join(parts[1:])
            else:
                sub_path = src_rel
            dest_rel = os.path.join(dest_prefix, sub_path)
        else:
            # Type mapped directly to a file name
            dest_rel = dest_prefix
            
        # Check target containment
        try:
            dest_abs = wsr_common.safe_resolve_path(target_root, dest_rel)
        except ValueError as e:
            raise ValueError(f"Adapter '{adapter_config.get('adapterId')}' mapping containment violation for artifact '{art['id']}' (mapped: '{dest_rel}'): {e}")
            
        # Current status
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
            "relative_destination": dest_rel.replace('\\', '/'),
            "current_state": current_state,
            "desired_state": desired_state,
            "action": action,
            "src_checksum": src_checksum,
            "dest_checksum": dest_checksum,
            "mutable": art.get("mutable", True)
        })
        
    return plan

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
    report["plan"] = plan
    
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
    import time
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
                
        # Step 4: Success - clean up backups (journaled only)
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
        if os.path.exists(journal_path):
            try:
                with open(journal_path, "r", encoding="utf-8") as jf:
                    j_dict = json.load(jf)
                j_staged = [(item["stage"], item["dest"]) for item in j_dict.get("staged_files", [])]
                j_backups = [(item["dest"], item["backup"]) for item in j_dict.get("backup_files", [])]
            except Exception as j_err:
                report["execution_log"].append(f"Failed to read transaction journal: {j_err}")
                
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
