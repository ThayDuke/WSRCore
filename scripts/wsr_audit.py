"""WSR Audit v1.4: deterministic, read-only repository audit."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import wsr_audit_checks as checks

sys.dont_write_bytecode = True

EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache", "dist", "build"}
EXCLUDED_EXTENSIONS = {".zip", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".mp3", ".mp4", ".wav", ".psd", ".woff", ".woff2", ".ttf", ".eot", ".pdf", ".webp", ".cer", ".db", ".sqlite", ".pyc"}


def git_changed(root: Path) -> tuple[list[Path], dict]:
    root = root.resolve()
    probe = subprocess.run(
        ("git", "-C", str(root), "rev-parse", "--show-toplevel"),
        capture_output=True, check=False,
    )
    if probe.returncode:
        raise RuntimeError(os.fsdecode(probe.stderr).strip() or "git repository discovery failed")
    repo_root = Path(os.fsdecode(probe.stdout).strip()).resolve()
    try:
        scope = root.relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise RuntimeError("Audit root is outside the discovered Git repository") from exc
    pathspec = scope or "."
    files: set[Path] = set()
    deleted: set[str] = set()
    renamed: set[str] = set()

    def relative_path(raw: bytes) -> tuple[Path, str] | None:
        candidate = (repo_root / os.fsdecode(raw)).resolve()
        try:
            relative = candidate.relative_to(root).as_posix()
        except ValueError:
            return None
        return candidate, relative

    for args in (("diff", "--name-status", "-z"), ("diff", "--cached", "--name-status", "-z")):
        result = subprocess.run(("git", "-C", str(repo_root)) + args + ("--", pathspec), capture_output=True)
        if result.returncode:
            raise RuntimeError(os.fsdecode(result.stderr).strip() or "git command failed")
        fields = result.stdout.split(b"\0")
        if fields and not fields[-1]:
            fields.pop()
        index = 0
        while index < len(fields):
            status = os.fsdecode(fields[index])
            index += 1
            path_count = 2 if status.startswith(("R", "C")) else 1
            if index + path_count > len(fields):
                raise RuntimeError("Malformed NUL-delimited Git name-status output")
            raw_paths = fields[index:index + path_count]
            index += path_count
            current = relative_path(raw_paths[-1])
            previous = relative_path(raw_paths[0]) if path_count == 2 else current
            if current is None:
                continue
            if status.startswith("D"):
                deleted.add(current[1])
            elif status.startswith(("R", "C")) and previous is not None:
                renamed.add(f"{previous[1]} -> {current[1]}")
                if current[0].is_file():
                    files.add(current[0])
            else:
                if current[0].is_file():
                    files.add(current[0])

    untracked = subprocess.run(
        ("git", "-C", str(repo_root), "ls-files", "--others", "--exclude-standard", "-z", "--", pathspec),
        capture_output=True,
    )
    if untracked.returncode:
        raise RuntimeError(os.fsdecode(untracked.stderr).strip() or "git untracked-file discovery failed")
    for raw_path in untracked.stdout.split(b"\0"):
        if not raw_path:
            continue
        current = relative_path(raw_path)
        if current is not None and current[0].is_file():
            files.add(current[0])
    return sorted(files), {"deleted": sorted(deleted), "renamed": sorted(renamed)}


def tree_files(root: Path) -> tuple[list[Path], dict[str, int]]:
    files: list[Path] = []
    skipped: dict[str, int] = {}
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for name in names:
            path = Path(current) / name
            if path.suffix.lower() in EXCLUDED_EXTENSIONS:
                skipped["extension"] = skipped.get("extension", 0) + 1
                continue
            files.append(path.resolve())
    return sorted(files), skipped


def run_doctor(root: Path) -> tuple[list[dict], dict]:
    if not (root / "WSR_MANIFEST.json").exists():
        return [], {"ran": False, "reason": "WSR_MANIFEST.json not present"}
    try:
        import wsr_doctor
        result, _, _ = wsr_doctor.run_doctor_checks(str(root), strict=True, is_json=True)
    except Exception as exc:
        return [{"ruleId": "INT-003", "category": "integrity", "severity": "BLOCKER", "confidence": "high", "path": "WSR_MANIFEST.json", "line": None, "message": "Doctor execution failed", "evidence": {"error": str(exc)}, "recommendation": "Fix Doctor execution before release", "estimatedLineReduction": None, "estimatedDependencyReduction": None}], {"ran": True, "error": str(exc)}
    findings = []
    for item in result.get("blockers", []):
        findings.append({"ruleId": "DOCTOR-BLOCKER", "category": _doctor_category(item), "severity": "BLOCKER", "confidence": "high", "path": "WSR_MANIFEST.json", "line": None, "message": str(item), "evidence": {"doctor": "blocker"}, "recommendation": "Resolve the Doctor blocker", "estimatedLineReduction": None, "estimatedDependencyReduction": None})
    for item in result.get("warnings", []):
        findings.append({"ruleId": "DOCTOR-WARN", "category": _doctor_category(item), "severity": "MEDIUM", "confidence": "high", "path": "WSR_MANIFEST.json", "line": None, "message": str(item), "evidence": {"doctor": "warning"}, "recommendation": "Resolve or document the Doctor warning", "estimatedLineReduction": None, "estimatedDependencyReduction": None})
    return findings, {"ran": True, "status": result.get("status"), "score": result.get("score"), "checks": len(result.get("checks", []))}


def _doctor_category(text: str) -> str:
    value = str(text).upper()
    if any(x in value for x in ("ADAPTER", "NATIVE", "ROUTER")):
        return "ide"
    if any(x in value for x in ("PROFILE", "BUDGET", "KERNEL", "LOADING", "SIZE")):
        return "resource"
    return "integrity"


def dedup_sort(findings: list[checks.Finding | dict], root: Path) -> list[dict]:
    result: dict[tuple, dict] = {}
    for item in findings:
        data = item.as_dict() if isinstance(item, checks.Finding) else item
        if Path(str(data.get("path", ""))).is_absolute():
            data = dict(data)
            try:
                data["path"] = Path(data["path"]).resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                data["path"] = Path(data["path"]).as_posix()
        evidence = json.dumps(data.get("evidence", {}), sort_keys=True, ensure_ascii=False)
        key = (data["ruleId"], data.get("path", ""), data.get("line"), evidence)
        result[key] = data
    severity_order = {"BLOCKER": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    return sorted(result.values(), key=lambda x: (severity_order.get(x.get("severity", "INFO"), 9), x.get("category", ""), x.get("ruleId", ""), x.get("path", "").lower(), x.get("line") is None, x.get("line") or 0))


def score(findings: list[dict], mode: str, coverage: dict, fail_on: str) -> tuple[int, str, bool]:
    penalties: dict[str, int] = {}
    for item in findings:
        rule = item.get("ruleId", "UNKNOWN")
        penalties[rule] = min(25, penalties.get(rule, 0) + checks.SEVERITY_WEIGHT.get(item.get("severity", "INFO"), 0))
    value = max(0, min(100, 100 - sum(penalties.values())))
    threshold = checks.SEVERITY_WEIGHT[fail_on.upper()]
    threshold_breached = any(
        checks.SEVERITY_WEIGHT.get(x.get("severity", "INFO"), 0) >= threshold
        for x in findings
    )
    if mode == "deep" and coverage.get("auditedFiles", 0) == 0:
        return value, "FAIL", True
    if threshold_breached:
        return value, "FAIL", True
    if findings or (mode == "quick" and coverage.get("auditedFiles", 0) == 0):
        return value, "WARN", False
    return value, "PASS", False


def audit(root: Path, mode: str, changed: bool, categories: set[str] | None, fail_on: str) -> dict:
    metadata = {"deleted": [], "renamed": []}
    if changed or mode == "quick":
        files, metadata = git_changed(root)
        skipped = {}
    else:
        files, skipped = tree_files(root)
    text_files: list[tuple[Path, str]] = []
    findings: list[checks.Finding | dict] = []
    for path in files:
        text, encoding_finding, binary = checks.read_text(path)
        if binary:
            skipped["binary_or_unsupported"] = skipped.get("binary_or_unsupported", 0) + 1
            continue
        if encoding_finding:
            findings.append(encoding_finding)
            continue
        assert text is not None
        text_files.append((path, text))
        findings.extend(checks.file_findings(root, path, text))
    if mode == "deep":
        findings.extend(checks.duplicate_blocks(text_files))
        findings.extend(checks.dependency_findings(root, text_files, EXCLUDED_DIRS))
        doctor_findings, doctor = run_doctor(root)
    else:
        doctor_findings, doctor = [], {"ran": False, "reason": "quick mode"}
    coverage = {"discoveredFiles": len(files), "auditedFiles": len(text_files), "skippedFiles": sum(skipped.values()), "coverageRatio": round(len(text_files) / len(files), 4) if files else 0.0, **metadata}
    if coverage["auditedFiles"] == 0:
        findings.append(checks.finding(
            "INT-004", str(root), None, "Audit covered no supported text files",
            {"mode": mode, "discoveredFiles": coverage["discoveredFiles"], "skippedFiles": coverage["skippedFiles"]},
            "Provide an auditable path or include supported changed files",
            severity="BLOCKER" if mode == "deep" else "INFO",
        ))
    findings = dedup_sort(findings + doctor_findings, root)
    all_findings = findings
    if categories:
        findings = [x for x in findings if x.get("category") in categories]
    value, status, threshold_breached = score(all_findings, mode, coverage, fail_on)
    coverage_valid = coverage["auditedFiles"] > 0
    gate_passed = coverage_valid and not threshold_breached
    release_eligible = gate_passed and not categories
    counts = {level: sum(1 for x in findings if x.get("severity") == level) for level in ("BLOCKER", "HIGH", "MEDIUM", "LOW", "INFO")}
    category_counts = {category: sum(1 for x in findings if x.get("category") == category) for category in checks.CATEGORIES}
    return {
        "schemaVersion": 1,
        "auditVersion": "1.4.1",
        "mode": mode,
        "root": root.as_posix(),
        "categories": sorted(categories or set(checks.CATEGORIES)),
        "coverage": coverage,
        "gatePassed": gate_passed,
        "thresholdBreached": threshold_breached,
        "releaseEligible": release_eligible,
        "summary": {
            "score": value,
            "scoreVersion": "severity-v1",
            "status": status,
            "failOn": fail_on.upper(),
            "counts": counts,
            "categoryCounts": category_counts,
            "estimatedLineReduction": sum(x.get("estimatedLineReduction") or 0 for x in findings),
            "estimatedDependencyReduction": sum(x.get("estimatedDependencyReduction") or 0 for x in findings),
            "unknownEstimateCount": sum(
                1 for x in findings
                if x.get("estimatedLineReduction") is None
                and x.get("estimatedDependencyReduction") is None
            ),
        },
        "findings": findings,
        "skipped": skipped,
        "doctor": doctor,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="WSR Audit v1.4, deterministic and read-only")
    parser.add_argument("--path", default=None)
    parser.add_argument("--mode", choices=("quick", "deep"), default="quick")
    parser.add_argument("--changed", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--category", action="append")
    parser.add_argument("--fail-on", choices=("blocker", "high", "medium", "low"), default="high")
    parser.add_argument("--explain")
    args = parser.parse_args()
    if args.explain:
        rule = checks.RULES.get(args.explain.upper())
        print(json.dumps({"ruleId": args.explain.upper(), "found": bool(rule), "definition": rule}, ensure_ascii=False, indent=2))
        return 0 if rule else 2
    report = audit(Path(args.path or ".").resolve(), args.mode, args.changed, set(args.category) if args.category else None, args.fail_on)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(f"WSR-AUDIT {summary['status']} {summary['score']}/100 | files={report['coverage']['auditedFiles']}/{report['coverage']['discoveredFiles']}")
        for item in report["findings"][:30]:
            print(f"[{item['severity']}] {item['ruleId']} {item['path']}:{item.get('line') or '-'} — {item['message']}")
        hidden = max(0, len(report["findings"]) - 30)
        if hidden:
            print(f"... {hidden} findings hidden; use --json for full output")
    return 0 if report["gatePassed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
