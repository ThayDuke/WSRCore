import argparse
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True

import wsr_common
import sync_config


def load_json(path):
    with open(path, "r", encoding="utf-8", errors="strict") as handle:
        return json.load(handle)


def resolve_source(source_root, lock_file):
    resolved, origin, diags = wsr_common.resolve_active_root(source_root, lock_file)
    lock = None
    if origin.startswith("lock:"):
        lock_path = origin.split(":", 1)[1]
        if os.path.isfile(lock_path):
            lock = load_json(lock_path)
    return resolved, origin, lock


def validate_identity(source_root, lock, allow_review=False):
    manifest_path = os.path.join(source_root, "WSR_MANIFEST.json")
    manifest = load_json(manifest_path)
    if manifest.get("status") != "Released" and not (allow_review and manifest.get("status") == "Review"):
        raise ValueError("Only Released packages may be loaded unless --allow-review is explicit")

    manifest_sha = wsr_common.calculate_sha256(manifest_path)
    if lock:
        expected = {
            "version": manifest.get("version"),
            "buildId": manifest.get("buildId"),
            "manifestSha256": manifest_sha,
        }
        mismatches = [key for key, value in expected.items() if lock.get(key) != value]
        if mismatches:
            raise ValueError(f"Source lock identity mismatch: {mismatches}")
    return manifest, manifest_sha


def run_json(command):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        env=env,
        check=False,
    )
    payload = None
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = None
    return result.returncode, payload, result.stderr.strip()


def run_doctor(source_root):
    doctor = os.path.join(source_root, "scripts", "wsr_doctor.py")
    return run_json([sys.executable, doctor, "--path", source_root, "--source-mode", "--strict", "--json"])


def run_runtime_doctor(source_root, adapter_name, target_root):
    doctor = os.path.join(source_root, "scripts", "wsr_doctor.py")
    return run_json([
        sys.executable, doctor, "--path", source_root, "--runtime-mode",
        "--adapter", adapter_name, "--target-root", target_root, "--strict", "--json"
    ])


def run_deep_audit(source_root):
    audit = os.path.join(source_root, "scripts", "wsr_audit.py")
    return run_json([sys.executable, audit, "--path", source_root, "--mode", "deep", "--json"])


def resolve_target(source_root, manifest, adapter_name, target_root):
    adapter_path = os.path.join(source_root, "adapters", f"{adapter_name}.json")
    adapter = load_json(adapter_path)
    if not adapter.get("enabled"):
        raise ValueError(f"Adapter '{adapter_name}' is disabled")
    try:
        return sync_config.get_target_root(adapter, target_root)
    except ValueError:
        if not target_root and adapter.get("requiresExplicitTargetRoot"):
            return None
        raise


def read_active_identity(source_root, target_root, adapter_name):
    if not target_root or not adapter_name:
        return None
    adapter = load_json(os.path.join(source_root, "adapters", f"{adapter_name}.json"))
    marker_path = wsr_common.safe_resolve_path(target_root, adapter["activeMarkerContract"]["path"])
    if not os.path.isfile(marker_path):
        return None
    try:
        data = load_json(marker_path)
        required = {
            "schemaVersion", "adapterIdentity", "packageVersion", "buildId",
            "manifestHash", "inventoryHash", "routerHash", "logicalRoots",
            "installTimestamp", "transactionId"
        }
        if set(data) != required or data.get("schemaVersion") != 1 or data.get("adapterIdentity") != adapter_name:
            return None
        data["version"] = data["packageVersion"]
        return data
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def version_key(manifest):
    version = tuple(int(part) for part in re.findall(r"\d+", manifest.get("version", "")))
    build_match = re.search(r"-V(\d+)(?:-|$)", manifest.get("buildId", ""), re.IGNORECASE)
    build_number = int(build_match.group(1)) if build_match else 0
    return version, build_number


def check_drift(source_root, adapter_name, target_root):
    if not target_root:
        return "NOT_CHECKED", None, "Target root unavailable"
    sync_script = os.path.join(source_root, "scripts", "sync_config.py")
    command = [
        sys.executable,
        sync_script,
        "--adapter",
        adapter_name,
        "--target-root",
        target_root,
        "--json",
    ]
    code, payload, error = run_json(command)
    if code != 0 or not payload:
        return "NOT_CHECKED", None, error or "Sync dry-run failed"
    changes = int(payload.get("changes_count", 0))
    return ("DRIFTED" if changes else "CLEAN"), changes, None


def build_load_plan(source_root, manifest, adapter_name, profile="startup", command_name=None, capability_ids=None):
    load_plan = []
    seen = set()

    def add_entry(rel_path, role, required=True, priority=10, capability_owner=None):
        abs_path = os.path.realpath(os.path.join(source_root, rel_path))
        if os.path.commonpath([os.path.realpath(source_root), abs_path]) != os.path.realpath(source_root):
            raise ValueError(f"Load plan path escapes source root: {rel_path}")
        if abs_path in seen:
            return
        if not os.path.exists(abs_path):
            if required:
                raise ValueError(f"Required load plan file missing: {rel_path} ({abs_path})")
            return
        seen.add(abs_path)
        load_plan.append({
            "absolutePath": abs_path,
            "role": role,
            "originRoot": source_root,
            "sha256": wsr_common.calculate_sha256(abs_path),
            "required": required,
            "loadPhase": profile,
            "precedence": priority,
            "capabilityOwner": capability_owner
        })

    context_path = os.path.join(source_root, manifest.get("contextFile", "WSR_CONTEXT.json"))
    context_data = {}
    if os.path.exists(context_path):
        try:
            with open(context_path, "r", encoding="utf-8") as f:
                context_data = json.load(f)
        except Exception as e:
            raise ValueError(f"Context JSON parse error in {context_path}: {e}")

    for policy_path in context_data.get("policyFiles", []):
        add_entry(policy_path, "policy", required=True, priority=1)
    add_entry("WSR_MANIFEST.json", "config", required=True, priority=2)
    add_entry(manifest.get("contextFile", "WSR_CONTEXT.json"), "config", required=True, priority=2)
    adapter_path = f"adapters/{adapter_name}.json"
    add_entry(adapter_path, "adapter", required=True, priority=2)

    if profile in ("command", "task") and command_name:
        clean_cmd = command_name.lstrip("/")
        cmd_map = context_data.get("commandMap", {})
        cmd_info = cmd_map.get(clean_cmd) or manifest.get("commands", {}).get(clean_cmd)
        if not cmd_info:
            raise ValueError(f"Unknown command requested: {command_name}")
        wf_path = cmd_info.get("workflow") or cmd_info.get("script")
        if wf_path:
            add_entry(wf_path, "workflow", required=True, priority=4)

    if profile == "task":
        skill_index = context_data.get("skillIndex", [])
        requested_caps = list(dict.fromkeys(capability_ids or []))
        if not requested_caps:
            # Task profile with no selected capability loads 0 skills
            pass
        else:
            # Validate all requested capabilities exist
            valid_caps = {sk.get("capabilityId") for sk in skill_index if sk.get("capabilityId")}
            unknown_caps = set(requested_caps) - valid_caps
            if unknown_caps:
                raise ValueError(f"Unknown capability requested: {unknown_caps}")

            for sk in skill_index:
                cap_id = sk.get("capabilityId")
                if cap_id in requested_caps:
                    if sk.get("path"):
                        add_entry(sk["path"], "skill", required=False, priority=sk.get("priority", 10), capability_owner=cap_id)
                    for ref in sk.get("references", []):
                        add_entry(ref, "reference", required=False, priority=sk.get("priority", 10) + 1, capability_owner=cap_id)

    if profile == "diagnostic":
        for art in manifest.get("artifacts", []):
            add_entry(art["source"], art.get("type", "document"), required=art.get("required", False), priority=10)

    return load_plan


def emit_human(receipt, status_only):
    print("WSR SMART RELOAD RECEIPT")
    print(f"State: {receipt['state']}")
    print(f"Source: {receipt['sourceRoot']}")
    print(f"Version: {receipt['version']} | Build: {receipt['buildId']}")
    print(f"Manifest SHA-256: {receipt['manifestSha256']}")
    print(f"Doctor: {receipt['doctorScore']}/100 | Drift: {receipt['drift']}")
    if receipt.get("deepAudit"):
        print(f"Deep Audit: {receipt['deepAudit']['score']}/100")
    if not status_only:
        print("Load Plan Entries:")
        for entry in receipt.get("loadPlan", []):
            req_str = "REQ" if entry["required"] else "OPT"
            print(f" - [{req_str}] {entry['role'].upper()}: {entry['absolutePath']}")


def main():
    parser = argparse.ArgumentParser(description="Read-only WSR Smart Reload Gate")
    parser.add_argument("--source-root", help="Explicit WSR package root")
    parser.add_argument("--lock-file", help="JSON source lock path")
    parser.add_argument("--adapter", default="codex", help="Adapter name")
    parser.add_argument("--target-root", help="Active configuration root for drift checks")
    parser.add_argument("--profile", choices=["startup", "command", "task", "diagnostic"], default="startup", help="Load profile")
    parser.add_argument("--command-name", help="Slash command name for profile routing")
    parser.add_argument("--capability", action="append", help="Capability ID for task profile")
    parser.add_argument("--deep", action="store_true", help="Approve and run Deep Audit")
    parser.add_argument("--confirm-loaded", action="store_true", help="Confirm every required load-plan entry was read")
    parser.add_argument("--allow-review", action="store_true", help="Allow source verification of an explicitly selected Review build")
    parser.add_argument("--status", action="store_true", help="Emit compact status")
    parser.add_argument("--json", action="store_true", help="Emit JSON receipt")
    args = parser.parse_args()

    try:
        source_root, source_origin, lock = resolve_source(args.source_root, args.lock_file)
        manifest, manifest_sha = validate_identity(source_root, lock, allow_review=args.allow_review)
        target_root = resolve_target(source_root, manifest, args.adapter, args.target_root)
        active_identity = read_active_identity(source_root, target_root, args.adapter)
        active_build = active_identity.get("buildId") if active_identity else None
        if active_identity and version_key(manifest) < version_key(active_identity):
            raise ValueError(f"Source downgrade rejected: {manifest.get('buildId')} < {active_build}")

        doctor_code, doctor, doctor_error = run_doctor(source_root)
        if doctor_code != 0 or not doctor or doctor.get("status") != "PASS":
            raise RuntimeError(doctor_error or "Doctor strict gate failed")
        if doctor.get("score") != 100:
            raise RuntimeError(f"Doctor score must be 100, got {doctor.get('score')}")
        transitions = ["SOURCE_VERIFIED"]

        build_changed = bool(active_build and active_build != manifest.get("buildId"))
        if build_changed and not args.deep:
            receipt = {
                "state": "BLOCKED",
                "reason": "DEEP_AUDIT_REQUIRED",
                "sourceRoot": source_root,
                "sourceOrigin": source_origin,
                "version": manifest.get("version"),
                "buildId": manifest.get("buildId"),
                "activeBuildId": active_build,
                "manifestSha256": manifest_sha,
                "doctorScore": doctor.get("score"),
                "drift": "NOT_CHECKED",
                "loadPlan": build_load_plan(source_root, manifest, args.adapter, args.profile, args.command_name, args.capability),
            }
            if args.json:
                wsr_common.print_json_report(receipt)
            else:
                emit_human(receipt, args.status)
                print("Run again with --deep after explicit approval")
            return wsr_common.EXIT_SAFETY_REJECTION

        deep_result = None
        if args.deep:
            audit_code, audit, audit_error = run_deep_audit(source_root)
            if audit_code != 0 or not audit or audit["summary"].get("status") != "PASS":
                raise RuntimeError(audit_error or "Deep Audit failed")
            deep_result = {
                "score": audit["summary"].get("score"),
                "status": audit["summary"].get("status"),
            }

        drift, changes, drift_error = check_drift(source_root, args.adapter, target_root)
        load_plan = build_load_plan(source_root, manifest, args.adapter, args.profile, args.command_name, args.capability)
        skills = [item["source"] for item in manifest.get("artifacts", []) if item.get("type") == "skill"]
        runtime_verified = False
        runtime_error = None
        if target_root:
            runtime_code, runtime_doctor, runtime_stderr = run_runtime_doctor(source_root, args.adapter, target_root)
            runtime_verified = bool(runtime_code == 0 and runtime_doctor and runtime_doctor.get("status") == "PASS" and runtime_doctor.get("score") == 100)
            runtime_error = None if runtime_verified else (runtime_stderr or "Runtime Doctor gate failed")
        if not target_root:
            state = "TARGET_UNRESOLVED"
        elif drift == "CLEAN" and runtime_verified:
            state = "READY"
        elif drift == "DRIFTED":
            state = "DRIFTED"
        else:
            state = "BLOCKED"
        transitions.append(state)
        if args.confirm_loaded:
            if state != "READY" or any(entry["required"] and not os.path.isfile(entry["absolutePath"]) for entry in load_plan):
                raise RuntimeError("LOADED confirmation requires READY and every required load-plan entry")
            state = "LOADED"
            transitions.append(state)
        receipt = {
            "state": state,
            "transitions": transitions,
            "sourceRoot": source_root,
            "sourceOrigin": source_origin,
            "version": manifest.get("version"),
            "buildId": manifest.get("buildId"),
            "activeBuildId": active_build,
            "manifestSha256": manifest_sha,
            "doctorScore": doctor.get("score"),
            "drift": drift,
            "driftChanges": changes,
            "driftWarning": drift_error,
            "runtimeVerified": runtime_verified,
            "runtimeWarning": runtime_error,
            "deepAudit": deep_result,
            "loadPlan": load_plan,
            "skillIndex": skills,
        }
        if args.json:
            wsr_common.print_json_report(receipt)
        else:
            emit_human(receipt, args.status)
        return wsr_common.EXIT_SUCCESS
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        receipt = {"state": "BLOCKED", "reason": str(error)}
        if args.json:
            wsr_common.print_json_report(receipt)
        else:
            print(f"WSR Smart Reload BLOCKED: {error}", file=sys.stderr)
        return wsr_common.EXIT_FAIL_FINDING


if __name__ == "__main__":
    sys.exit(main())
