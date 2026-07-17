import argparse
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True

import wsr_common


CORE_FILES = (
    "GEMINI.md",
    "AGENTS.md",
    "memory/project_checkpoint.yaml",
)


def load_json(path):
    with open(path, "r", encoding="utf-8", errors="strict") as handle:
        return json.load(handle)


def resolve_source(source_root, lock_file):
    package_root = wsr_common.get_package_root()
    selected_lock = lock_file or os.environ.get("WSR_RELOAD_LOCK")
    if not source_root and not selected_lock:
        local_lock = os.path.join(os.getcwd(), ".wsr-lock.json")
        if os.path.isfile(local_lock):
            selected_lock = local_lock

    lock = None
    if source_root:
        candidate = source_root
        origin = "explicit"
    elif selected_lock:
        lock_path = os.path.realpath(selected_lock)
        if not os.path.isfile(lock_path):
            raise ValueError(f"Source lock not found: {selected_lock}")
        lock = load_json(lock_path)
        required = {"sourceRoot", "version", "buildId", "manifestSha256"}
        missing = sorted(required.difference(lock))
        if missing:
            raise ValueError(f"Source lock missing fields: {missing}")
        raw_root = lock["sourceRoot"]
        if not os.path.isabs(raw_root):
            raw_root = os.path.join(os.path.dirname(lock_path), raw_root)
        candidate = raw_root
        origin = f"lock:{lock_path}"
    else:
        candidate = package_root
        origin = "package"

    if os.path.islink(candidate):
        raise ValueError("Symlink source roots are rejected")
    resolved = os.path.realpath(candidate)
    if not os.path.isdir(resolved):
        raise ValueError(f"Source root not found: {resolved}")
    return resolved, origin, lock


def validate_identity(source_root, lock):
    manifest_path = os.path.join(source_root, "WSR_MANIFEST.json")
    manifest = load_json(manifest_path)
    if manifest.get("status") != "Released":
        raise ValueError("Only Released packages may be loaded")

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
    return run_json([sys.executable, doctor, "--path", source_root, "--strict", "--json"])


def run_deep_audit(source_root):
    audit = os.path.join(source_root, "scripts", "wsr_audit.py")
    return run_json([sys.executable, audit, "--path", source_root, "--mode", "deep", "--json"])


def resolve_target(source_root, manifest, adapter_name, target_root):
    adapter_path = os.path.join(source_root, "adapters", f"{adapter_name}.json")
    adapter = load_json(adapter_path)
    if target_root:
        return os.path.realpath(target_root)
    env_name = adapter.get("targetRootEnvironmentVariable")
    env_value = os.environ.get(env_name, "") if env_name else ""
    return os.path.realpath(env_value) if env_value else None


def read_active_identity(target_root):
    if not target_root:
        return None
    manifest_path = os.path.join(target_root, "WSR_MANIFEST.json")
    if not os.path.isfile(manifest_path):
        return None
    try:
        return load_json(manifest_path)
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


def build_core_paths(source_root, adapter_name):
    paths = [os.path.join(source_root, item) for item in CORE_FILES]
    paths.insert(3, os.path.join(source_root, "adapters", f"{adapter_name}.json"))
    return paths


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
        print("Core files:")
        for path in receipt["coreFiles"]:
            print(f" - {path}")


def main():
    parser = argparse.ArgumentParser(description="Read-only WSR Smart Reload Gate")
    parser.add_argument("--source-root", help="Explicit WSR package root")
    parser.add_argument("--lock-file", help="JSON source lock path")
    parser.add_argument("--adapter", default="codex", help="Adapter name")
    parser.add_argument("--target-root", help="Active configuration root for drift checks")
    parser.add_argument("--deep", action="store_true", help="Approve and run Deep Audit")
    parser.add_argument("--status", action="store_true", help="Emit compact status")
    parser.add_argument("--json", action="store_true", help="Emit JSON receipt")
    args = parser.parse_args()

    try:
        source_root, source_origin, lock = resolve_source(args.source_root, args.lock_file)
        manifest, manifest_sha = validate_identity(source_root, lock)
        target_root = resolve_target(source_root, manifest, args.adapter, args.target_root)
        active_identity = read_active_identity(target_root)
        active_build = active_identity.get("buildId") if active_identity else None
        if active_identity and version_key(manifest) < version_key(active_identity):
            raise ValueError(f"Source downgrade rejected: {manifest.get('buildId')} < {active_build}")

        doctor_code, doctor, doctor_error = run_doctor(source_root)
        if doctor_code != 0 or not doctor or doctor.get("status") != "PASS":
            raise RuntimeError(doctor_error or "Doctor strict gate failed")
        if doctor.get("score") != 100:
            raise RuntimeError(f"Doctor score must be 100, got {doctor.get('score')}")

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
                "coreFiles": build_core_paths(source_root, args.adapter),
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
        skills = [item["source"] for item in manifest.get("artifacts", []) if item.get("type") == "skill"]
        receipt = {
            "state": "VERIFIED",
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
            "deepAudit": deep_result,
            "coreFiles": build_core_paths(source_root, args.adapter),
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

