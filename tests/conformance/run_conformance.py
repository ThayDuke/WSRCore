"""Executable, dependency-free conformance runner for WSR-Core."""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True


def run(package_root: Path) -> dict:
    package_root = package_root.resolve()
    manifest = json.loads((package_root / "WSR_MANIFEST.json").read_text(encoding="utf-8"))
    fixtures = json.loads((package_root / "tests" / "conformance" / "fixtures.json").read_text(encoding="utf-8"))
    if fixtures.get("buildId") != manifest.get("buildId"):
        raise ValueError("conformance fixture buildId does not match manifest")
    sys.path.insert(0, str(package_root / "scripts"))
    import sync_config
    import wsr_audit
    import wsr_common
    import wsr_doctor
    import wsr_reload

    doctor, _, _ = wsr_doctor.run_doctor_checks(str(package_root), strict=True, is_json=True, source_mode=True)
    if doctor.get("status") != "PASS":
        raise RuntimeError("Doctor failed: {0}".format(doctor.get("blockers")))
    audit = wsr_audit.audit(package_root, "deep", False, None, "high")
    audit_schema = json.loads((package_root / "schemas" / "wsr-audit-report-v1.schema.json").read_text(encoding="utf-8"))
    valid, detail = wsr_doctor.validate_schema_instance(audit, audit_schema, "audit")
    if not valid or not audit.get("gatePassed"):
        raise RuntimeError("Audit contract failed: {0}".format(detail or audit.get("summary")))
    syntax_count = 0
    for path in sorted((package_root / "scripts").glob("*.py")):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        syntax_count += 1
    goal_cases = _run_goal_contract(package_root, fixtures, manifest, wsr_common, wsr_doctor)
    telemetry_cases = _run_context_telemetry(fixtures, wsr_common)
    grilling_cases = _run_grilling_contract(package_root, fixtures, manifest, wsr_reload)
    override_cases = _run_codex_override_contract(package_root, fixtures, manifest, sync_config)
    approval_cases = 0
    for prompt in fixtures.get("approval", {}).get("approved", []):
        if not wsr_common.is_explicit_approval(prompt):
            raise RuntimeError("Approval allowlist rejected explicit signal: {0}".format(prompt))
        approval_cases += 1
    for prompt in fixtures.get("approval", {}).get("discussion", []):
        if wsr_common.is_explicit_approval(prompt):
            raise RuntimeError("Approval parser accepted ambiguous signal: {0}".format(prompt))
        approval_cases += 1
    checksums = sync_config.compute_checksums(str(package_root), manifest)
    adapters = {}
    for adapter_name in ("codex", "antigravity"):
        adapter = sync_config.load_adapter_config(str(package_root), adapter_name, manifest)
        with tempfile.TemporaryDirectory(prefix="wsr-conformance-") as temp:
            target = Path(temp)
            overrides = {name: str(target / name) for name in adapter.get("roots", {}) if name != "config"}
            plan = sync_config.build_deployment_plan(str(package_root), str(target), manifest, adapter, checksums, overrides)
            destinations = [item["destination_path"] for item in plan]
            if len(destinations) != len(set(os.path.normcase(item) for item in destinations)):
                raise RuntimeError("destination collision for {0}".format(adapter_name))
            roots = sync_config.resolve_roots(adapter, config_override=str(target), root_overrides=overrides)
            sync_config.apply_plan(str(package_root), adapter, manifest, roots, plan)
            runtime, _, _ = wsr_doctor.run_doctor_checks(
                str(package_root), strict=True, is_json=True, adapter_name=adapter_name,
                target_root=str(target), root_overrides=overrides, runtime_mode=True, source_mode=False,
            )
            if runtime.get("status") != "PASS":
                raise RuntimeError("runtime Doctor failed for {0}: {1}".format(adapter_name, runtime.get("blockers")))
            adapters[adapter_name] = {"status": "PASS", "operations": len(plan), "runtimeDoctor": "PASS"}
    cases = (len(fixtures.get("profiles", {})) + len(fixtures.get("adapters", {}))
             + len(fixtures.get("negative", [])) + goal_cases + approval_cases)
    cases += telemetry_cases + grilling_cases + override_cases
    findings = audit.get("findings", [])
    severities = {str(item.get("severity", "")).upper() for item in findings if isinstance(item, dict)}
    counts = {level: sum(1 for item in findings if isinstance(item, dict) and str(item.get("severity", "")).upper() == level)
              for level in ("BLOCKER", "HIGH", "MEDIUM", "LOW")}
    return {"schemaVersion": 2, "buildId": manifest.get("buildId"), "status": "PASS",
            "audit": {"status": audit["summary"]["status"], "score": audit["summary"]["score"],
                      "blockers": counts["BLOCKER"], "high": counts["HIGH"],
                      "medium": counts["MEDIUM"], "low": counts["LOW"]},
            "doctor": {"status": doctor["status"], "score": doctor["score"], "gates": len(doctor.get("checks", []))},
            "syntax": {"status": "PASS", "files": syntax_count},
            "fixtures": {"status": "PASS", "cases": cases}, "adapters": adapters}


def _run_goal_contract(package_root, fixtures, manifest, wsr_common, wsr_doctor):
    """Exercise Goal authorization, scope, fallback, and receipt invariants."""
    goal_fixtures = fixtures.get("goal", {})
    schema_path = package_root / "schemas" / "wsr-goal-v1.schema.json"
    goal_schema = json.loads(schema_path.read_text(encoding="utf-8"))
    valid, detail = wsr_doctor.validate_schema_semantics(goal_schema)
    if not valid:
        raise RuntimeError("Goal schema contract failed: {0}".format(detail))

    cases = 0
    for case in goal_fixtures.get("authorized", []):
        goal = wsr_common.parse_goal_prompt(case["prompt"], authorized_at="2026-08-27T00:00:00Z", allowed_paths=["scripts"])
        if not goal or goal.get("state") != "GOAL_AUTHORIZED":
            raise RuntimeError("Goal authorization fixture did not activate: {0}".format(case["prompt"]))
        if goal.get("authorizationSource") != case["source"] or goal.get("objective") != case["objective"]:
            raise RuntimeError("Goal parser normalization mismatch: {0}".format(case["prompt"]))
        ok, detail = wsr_common.validate_goal_ledger(goal)
        if not ok:
            raise RuntimeError("Goal ledger contract failed: {0}".format(detail))
        ok, detail = wsr_doctor.validate_schema_instance(goal, goal_schema, "goal")
        if not ok:
            raise RuntimeError("Goal schema instance failed: {0}".format(detail))
        cases += 1

    for prompt in goal_fixtures.get("discussion", []):
        if wsr_common.parse_goal_prompt(prompt) is not None:
            raise RuntimeError("Non-leading/definition Goal incorrectly authorized: {0}".format(prompt))
        cases += 1

    scope = goal_fixtures.get("scopeEscape", {})
    scoped_goal = wsr_common.parse_goal_prompt("/goal bounded task", authorized_at="2026-08-27T00:00:00Z", allowed_paths=scope.get("allowedPaths"))
    if not scoped_goal or wsr_common.goal_path_allowed(scoped_goal, scope.get("path", "")):
        raise RuntimeError("Goal path escape was not rejected")
    cases += 1

    task = wsr_common.make_goal_task(scoped_goal, "task-1", "conformance", ["scripts"], "Parser and receipt contract pass")
    receipt = wsr_common.make_goal_receipt(task, checks_run=["schema", "scope"], status="DONE")
    task["status"] = "DONE"
    task["receipt"] = receipt
    scoped_goal["tasks"] = [task]
    ok, detail = wsr_common.validate_goal_receipt(receipt, task)
    if not ok:
        raise RuntimeError("Goal receipt contract failed: {0}".format(detail))
    ok, detail = wsr_common.validate_goal_ledger(scoped_goal)
    if not ok:
        raise RuntimeError("Goal receipt ledger failed: {0}".format(detail))
    ok, detail = wsr_doctor.validate_schema_instance(scoped_goal, goal_schema, "goal")
    if not ok:
        raise RuntimeError("Goal receipt schema failed: {0}".format(detail))
    cases += 2

    for adapter_name in ("codex", "antigravity"):
        adapter_path = package_root / "adapters" / (adapter_name + ".json")
        adapter = json.loads(adapter_path.read_text(encoding="utf-8"))
        capabilities = adapter.get("capabilities", {})
        if not (
            capabilities.get("goalSupport") == "native"
            and capabilities.get("goalEntrypoint")
            and capabilities.get("subagentDispatch") is True
            and capabilities.get("receiptContract") == goal_fixtures.get("receiptContract")
            and isinstance(capabilities.get("maxParallelTasks"), int)
            and capabilities["maxParallelTasks"] >= 1
        ):
            raise RuntimeError("Native Goal capability handshake failed: {0}".format(adapter_name))
        cases += 1

    fallback_name = goal_fixtures.get("fallbackAdapter", "generic")
    fallback = json.loads((package_root / "adapters" / (fallback_name + ".json")).read_text(encoding="utf-8"))
    fallback_caps = fallback.get("capabilities", {})
    if fallback_caps.get("subagentDispatch") is not False or fallback_caps.get("goalEntrypoint") != "fallback-single-agent":
        raise RuntimeError("Goal fallback capability contract failed")
    return cases + 1


def _run_context_telemetry(fixtures, wsr_common):
    """Verify every-response telemetry formatting and threshold mapping."""
    telemetry = fixtures.get("contextTelemetry", {})
    if telemetry.get("everyResponse") is not True:
        raise RuntimeError("Context telemetry must report every response")
    thresholds = {"warningPercent": 60, "handoffPercent": 75, "criticalPercent": 85}
    cases = 1
    for case in telemetry.get("cases", []):
        report = wsr_common.make_context_report(
            case["usedTokens"], case["windowTokens"], thresholds, source="estimate",
        )
        if report["contextUsagePercent"] != case["expectedPercent"]:
            raise RuntimeError("Context percentage mismatch")
        if report["contextState"] != case["expectedState"]:
            raise RuntimeError("Context threshold state mismatch")
        if not report["contextLine"].startswith("[Context: ~"):
            raise RuntimeError("Context line missing")
        cases += 1
    return cases


def _run_grilling_contract(package_root, fixtures, manifest, wsr_reload):
    """Verify /gr and /grd route through one bounded task capability."""
    grilling = fixtures.get("grilling", {})
    capability = grilling.get("capability")
    context = json.loads((package_root / "WSR_CONTEXT.json").read_text(encoding="utf-8"))
    declared = {item.get("source") for item in manifest.get("artifacts", [])}
    cases = 0

    indexed = {item.get("capabilityId"): item for item in context.get("skillIndex", [])}
    skill = indexed.get(capability)
    if not skill or skill.get("references") != grilling.get("references"):
        raise RuntimeError("WSR grilling capability or references are invalid")
    if not set(skill.get("references", [])).issubset(declared):
        raise RuntimeError("WSR grilling references are not declared artifacts")
    cases += 1

    for command, expected in grilling.get("commands", {}).items():
        actual = context.get("commandMap", {}).get(command)
        if not actual or any(actual.get(key) != value for key, value in expected.items()):
            raise RuntimeError("WSR grilling command contract failed: {0}".format(command))
        plan = wsr_reload.build_load_plan(
            str(package_root), manifest, "codex", "task",
            command_name=command, capability_ids=[capability],
        )
        roles = [item.get("role") for item in plan]
        if roles != ["kernel", "command_index", "workflow", "skill"]:
            raise RuntimeError("WSR grilling JIT load plan failed: {0}".format(command))
        if plan[-1].get("capabilityOwner") != capability:
            raise RuntimeError("WSR grilling skill owner is invalid")
        cases += 1
    return cases


def _run_codex_override_contract(package_root, fixtures, manifest, sync_config):
    """Reject shadowing Codex overrides while accepting explicit delegation."""
    fixture = fixtures.get("codexOverride", {})
    adapter = sync_config.load_adapter_config(str(package_root), "codex", manifest)
    checksums = sync_config.compute_checksums(str(package_root), manifest)
    with tempfile.TemporaryDirectory(prefix="wsr-codex-override-") as temp:
        target = Path(temp)
        overrides = {name: str(target / name) for name in adapter.get("roots", {}) if name != "config"}
        override_path = target / "AGENTS.override.md"
        override_path.write_text(fixture.get("stale", "# stale\n"), encoding="utf-8")
        try:
            sync_config.build_deployment_plan(str(package_root), str(target), manifest, adapter, checksums, overrides)
        except ValueError as error:
            if "shadowed by unmanaged override" not in str(error):
                raise RuntimeError("Codex shadow rejection returned the wrong failure") from error
        else:
            raise RuntimeError("Codex shadowing override was not rejected")
        override_path.write_text(fixture.get("conflicting", ""), encoding="utf-8")
        try:
            sync_config.build_deployment_plan(str(package_root), str(target), manifest, adapter, checksums, overrides)
        except ValueError:
            pass
        else:
            raise RuntimeError("Conflicting Codex delegation was not rejected")
        override_path.write_text(fixture.get("delegation", ""), encoding="utf-8")
        plan = sync_config.build_deployment_plan(
            str(package_root), str(target), manifest, adapter, checksums, overrides,
        )
        if not any(item.get("id") == "gemini-policy" for item in plan):
            raise RuntimeError("Codex kernel mapping is missing from the deployment plan")
    return 3


def main() -> int:
    parser = argparse.ArgumentParser(description="WSR executable conformance runner")
    parser.add_argument("--path", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = run(Path(args.path or Path(__file__).resolve().parents[2]))
    except Exception as error:
        report = {"schemaVersion": 1, "status": "FAIL", "message": str(error)}
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) if args.json else "WSR CONFORMANCE {0}".format(report["status"]))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
