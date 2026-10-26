import os
import sys
sys.dont_write_bytecode = True
import json
import hashlib
import tempfile
import datetime
import re

# Standardized exit codes
EXIT_SUCCESS = 0
EXIT_FAIL_FINDING = 1
EXIT_INVALID_ARGS = 2
EXIT_IO_TRANSACTION_ERROR = 3
EXIT_SAFETY_REJECTION = 4

CANONICAL_WSR_REPO = "https://github.com/ThayDuke/WSRCore"

def get_git_remote_info(path):
    """Inspect Git remote and commit info for a package root if available."""
    try:
        import subprocess
        probe = subprocess.run(
            ["git", "-C", str(path), "remote", "get-url", "origin"],
            capture_output=True, text=True, check=False,
        )
        remote_url = probe.stdout.strip() if probe.returncode == 0 else None

        branch_probe = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=False,
        )
        branch = branch_probe.stdout.strip() if branch_probe.returncode == 0 else None

        commit_probe = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False,
        )
        commit = commit_probe.stdout.strip() if commit_probe.returncode == 0 else None

        return {
            "remoteUrl": remote_url,
            "branch": branch,
            "commit": commit,
            "isCanonical": bool(remote_url and CANONICAL_WSR_REPO.lower() in remote_url.lower()),
        }
    except Exception:
        return {"remoteUrl": None, "branch": None, "commit": None, "isCanonical": False}

def get_package_root():
    """Find package root based on this script's location."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(current_dir)

def find_ancestor_lock(start_dir):
    """Walk up directory tree from start_dir to find .wsr-lock.json."""
    curr = os.path.abspath(start_dir)
    while True:
        candidate = os.path.join(curr, ".wsr-lock.json")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    return None

def resolve_source_root(explicit_source_root=None, lock_file=None):
    """Resolve WSR package source root (explicit -> lock -> env -> ancestor lock -> package_root)."""
    if explicit_source_root:
        return _resolve_source_candidate(explicit_source_root, "explicit_source_root")

    explicit_lock = lock_file or os.environ.get("WSR_RELOAD_LOCK")
    if explicit_lock:
        return _resolve_source_candidate(explicit_lock, f"lock:{explicit_lock}")

    env_root = os.environ.get("WSR_CORE_ROOT")
    if env_root and os.path.isdir(env_root):
        return _resolve_source_candidate(env_root, "env:WSR_CORE_ROOT")

    ancestor_lock = find_ancestor_lock(os.getcwd())
    if ancestor_lock:
        return _resolve_source_candidate(ancestor_lock, f"lock:{ancestor_lock}")

    pkg_root = get_package_root()
    if os.path.isfile(os.path.join(pkg_root, "WSR_MANIFEST.json")):
        return _resolve_source_candidate(pkg_root, "package_root")

    raise ValueError(f"WSRCore source root could not be resolved. Expected valid clone of {CANONICAL_WSR_REPO}")

def _resolve_source_candidate(candidate_path, origin):
    """Resolve one authoritative source candidate without fallback."""
    if not candidate_path:
        raise ValueError(f"Empty WSR source candidate at {origin}")
    if os.path.islink(candidate_path):
        raise ValueError(f"Rejected symlink at {origin}: {candidate_path}")

    target_dir = candidate_path
    if str(candidate_path).lower().endswith(".json"):
        if not os.path.isfile(candidate_path):
            raise ValueError(f"Lock file not found at {origin}: {candidate_path}")
        try:
            with open(candidate_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"Invalid JSON at {origin}: {error}") from error
        raw_root = data.get("sourceRoot") or os.path.dirname(candidate_path)
        if not os.path.isabs(raw_root):
            raw_root = os.path.join(os.path.dirname(candidate_path), raw_root)
        target_dir = raw_root

    resolved = os.path.realpath(target_dir)
    if not os.path.isdir(resolved):
        raise ValueError(f"Directory not found at {origin}: {target_dir}")
    if not os.path.isfile(os.path.join(resolved, "WSR_MANIFEST.json")):
        raise ValueError(f"Manifest missing at {origin}: {resolved}")
    return resolved, origin, []

def resolve_target_root(explicit_target=None, env_var=None, default_path=None, workspace_root=None):
    """Resolve target root for adapter (explicit -> env -> default -> workspace)."""
    if explicit_target:
        return os.path.abspath(explicit_target), "explicit"
    if env_var and os.environ.get(env_var):
        return os.path.abspath(os.environ[env_var]), f"env:{env_var}"
    if default_path:
        expanded = os.path.expanduser(default_path)
        return os.path.abspath(expanded), "default"
    if workspace_root:
        return os.path.abspath(workspace_root), "workspace"
    return None, "unresolved"

def resolve_active_root(explicit_source_root=None, lock_file=None):
    """Backward compatible alias for resolve_source_root."""
    return resolve_source_root(explicit_source_root, lock_file)

def load_manifest(package_root):
    """Load and parse manifest file strictly using UTF-8."""
    manifest_path = os.path.join(package_root, "WSR_MANIFEST.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        # strict loading
        return json.load(f)

def validate_relative_path(path_str):
    """Check that path is relative and does not escape via dot-dots."""
    normalized = os.path.normpath(path_str)
    if os.path.isabs(normalized) or normalized.startswith("..") or "/../" in normalized.replace('\\', '/') or normalized.endswith("/..") or normalized.startswith("../"):
        return False
    return True

def safe_resolve_path(package_root, relative_path):
    """Resolve a relative path within the package root and verify containment using realpath/commonpath."""
    if not validate_relative_path(relative_path):
        raise ValueError(f"Path escape attempt or absolute path detected: {relative_path}")
        
    abs_base = os.path.realpath(package_root)
    abs_target = os.path.realpath(os.path.join(abs_base, relative_path))
    
    # Verify path containment using commonpath to prevent sibling prefix issues
    try:
        common = os.path.commonpath([abs_base, abs_target])
    except ValueError as e:
        raise ValueError(f"Path resolution error (drive mismatch or invalid format): {e}")
        
    if common != abs_base:
        raise ValueError(f"Resolved path lies outside base directory: {relative_path}")
        
    # Symlink safety gate: reject symlink operations
    if os.path.islink(abs_target) or os.path.islink(os.path.join(abs_base, relative_path)):
        raise ValueError(f"Symlinks or junctions are rejected for security: {relative_path}")
        
    return abs_target

def calculate_sha256(filepath):
    """Calculate SHA-256 checksum of a file in binary mode."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def calculate_package_content_hash(package_root, manifest):
    """Bind a build identity to manifest plus immutable package payload."""
    excluded_ids = {"wsr-checksums", "release-identity-ledger"}
    rows = [f"manifest:{calculate_sha256(os.path.join(package_root, 'WSR_MANIFEST.json'))}"]
    for artifact in manifest.get("artifacts", []):
        if artifact.get("id") in excluded_ids:
            continue
        source = artifact.get("source", "").replace('\\', '/')
        source_path = os.path.join(package_root, source)
        if not os.path.isfile(source_path):
            raise FileNotFoundError(f"Package content artifact missing: {source}")
        rows.append(f"{source}:{calculate_sha256(source_path)}")
    return hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")).hexdigest()

def atomic_write_text(filepath, content, encoding="utf-8"):
    """Write text content to a file atomically via temporary file replacement."""
    dir_name = os.path.dirname(filepath)
    os.makedirs(dir_name, exist_ok=True)
    
    # Write to a temporary file in the same directory to ensure same filesystem for atomic replace
    fd, temp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as f:
            f.write(content)
        # Atomic rename
        os.replace(temp_path, filepath)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

def print_json_report(report_dict):
    """Output standardized JSON report to stdout."""
    print(json.dumps(report_dict, indent=2, ensure_ascii=False))


def validate_manual_uat_record(manual_uat, primary_adapters=("codex", "antigravity")):
    """Validate either completed native UAT or an explicit, auditable waiver."""
    if not isinstance(manual_uat, dict):
        return False, "Manual UAT record is missing"
    status = manual_uat.get("status")
    expected = "PASS" if status == "PASS" else "NOT_RUN" if status == "WAIVED" else None
    if expected is None:
        return False, "Manual UAT status must be PASS or WAIVED"
    required_keys = {"status", "adapters"} | ({"waiver"} if status == "WAIVED" else set())
    if set(manual_uat) != required_keys:
        return False, "Manual UAT record has invalid fields"
    adapters = manual_uat.get("adapters")
    if not isinstance(adapters, dict) or set(adapters) != set(primary_adapters):
        return False, "Manual UAT adapter set is invalid"
    result_keys = {"status", "router", "overridePrecedence", "restart"}
    for name in primary_adapters:
        result = adapters.get(name)
        if not isinstance(result, dict) or set(result) != result_keys:
            return False, "Manual UAT adapter fields are incomplete: {0}".format(name)
        if any(result.get(key) != expected for key in result_keys):
            return False, "Manual UAT adapter result is invalid: {0}".format(name)
    if status == "WAIVED":
        waiver = manual_uat.get("waiver")
        waiver_keys = {"authorizedBy", "authorizedAt", "reason"}
        if not isinstance(waiver, dict) or set(waiver) != waiver_keys:
            return False, "Manual UAT waiver fields are incomplete"
        if not all(isinstance(waiver.get(key), str) and waiver[key].strip() for key in waiver_keys):
            return False, "Manual UAT waiver values are invalid"
        try:
            datetime.date.fromisoformat(waiver["authorizedAt"])
        except ValueError:
            return False, "Manual UAT waiver date is invalid"
    return True, ""

def format_alert(alert_type, title, message=None):
    """Format GitHub-style alerts."""
    lines = [f"> [!{alert_type.upper()}]", f"> {title}"]
    if message:
        for msg_line in message.split("\n"):
            lines.append(f"> {msg_line}")
    return "\n".join(lines)


CONTEXT_STATE_LABELS = {
    "NORMAL": "An toàn",
    "WARNING": "Gần đầy",
    "HANDOFF_REQUIRED": "Cần handoff",
    "CRITICAL": "Nguy cơ tràn",
    "UNAVAILABLE": "Chưa đo được",
}


def context_state_for_percent(usage_percent, thresholds=None):
    """Map a bounded context percentage to the WSR threshold state."""
    thresholds = thresholds or {}
    if usage_percent >= thresholds.get("criticalPercent", 85):
        return "CRITICAL"
    if usage_percent >= thresholds.get("handoffPercent", 75):
        return "HANDOFF_REQUIRED"
    if usage_percent >= thresholds.get("warningPercent", 60):
        return "WARNING"
    return "NORMAL"


def make_context_report(used_tokens, window_tokens, thresholds=None, source="estimate", projected_tokens=0):
    """Create the stable context telemetry and preflight report."""
    if not isinstance(used_tokens, (int, float)) or not isinstance(window_tokens, (int, float)):
        raise ValueError("Context usage requires numeric token counts")
    if used_tokens < 0 or window_tokens <= 0 or projected_tokens < 0:
        raise ValueError("Context token counts must be non-negative and window must be positive")
    thresholds = thresholds or {}
    percent = min(100, max(0, round((used_tokens / window_tokens) * 100)))
    projected = min(100, max(0, round(((used_tokens + projected_tokens) / window_tokens) * 100)))
    state = context_state_for_percent(percent, thresholds)
    projected_state = context_state_for_percent(projected, thresholds)
    confidence = "high" if source == "native" else "medium"
    remaining = max(0, int(window_tokens - used_tokens))
    return {
        "contextUsagePercent": percent,
        "contextState": state,
        "contextStateLabel": CONTEXT_STATE_LABELS[state],
        "contextMeasurementSource": source,
        "contextConfidence": confidence,
        "contextUsedTokens": int(used_tokens),
        "contextWindowTokens": int(window_tokens),
        "contextRemainingTokens": remaining,
        "contextProjectedPercent": projected,
        "contextProjectedState": projected_state,
        "contextPreflightWarning": projected >= thresholds.get("warningPercent", 60),
        "contextLine": "[Context: ~{0}% | Trạng thái: {1}]".format(percent, CONTEXT_STATE_LABELS[state]),
    }


# Goal orchestration is deliberately dependency-free so every adapter can use
# the same parser and receipt contract without importing runtime-specific code.
GOAL_PREFIX = re.compile(r"^(?P<token>/goal|goal)(?P<separator>\s+|:\s*)(?P<objective>.*)$", re.I)
GOAL_DEFINITION = re.compile(r"^(?:what(?:\s+is|'s)\s+goal|(?:goal\s+)?(?:nghĩa|la|là)\s+gì)\s*\??$", re.I)
GOAL_PATH_PATTERN = re.compile(r"^(?![\\/])(?![A-Za-z]:)(?!.*(?:^|[\\/])\.\.(?:[\\/]|$)).+$")
APPROVAL_ALLOWLIST = frozenset({
    "ok", "làm đi", "duyệt", "ok duyệt", "ok làm đi",
    "được rồi làm đi", "duyệt phương án", "làm đi bạn",
})


def is_explicit_approval(prompt):
    """Return True only for the exact, bounded 1.0.8 approval allowlist."""
    if not isinstance(prompt, str):
        return False
    normalized = " ".join(prompt.strip().casefold().split())
    if not normalized or any(mark in normalized for mark in ("?", "chưa", "không", "có nên")):
        return False
    return normalized in APPROVAL_ALLOWLIST


def _goal_timestamp(value=None):
    if value is not None:
        return value
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_goal_prompt(prompt, authorized_at=None, allowed_paths=None, goal_id=None):
    """Parse a leading /goal, ``Goal `` or ``Goal:`` authorization.

    Returns a normalized goal ledger record, or ``None`` for ordinary,
    empty, definition-question, or non-leading Goal text.
    """
    if not isinstance(prompt, str):
        return None
    match = GOAL_PREFIX.match(prompt.strip())
    if not match:
        return None
    objective = match.group("objective").strip()
    if not objective or objective.endswith("?") or GOAL_DEFINITION.fullmatch(objective):
        return None
    source_token = match.group("token")
    source = "/goal" if source_token.lower() == "/goal" else (
        "Goal:" if match.group("separator").lstrip().startswith(":") else "Goal"
    )
    paths = list(dict.fromkeys(allowed_paths or []))
    if any(not isinstance(path, str) or not GOAL_PATH_PATTERN.fullmatch(path) for path in paths):
        raise ValueError("Goal allowedPaths must be workspace-relative")
    digest = hashlib.sha256((source + "\n" + objective).encode("utf-8")).hexdigest()
    return {
        "schemaVersion": 1,
        "contract": "goal-v1",
        "state": "GOAL_AUTHORIZED",
        "goalId": goal_id or "goal-" + digest[:16],
        "objective": objective,
        "authorizedAt": _goal_timestamp(authorized_at),
        "authorizationSource": source,
        "scope": {"allowedPaths": paths},
        "allowedPaths": paths,
        "approvalMode": "goal",
        "backupResponsibility": "user",
        "autoCheckpointApproval": True,
        "tasks": [],
    }


def goal_path_allowed(goal, path):
    """Return whether a workspace-relative path is inside the Goal scope."""
    if not isinstance(goal, dict) or not isinstance(path, str) or not validate_relative_path(path):
        return False
    allowed = goal.get("allowedPaths")
    if allowed is None:
        allowed = (goal.get("scope") or {}).get("allowedPaths", [])
    if not allowed:
        return False
    candidate = os.path.normcase(os.path.normpath(path)).replace("\\", "/")
    for root in allowed:
        if not isinstance(root, str) or not GOAL_PATH_PATTERN.fullmatch(root):
            continue
        normalized = os.path.normcase(os.path.normpath(root)).replace("\\", "/").rstrip("/")
        if normalized in ("", ".") or candidate == normalized or candidate.startswith(normalized + "/"):
            return True
    return False


def make_goal_task(goal, task_id, owner, allowed_paths, acceptance, dependencies=None, status="PENDING"):
    """Build one bounded Goal task record for native or fallback dispatch."""
    if not isinstance(goal, dict) or not goal.get("goalId"):
        raise ValueError("Goal task requires a goalId")
    paths = list(dict.fromkeys(allowed_paths or []))
    if not paths or any(not isinstance(path, str) or not GOAL_PATH_PATTERN.fullmatch(path) for path in paths):
        raise ValueError("Goal task allowedPaths must be workspace-relative")
    if not isinstance(acceptance, str) or not acceptance.strip():
        raise ValueError("Goal task acceptance must be non-empty")
    return {
        "taskId": str(task_id),
        "goalId": goal["goalId"],
        "owner": str(owner),
        "allowedPaths": paths,
        "dependencies": list(dict.fromkeys(dependencies or [])),
        "acceptance": acceptance.strip(),
        "status": status,
        "receipt": None,
    }


def make_goal_receipt(task, files_changed=None, checks_run=None, findings=None, next_dependency=None, status=None):
    """Build the short, auditable receipt returned by a Goal subagent."""
    if not isinstance(task, dict) or not task.get("taskId") or not task.get("goalId"):
        raise ValueError("Goal receipt requires taskId and goalId")
    return {
        "schemaVersion": 1,
        "contract": "goal-task-v1",
        "taskId": task["taskId"],
        "goalId": task["goalId"],
        "status": status or task.get("status", "DONE"),
        "filesChanged": list(dict.fromkeys(files_changed or [])),
        "checksRun": list(dict.fromkeys(checks_run or [])),
        "findings": list(findings or []),
        "nextDependency": next_dependency,
    }


def create_goal_ledger(goal, tasks=None):
    """Attach bounded tasks to a parsed Goal and validate the checkpoint record."""
    if isinstance(goal, str):
        goal = parse_goal_prompt(goal)
    if not isinstance(goal, dict):
        raise ValueError("Goal ledger requires an authorized Goal")
    ledger = dict(goal)
    ledger["tasks"] = list(tasks if tasks is not None else goal.get("tasks", []))
    valid, detail = validate_goal_ledger(ledger)
    if not valid:
        raise ValueError(detail)
    return ledger


def validate_goal_receipt(receipt, task=None):
    """Validate the minimal subagent receipt and its task/Goal identity."""
    if not isinstance(receipt, dict):
        return False, "Goal receipt must be an object"
    required = {"schemaVersion", "contract", "taskId", "goalId", "status",
                "filesChanged", "checksRun", "findings", "nextDependency"}
    if set(receipt) != required:
        return False, "Goal receipt violates the exact goal-task-v1 contract"
    if receipt.get("schemaVersion") != 1 or receipt.get("contract") != "goal-task-v1":
        return False, "Goal receipt identity mismatch"
    if receipt.get("status") not in {"DONE", "BLOCKED", "RUNNING"}:
        return False, "Goal receipt status is invalid"
    for key in ("filesChanged", "checksRun", "findings"):
        if not isinstance(receipt.get(key), list) or any(not isinstance(item, str) for item in receipt[key]):
            return False, "Goal receipt {0} must be a string list".format(key)
    if receipt.get("nextDependency") is not None and not isinstance(receipt["nextDependency"], str):
        return False, "Goal receipt nextDependency must be string or null"
    if task is not None and (receipt.get("taskId") != task.get("taskId") or receipt.get("goalId") != task.get("goalId")):
        return False, "Goal receipt task identity mismatch"
    return True, ""


def validate_goal_ledger(ledger):
    """Validate Goal scope and authority invariants before dispatch or checkpoint."""
    if not isinstance(ledger, dict):
        return False, "Goal ledger must be an object"
    required = {"schemaVersion", "contract", "goalId", "objective", "authorizedAt",
                "authorizationSource", "scope", "allowedPaths", "approvalMode",
                "backupResponsibility", "autoCheckpointApproval", "tasks"}
    allowed_keys = required | {"state"}
    if set(ledger) - allowed_keys or not required.issubset(ledger):
        return False, "Goal ledger violates the exact v1 contract"
    if ledger.get("schemaVersion") != 1 or ledger.get("contract") != "goal-v1":
        return False, "Goal ledger identity mismatch"
    if not ledger.get("objective", "").strip() or ledger.get("approvalMode") != "goal":
        return False, "Goal objective or approval mode is invalid"
    if ledger.get("backupResponsibility") != "user" or ledger.get("autoCheckpointApproval") is not True:
        return False, "Goal checkpoint/backup semantics are invalid"
    paths = ledger.get("allowedPaths")
    if not isinstance(paths, list) or paths != (ledger.get("scope") or {}).get("allowedPaths"):
        return False, "Goal scope paths are inconsistent"
    if any(not isinstance(path, str) or not GOAL_PATH_PATTERN.fullmatch(path) for path in paths):
        return False, "Goal scope escapes workspace"
    serialized = json.dumps(ledger, ensure_ascii=False, sort_keys=True).lower()
    if any(term in serialized for term in ("approvaltoken", "permission", "secret")):
        return False, "Goal ledger may not persist authority or secrets"
    task_ids = set()
    for task in ledger.get("tasks", []):
        if not isinstance(task, dict) or task.get("taskId") in task_ids:
            return False, "Goal task IDs must be unique"
        task_ids.add(task.get("taskId"))
        if task.get("goalId") != ledger.get("goalId"):
            return False, "Goal task identity mismatch"
        for path in task.get("allowedPaths", []):
            if not goal_path_allowed({"allowedPaths": paths}, path):
                return False, "Goal task scope exceeds Goal scope"
        if task.get("receipt") is not None:
            receipt_ok, receipt_detail = validate_goal_receipt(task["receipt"], task)
            if not receipt_ok:
                return False, receipt_detail
    return True, ""
