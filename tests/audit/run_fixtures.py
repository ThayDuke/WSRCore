"""Small stdlib-only audit fixture runner."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
PACKAGE = HERE.parents[2]
sys.path.insert(0, str(PACKAGE / "scripts"))
import wsr_audit_checks as checks
import wsr_audit as audit_tool
import wsr_debt_scanner as debt_tool


def run_case(case: dict) -> set[str]:
    suffix = {"python": ".py", "json": ".json", "markdown": ".md", "text": ".txt"}[case["kind"]]
    content = case["content"]
    if content.startswith("__REPEAT__:"):
        count = int(content.split(":", 1)[1])
        content = "def f():\n" + "  x = 1\n" * count
    with tempfile.TemporaryDirectory(prefix="wsr-audit-fixture-") as temp:
        relative_name = case.get("name", "fixture" + suffix)
        path = Path(temp) / ("global_workflows" if case["kind"] == "markdown" else "") / relative_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        text, encoding_finding, binary = checks.read_text(path)
        findings = []
        if encoding_finding:
            findings.append(encoding_finding)
        elif not binary and text is not None:
            findings.extend(checks.file_findings(Path(temp), path, text))
        return {item.rule_id for item in findings}


def run_dependency_case(case: dict) -> set[str]:
    with tempfile.TemporaryDirectory(prefix="wsr-audit-dependency-") as temp:
        root = Path(temp)
        for relative, content in case["files"].items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        text_files = [
            (path, path.read_text(encoding="utf-8"))
            for path in root.rglob("*.py")
            if "node_modules" not in path.parts
        ]
        findings = checks.dependency_findings(root, text_files, {"node_modules", ".git"})
        return {item.rule_id for item in findings}


def git_run(cwd: Path, *args: str) -> None:
    result = subprocess.run(("git",) + args, cwd=cwd, capture_output=True)
    if result.returncode:
        raise RuntimeError(os.fsdecode(result.stderr).strip() or "git fixture command failed")


def run_git_discovery_fixture() -> list[dict]:
    failures = []
    with tempfile.TemporaryDirectory(prefix="wsr-audit-git-") as temp:
        repo = Path(temp)
        scope = repo / "scope"
        scope.mkdir()
        (scope / "tracked.py").write_text("value = 1\n", encoding="utf-8")
        (repo / "outside.py").write_text("outside = 1\n", encoding="utf-8")
        git_run(repo, "init", "-q")
        git_run(repo, "add", ".")
        git_run(repo, "-c", "user.name=WSR", "-c", "user.email=wsr@example.invalid", "commit", "-qm", "base")
        canonical = subprocess.run(("git", "rev-parse", "--show-toplevel"), cwd=repo, capture_output=True, check=True)
        repo = Path(os.fsdecode(canonical.stdout).strip())
        scope = repo / "scope"
        (scope / "tracked.py").write_text("value = 2\n", encoding="utf-8")
        (scope / "mới.py").write_text("unicode_name = True\n", encoding="utf-8")
        (repo / "outside.py").write_text("outside = 2\n", encoding="utf-8")
        expected = {"tracked.py", "mới.py"}
        files, metadata = audit_tool.git_changed(scope)
        actual = {path.relative_to(scope).as_posix() for path in files}
        if actual != expected or metadata != {"deleted": [], "renamed": []}:
            failures.append({"id": "git-audit-subroot-unicode", "expected": sorted(expected), "actual": sorted(actual), "metadata": metadata})
        debt_files = {Path(path).relative_to(scope).as_posix() for path in debt_tool.get_git_changed_files(str(scope))}
        if debt_files != expected:
            failures.append({"id": "git-debt-subroot-unicode", "expected": sorted(expected), "actual": sorted(debt_files)})
    return failures


def run_gate_fixtures() -> list[dict]:
    failures = []
    coverage = {"auditedFiles": 1}
    cases = (
        ("HIGH", "blocker", "WARN"),
        ("HIGH", "high", "FAIL"),
        ("MEDIUM", "high", "WARN"),
        ("MEDIUM", "medium", "FAIL"),
        ("LOW", "medium", "WARN"),
        ("LOW", "low", "FAIL"),
        ("INFO", "low", "WARN"),
    )
    for severity, fail_on, expected in cases:
        finding = {"ruleId": "FIXTURE", "severity": severity}
        _, actual, _ = audit_tool.score([finding], "quick", coverage, fail_on)
        if actual != expected:
            failures.append({"id": f"fail-on-{severity.lower()}-{fail_on}", "expected": expected, "actual": actual})
    with tempfile.TemporaryDirectory(prefix="wsr-audit-empty-") as temp:
        root = Path(temp)
        git_run(root, "init", "-q")
        quick = audit_tool.audit(root, "quick", False, None, "high")
        quick_zero = [item for item in quick["findings"] if item["ruleId"] == "INT-004"]
        if quick["summary"]["status"] != "WARN" or [item["severity"] for item in quick_zero] != ["INFO"]:
            failures.append({"id": "zero-coverage-quick", "expected": "WARN/INFO", "actual": quick})
        deep = audit_tool.audit(root, "deep", False, None, "high")
        deep_zero = [item for item in deep["findings"] if item["ruleId"] == "INT-004"]
        if deep["summary"]["status"] != "FAIL" or [item["severity"] for item in deep_zero] != ["BLOCKER"]:
            failures.append({"id": "zero-coverage-deep", "expected": "FAIL/BLOCKER", "actual": deep})
    return failures


def main() -> int:
    fixtures = json.loads((HERE.parent / "fixtures.json").read_text(encoding="utf-8"))
    failures = []
    for case in fixtures["cases"]:
        actual = run_case(case)
        expected = set(case["expect"])
        if actual != expected:
            failures.append({"id": case["id"], "expected": sorted(expected), "actual": sorted(actual)})
    for case in fixtures.get("dependencyCases", []):
        actual = run_dependency_case(case)
        expected = set(case["expect"])
        if actual != expected:
            failures.append({"id": case["id"], "expected": sorted(expected), "actual": sorted(actual)})
    failures.extend(run_git_discovery_fixture())
    failures.extend(run_gate_fixtures())
    if failures:
        print(json.dumps({"status": "FAIL", "failures": failures}, ensure_ascii=False))
        return 1
    report = audit_tool.audit(PACKAGE, "quick", False, None, "high")
    required = {"schemaVersion", "auditVersion", "mode", "root", "categories", "coverage", "gatePassed", "thresholdBreached", "releaseEligible", "summary", "findings", "skipped", "doctor"}
    if set(report) != required:
        print(json.dumps({"status": "FAIL", "reportSchemaExpected": sorted(required), "reportSchemaActual": sorted(report)}, ensure_ascii=False))
        return 1
    total = len(fixtures["cases"]) + len(fixtures.get("dependencyCases", [])) + 11
    print(json.dumps({"status": "PASS", "cases": total, "reportSchema": "PASS"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
