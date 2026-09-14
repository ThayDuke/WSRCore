import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True

import sync_config
import wsr_common


SESSION_KEYS = {
    "schemaVersion", "buildId", "updatedAt", "activeWorkflow",
    "capabilityIds", "activePlan", "checkpointFiles", "lessonFiles",
}


def load_json(path):
    with open(path, "r", encoding="utf-8", errors="strict") as handle:
        return json.load(handle)


def resolve_source(source_root, lock_file):
    resolved, origin, diagnostics = wsr_common.resolve_active_root(source_root, lock_file)
    lock = None
    if origin.startswith("lock:"):
        lock_path = origin.split(":", 1)[1]
        if os.path.isfile(lock_path):
            lock = load_json(lock_path)
    return resolved, origin, lock


def validate_identity(source_root, lock, allow_review=False):
    manifest_path = os.path.join(source_root, "WSR_MANIFEST.json")
    manifest = load_json(manifest_path)
    status = manifest.get("status")
    if status != "Released" and not (allow_review and status == "Review"):
        raise ValueError("Only Released packages load by default; Review requires --allow-review")
    manifest_sha = wsr_common.calculate_sha256(manifest_path)
    if lock:
        expected = {
            "version": manifest.get("version"),
            "buildId": manifest.get("buildId"),
            "manifestSha256": manifest_sha,
        }
        mismatches = [key for key, value in expected.items() if lock.get(key) != value]
        if mismatches:
            raise ValueError("Source lock identity mismatch: {0}".format(mismatches))
    return manifest, manifest_sha


def run_json(command):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8",
        errors="strict", env=env, check=False,
    )
    payload = None
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass
    return result.returncode, payload, result.stderr.strip()


def run_doctor(source_root):
    path = os.path.join(source_root, "scripts", "wsr_doctor.py")
    return run_json([sys.executable, path, "--path", source_root, "--source-mode", "--strict", "--json"])


def run_runtime_doctor(source_root, adapter_name, roots):
    path = os.path.join(source_root, "scripts", "wsr_doctor.py")
    command = [
        sys.executable, path, "--path", source_root, "--runtime-mode",
        "--adapter", adapter_name, "--target-root", roots["config"], "--strict", "--json",
    ]
    for name, value in roots.items():
        if name != "config":
            command.extend(["--root-override", "{0}={1}".format(name, value)])
    return run_json(command)


def run_deep_audit(source_root):
    path = os.path.join(source_root, "scripts", "wsr_audit.py")
    return run_json([sys.executable, path, "--path", source_root, "--mode", "deep", "--json"])


def resolve_target(source_root, manifest, adapter_name, target_root, root_overrides=None):
    adapter = sync_config.load_adapter_config(source_root, adapter_name, manifest)
    if not adapter.get("enabled"):
        raise ValueError("Adapter '{0}' is disabled".format(adapter_name))
    return adapter, sync_config.resolve_roots(adapter, target_root, root_overrides)


def read_active_identity(adapter, roots):
    state = adapter["state"]
    marker = wsr_common.safe_resolve_path(roots[state["root"]], state["path"])
    if not os.path.isfile(marker):
        return None
    try:
        data = load_json(marker)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    required = {
        "schemaVersion", "adapterIdentity", "packageVersion", "buildId",
        "manifestHash", "inventoryHash", "routerHash", "logicalRoots",
        "installTimestamp", "transactionId",
    }
    if set(data) != required or data.get("schemaVersion") != 1:
        return None
    if data.get("adapterIdentity") != adapter["adapterId"]:
        return None
    data["version"] = data["packageVersion"]
    return data


def version_key(manifest):
    version = tuple(int(part) for part in re.findall(r"\d+", manifest.get("version", "")))
    return version


def check_drift(source_root, adapter_name, roots):
    command = [
        sys.executable, os.path.join(source_root, "scripts", "sync_config.py"),
        "--adapter", adapter_name, "--target-root", roots["config"], "--json",
    ]
    for name, value in roots.items():
        if name != "config":
            command.extend(["--root-override", "{0}={1}".format(name, value)])
    code, payload, error = run_json(command)
    if code != 0 or not payload:
        return "NOT_CHECKED", None, error or "Sync dry-run failed", None
    changes = int(payload.get("changes_count", 0))
    return ("DRIFTED" if changes else "CLEAN"), changes, None, payload


def _text_tokens(text):
    return int(math.ceil(len(text) / 4.0))


def _file_tokens(path):
    with open(path, "r", encoding="utf-8", errors="strict") as stream:
        return _text_tokens(stream.read())


def _load_context(source_root, manifest):
    path = os.path.join(source_root, manifest.get("contextFile", "WSR_CONTEXT.json"))
    context = load_json(path)
    if context.get("schemaVersion") != 2:
        raise ValueError("WSR_CONTEXT.json must use schemaVersion 2")
    return context


def _validate_session(session_file, workspace_root, expected_build_id=None):
    session_file = os.path.realpath(os.path.abspath(session_file))
    workspace_root = os.path.realpath(os.path.abspath(workspace_root))
    if os.path.commonpath([workspace_root, session_file]) != workspace_root:
        raise ValueError("Session descriptor must be contained by workspace root")
    data = load_json(session_file)
    if set(data) - SESSION_KEYS or data.get("schemaVersion") != 1:
        raise ValueError("Session descriptor violates the exact v1 contract")
    for required in ("buildId", "updatedAt"):
        if not isinstance(data.get(required), str) or not data[required]:
            raise ValueError("Session descriptor missing {0}".format(required))
    if expected_build_id and data["buildId"] != expected_build_id:
        raise ValueError("Session build identity mismatch")
    serialized_keys = " ".join(data.keys()).lower()
    if "approval" in serialized_keys or "permission" in serialized_keys or "token" in serialized_keys:
        raise ValueError("Session descriptor may not persist authority")
    return data, session_file, workspace_root


def _validate_capability_selection(requested_caps, by_id):
    unknown = set(requested_caps) - set(by_id)
    if unknown:
        raise ValueError("Unknown capability requested: {0}".format(sorted(unknown)))
    groups = {}
    for capability in requested_caps:
        item = by_id[capability]
        group = item.get("exclusiveGroup")
        if group and group in groups and groups[group] != capability:
            raise ValueError(
                "Mutually exclusive capabilities requested: {0}, {1} ({2})".format(
                    groups[group], capability, group,
                )
            )
        if group:
            groups[group] = capability
        for conflict in item.get("conflictsWith", []):
            if conflict in requested_caps and conflict != capability:
                raise ValueError("Conflicting capabilities requested: {0}, {1}".format(capability, conflict))
        for required in item.get("requires", []):
            if required not in requested_caps:
                raise ValueError("Capability '{0}' requires '{1}'".format(capability, required))


def build_load_plan(
    source_root, manifest, adapter_name, profile="startup", command_name=None,
    capability_ids=None, session_file=None, workspace_root=None,
):
    context = _load_context(source_root, manifest)
    profile_spec = context.get("loadProfiles", {}).get(profile)
    if not profile_spec:
        raise ValueError("Unknown load profile: {0}".format(profile))
    plan = []
    seen = set()

    def add_file(path, role, root, required=True, precedence=10, owner=None):
        absolute = wsr_common.safe_resolve_path(root, path)
        key = os.path.normcase(os.path.realpath(absolute))
        if key in seen:
            return
        if not os.path.isfile(absolute):
            if required:
                raise ValueError("Required load file missing: {0}".format(absolute))
            return
        seen.add(key)
        plan.append({
            "absolutePath": absolute,
            "role": role,
            "originRoot": root,
            "sha256": wsr_common.calculate_sha256(absolute),
            "required": required,
            "loadPhase": profile,
            "precedence": precedence,
            "capabilityOwner": owner,
            "estimatedTokens": _file_tokens(absolute),
        })

    def add_virtual(content, role, precedence):
        plan.append({
            "absolutePath": None,
            "role": role,
            "originRoot": "inline",
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "required": True,
            "loadPhase": profile,
            "precedence": precedence,
            "capabilityOwner": None,
            "estimatedTokens": _text_tokens(content),
            "inlineContent": content,
        })

    add_file(context["policyFile"], "kernel", source_root, precedence=1)
    add_virtual(sync_config.command_index(context), "command_index", 2)

    selected_command = command_name.lstrip("/") if command_name else None
    requested_caps = list(dict.fromkeys(capability_ids or []))
    session = None
    session_root = None

    if profile == "resume":
        if not session_file or not workspace_root:
            raise ValueError("Resume profile requires --session-file and --workspace-root")
        session, session_abs, session_root = _validate_session(
            session_file, workspace_root, manifest.get("buildId"),
        )
        session_rel = os.path.relpath(session_abs, session_root)
        add_file(session_rel, "session_descriptor", session_root, precedence=3)
        selected_command = selected_command or session.get("activeWorkflow")
        requested_caps = list(dict.fromkeys(requested_caps + session.get("capabilityIds", [])))

    if selected_command:
        selected_command = selected_command.lstrip("/")
    if profile in ("command", "task") and not selected_command:
        raise ValueError("{0} profile requires --command-name".format(profile))
    if selected_command:
        info = context.get("commandMap", {}).get(selected_command)
        if not info:
            raise ValueError("Unknown command: {0}".format(selected_command))
        add_file(info["workflow"], "workflow", source_root, precedence=4)

    if profile in ("task", "resume") and requested_caps:
        by_id = {item.get("capabilityId"): item for item in context.get("skillIndex", [])}
        _validate_capability_selection(requested_caps, by_id)
        for capability in requested_caps:
            item = by_id[capability]
            add_file(item["path"], "skill", source_root, required=True, precedence=item.get("priority", 10), owner=capability)

    if profile == "resume" and session:
        references = []
        if session.get("activePlan"):
            references.append(("activePlan", session["activePlan"]))
        references.extend(("checkpoint", item) for item in session.get("checkpointFiles", []))
        references.extend(("lesson", item) for item in session.get("lessonFiles", []))
        for role, relative in references:
            if not wsr_common.validate_relative_path(relative):
                raise ValueError("Resume reference must be workspace-relative: {0}".format(relative))
            add_file(relative, role, session_root, required=True, precedence=20)

    if profile == "diagnostic":
        for artifact in manifest.get("artifacts", []):
            add_file(
                artifact["source"], artifact.get("type", "document"), source_root,
                required=artifact.get("required", False), precedence=30,
            )

    total = sum(item["estimatedTokens"] for item in plan)
    limit = int(profile_spec["maxTokens"])
    if total > limit:
        raise ValueError("Profile token budget exceeded: {0} > {1}".format(total, limit))
    return plan


def check_remote_sync(source_root, fetch_remote=False):
    """Check Git tracking and sync status against canonical GitHub repo."""
    info = wsr_common.get_git_remote_info(source_root)
    if not info.get("remoteUrl"):
        return "STANDALONE", info, None

    if fetch_remote:
        try:
            subprocess.run(
                ["git", "-C", str(source_root), "fetch", "origin", "main"],
                capture_output=True, text=True, check=False, timeout=10,
            )
        except Exception:
            pass

    try:
        probe = subprocess.run(
            ["git", "-C", str(source_root), "rev-parse", "origin/main"],
            capture_output=True, text=True, check=False,
        )
        origin_commit = probe.stdout.strip() if probe.returncode == 0 else None
        if not origin_commit:
            return "TRACKED", info, None

        if info["commit"] == origin_commit:
            return "UP_TO_DATE", info, None
        else:
            rev_list = subprocess.run(
                ["git", "-C", str(source_root), "rev-list", "{0}..{1}".format(info["commit"], origin_commit)],
                capture_output=True, text=True, check=False,
            )
            behind_count = len(rev_list.stdout.strip().splitlines()) if rev_list.returncode == 0 and rev_list.stdout.strip() else 0
            if behind_count > 0:
                return "BEHIND", info, "{0} commit(s) behind remote GitHub origin/main".format(behind_count)
            return "AHEAD", info, None
    except Exception as error:
        return "OFFLINE", info, str(error)


def validate_fetch_authorization(args, build_id):
    if args.fetch_remote and args.approval_token != build_id:
        raise ValueError("Remote fetch requires --approval-token matching the active build ID")


def emit_human(receipt, status_only):
    print("WSR RELOAD: {0}".format(receipt["state"]))
    print("Source: {0}".format(receipt["sourceRoot"]))
    if receipt.get("remoteInfo", {}).get("remoteUrl"):
        print("Remote: {0} ({1})".format(
            receipt["remoteInfo"]["remoteUrl"], receipt.get("remoteSyncStatus", "UNKNOWN")
        ))
    print("Build: {0}".format(receipt["buildId"]))
    print("Doctor: {0}/100 | Drift: {1}".format(receipt["doctorScore"], receipt["drift"]))
    print("Load budget: {0}/{1} tokens".format(receipt["estimatedTokens"], receipt["maxTokens"]))
    print(receipt["contextLine"])
    if receipt.get("contextPreflightWarning"):
        print("Context preflight: WARNING; projected usage {0}% ({1})".format(
            receipt["contextProjectedPercent"], receipt["contextProjectedState"],
        ))
    if not status_only:
        for entry in receipt.get("loadPlan", []):
            location = entry["absolutePath"] or "<inline>"
            print(" - {0}: {1} ({2} tokens)".format(entry["role"], location, entry["estimatedTokens"]))


def parse_args():
    parser = argparse.ArgumentParser(description="Read-only layered WSR reload gate")
    parser.add_argument("--source-root")
    parser.add_argument("--lock-file")
    parser.add_argument("--adapter", default="codex")
    parser.add_argument("--target-root")
    parser.add_argument("--root-override", action="append")
    parser.add_argument("--profile", choices=["startup", "command", "task", "resume", "diagnostic"], default="startup")
    parser.add_argument("--command-name")
    parser.add_argument("--capability", action="append")
    parser.add_argument("--session-file")
    parser.add_argument("--workspace-root")
    parser.add_argument("--context-used-tokens", type=int)
    parser.add_argument("--context-window-tokens", type=int)
    parser.add_argument("--projected-task-tokens", type=int, default=0)
    parser.add_argument("--deep", action="store_true")
    parser.add_argument("--allow-review", action="store_true")
    parser.add_argument("--check-remote", action="store_true")
    parser.add_argument("--fetch-remote", action="store_true")
    parser.add_argument("--approval-token")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def measure_context_usage(context, profile, estimated, used_tokens=None, window_tokens=None, projected_tokens=0):
    budget = context["loadProfiles"][profile]["maxTokens"]
    threshold = context.get("contextThreshold", {
        "warningPercent": 60,
        "handoffPercent": 75,
        "criticalPercent": 85,
    })
    source = "native" if used_tokens is not None and window_tokens is not None else "estimate"
    report = wsr_common.make_context_report(
        estimated if used_tokens is None else used_tokens,
        budget if window_tokens is None else window_tokens,
        threshold,
        source=source,
        projected_tokens=projected_tokens,
    )
    return budget, report


def evaluate_reload_state(source_root, manifest, args, active, roots):
    active_build = active.get("buildId") if active else None
    build_changed = bool(active_build and active_build != manifest.get("buildId"))
    if build_changed and not args.deep:
        return {
            "state": "BLOCKED",
            "reason": "DEEP_AUDIT_REQUIRED",
            "deep_result": None,
            "drift": "NOT_CHECKED",
            "changes": None,
            "warning": None,
            "runtime_verified": False,
        }

    deep_result = None
    if args.deep:
        audit_code, audit, audit_error = run_deep_audit(source_root)
        audit_gate_passed = audit and audit.get("gatePassed")
        if audit_gate_passed is None:
            audit_gate_passed = bool(audit and audit.get("summary", {}).get("status") == "PASS")
        if audit_code != 0 or not audit or not audit_gate_passed:
            raise RuntimeError(audit_error or "Deep Audit failed")
        deep_result = audit["summary"]

    drift, changes, warning, sync_report = check_drift(source_root, args.adapter, roots)
    runtime_code, runtime_doctor, runtime_error = run_runtime_doctor(source_root, args.adapter, roots)
    runtime_verified = bool(
        runtime_code == 0 and runtime_doctor and runtime_doctor.get("status") == "PASS"
        and runtime_doctor.get("score") == 100
    )
    router_changed = bool(sync_report and sync_report.get("restart_required"))
    if build_changed or (active and router_changed):
        state = "RESTART_REQUIRED"
    elif drift == "DRIFTED":
        state = "DRIFTED"
    elif args.profile == "resume":
        state = "RESUME_READY" if runtime_verified else "BLOCKED"
    elif drift == "CLEAN" and runtime_verified:
        state = "READY"
    else:
        state = "VERIFIED"
    if runtime_error and not runtime_verified:
        warning = warning or runtime_error
    return {
        "state": state,
        "reason": None,
        "deep_result": deep_result,
        "drift": drift,
        "changes": changes,
        "warning": warning,
        "runtime_verified": runtime_verified,
    }


def run_reload(args):
    source_root, source_origin, lock = resolve_source(args.source_root, args.lock_file)
    manifest, manifest_sha = validate_identity(source_root, lock, args.allow_review)
    validate_fetch_authorization(args, manifest.get("buildId"))
    root_overrides = sync_config.parse_root_overrides(args.root_override)
    adapter, roots = resolve_target(
        source_root, manifest, args.adapter, args.target_root, root_overrides,
    )
    active = read_active_identity(adapter, roots)
    active_build = active.get("buildId") if active else None
    if active and version_key(manifest) < version_key(active):
        raise ValueError("Source downgrade rejected")

    doctor_code, doctor, doctor_error = run_doctor(source_root)
    if doctor_code != 0 or not doctor or doctor.get("status") != "PASS" or doctor.get("score") != 100:
        raise RuntimeError(doctor_error or "Doctor strict gate failed")

    load_plan = build_load_plan(
        source_root, manifest, args.adapter, args.profile, args.command_name,
        args.capability, args.session_file, args.workspace_root,
    )
    context = _load_context(source_root, manifest)
    estimated = sum(item["estimatedTokens"] for item in load_plan)
    budget, context_report = measure_context_usage(
        context, args.profile, estimated,
        used_tokens=args.context_used_tokens,
        window_tokens=args.context_window_tokens,
        projected_tokens=args.projected_task_tokens,
    )
    outcome = evaluate_reload_state(source_root, manifest, args, active, roots)
    remote_status, remote_info, remote_msg = check_remote_sync(
        source_root, fetch_remote=args.fetch_remote
    )
    if remote_msg and not outcome.get("warning"):
        outcome["warning"] = remote_msg

    return {
        "state": outcome["state"],
        "reason": outcome["reason"],
        "sourceRoot": source_root,
        "sourceOrigin": source_origin,
        "canonicalRepo": wsr_common.CANONICAL_WSR_REPO,
        "remoteInfo": remote_info,
        "remoteSyncStatus": remote_status,
        "version": manifest.get("version"),
        "buildId": manifest.get("buildId"),
        "activeBuildId": active_build,
        "manifestSha256": manifest_sha,
        "doctorScore": doctor.get("score"),
        "drift": outcome["drift"],
        "driftChanges": outcome["changes"],
        "warning": outcome["warning"],
        "runtimeVerified": outcome["runtime_verified"],
        "deepAudit": outcome["deep_result"],
        "profile": args.profile,
        "estimatedTokens": estimated,
        "maxTokens": budget,
        **context_report,
        "loadPlan": load_plan,
        "skillIndex": [
            {
                "capabilityId": item.get("capabilityId"),
                "name": item.get("name"),
                "description": item.get("description"),
            }
            for item in context.get("skillIndex", [])
        ],
    }


def main():
    args = parse_args()

    try:
        receipt = run_reload(args)
        if args.json:
            wsr_common.print_json_report(receipt)
        else:
            emit_human(receipt, args.status)
        return wsr_common.EXIT_SAFETY_REJECTION if receipt["state"] == "BLOCKED" else wsr_common.EXIT_SUCCESS
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        receipt = {"state": "BLOCKED", "reason": str(error)}
        if args.json:
            wsr_common.print_json_report(receipt)
        else:
            print("WSR Reload BLOCKED: {0}".format(error), file=sys.stderr)
        return wsr_common.EXIT_FAIL_FINDING


if __name__ == "__main__":
    sys.exit(main())
