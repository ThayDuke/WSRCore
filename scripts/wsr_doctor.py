import argparse
import ast
import datetime
import fnmatch
import json
import os
import re
import sys

sys.dont_write_bytecode = True

import wsr_common


ADAPTER_KEYS = {
    "schemaVersion", "adapterId", "runtimeFamily", "enabled", "supportLevel",
    "roots", "discoveryPrecedence", "artifactMappings", "router", "state",
    "capabilities", "legacyRoots", "unsupportedFeatures",
}
RULE_IDS = {"AUTH-01", "AUTH-02", "SAFE-01", "SCOPE-01", "LOAD-01", "STATE-01", "VERIFY-01"}
PRIMARY_ADAPTERS = {"codex", "antigravity"}


def load_json(path):
    with open(path, "r", encoding="utf-8", errors="strict") as stream:
        return json.load(stream)


SCHEMA_KEYWORDS = {
    "$schema", "title", "type", "const", "enum", "format", "pattern",
    "properties", "required", "additionalProperties", "items",
    "minLength", "minProperties", "minimum", "maximum", "uniqueItems",
}
SCHEMA_TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}


def validate_schema_semantics(schema):
    """Validate the strict Draft-07 subset implemented by Doctor."""
    def visit(node, path="schema"):
        if not isinstance(node, dict):
            return False, "{0} must be an object".format(path)
        unknown = set(node) - SCHEMA_KEYWORDS
        if unknown:
            return False, "unsupported keyword(s) at {0}: {1}".format(path, sorted(unknown))
        declared = node.get("type")
        declared_types = declared if isinstance(declared, list) else [declared]
        if declared is not None and (
            not declared_types or any(item not in SCHEMA_TYPES for item in declared_types)
        ):
            return False, "invalid type at {0}".format(path)
        properties = node.get("properties", {})
        if not isinstance(properties, dict):
            return False, "properties at {0} must be an object".format(path)
        for name, child in properties.items():
            ok, detail = visit(child, "{0}.properties.{1}".format(path, name))
            if not ok:
                return ok, detail
        additional = node.get("additionalProperties", True)
        if not isinstance(additional, (bool, dict)):
            return False, "additionalProperties at {0} must be boolean or schema".format(path)
        if isinstance(additional, dict):
            ok, detail = visit(additional, "{0}.additionalProperties".format(path))
            if not ok:
                return ok, detail
        if "items" in node:
            ok, detail = visit(node["items"], "{0}.items".format(path))
            if not ok:
                return ok, detail
        required = node.get("required", [])
        if not isinstance(required, list) or len(required) != len(set(required)):
            return False, "required at {0} must contain unique names".format(path)
        if properties and any(name not in properties for name in required):
            return False, "required at {0} references an undeclared property".format(path)
        return True, ""

    return visit(schema)


def validate_schema_instance(value, schema, path="instance"):
    """Validate one value against the supported Draft-07 subset."""
    if "const" in schema and value != schema["const"]:
        return False, "{0} must equal {1!r}".format(path, schema["const"])
    if "enum" in schema and value not in schema["enum"]:
        return False, "{0} is outside the allowed enum".format(path)

    declared = schema.get("type")
    declared_types = declared if isinstance(declared, list) else ([declared] if declared else [])

    def type_matches(name):
        if name == "null":
            return value is None
        if name == "boolean":
            return isinstance(value, bool)
        if name == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if name == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if name == "string":
            return isinstance(value, str)
        if name == "array":
            return isinstance(value, list)
        if name == "object":
            return isinstance(value, dict)
        return False

    if declared_types and not any(type_matches(name) for name in declared_types):
        return False, "{0} has invalid type".format(path)

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            return False, "{0} is shorter than minLength".format(path)
        if schema.get("pattern") and re.search(schema["pattern"], value) is None:
            return False, "{0} does not match pattern".format(path)
        if schema.get("format") == "date-time":
            try:
                datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return False, "{0} is not a date-time".format(path)

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            return False, "{0} is below minimum".format(path)
        if "maximum" in schema and value > schema["maximum"]:
            return False, "{0} is above maximum".format(path)

    if isinstance(value, list):
        if schema.get("uniqueItems"):
            canonical = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
            if len(canonical) != len(set(canonical)):
                return False, "{0} contains duplicate items".format(path)
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                ok, detail = validate_schema_instance(item, item_schema, "{0}[{1}]".format(path, index))
                if not ok:
                    return ok, detail

    if isinstance(value, dict):
        if len(value) < schema.get("minProperties", 0):
            return False, "{0} has too few properties".format(path)
        required = schema.get("required", [])
        missing = [name for name in required if name not in value]
        if missing:
            return False, "{0} is missing {1}".format(path, missing)
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for name, item in value.items():
            child_schema = properties.get(name)
            if child_schema is None:
                if additional is False:
                    return False, "{0}.{1} is unexpected".format(path, name)
                child_schema = additional if isinstance(additional, dict) else None
            if child_schema:
                ok, detail = validate_schema_instance(item, child_schema, "{0}.{1}".format(path, name))
                if not ok:
                    return ok, detail
    return True, ""


def check_adapter_file(adapter_path):
    if not os.path.isfile(adapter_path):
        return False, "Adapter file not found"
    try:
        data = load_json(adapter_path)
    except (OSError, ValueError) as error:
        return False, "Adapter parse failed: {0}".format(error)
    schema_path = os.path.join(os.path.dirname(os.path.dirname(adapter_path)), "schemas", "wsr-adapter-v3.schema.json")
    try:
        schema = load_json(schema_path)
        valid, detail = validate_schema_instance(data, schema, "adapter")
    except (OSError, ValueError) as error:
        return False, "Adapter schema validation failed: {0}".format(error)
    if not valid:
        return False, detail
    if data.get("schemaVersion") != 3 or set(data) != ADAPTER_KEYS:
        return False, "Adapter must use the exact v3 top-level contract"
    if not isinstance(data.get("roots"), dict) or not data["roots"]:
        return False, "Adapter roots are missing"
    for name, spec in data["roots"].items():
        if set(spec) != {"default", "environmentVariable", "requiresExplicit"}:
            return False, "Root '{0}' violates the exact resolver contract".format(name)
        if spec["default"] is not None and not isinstance(spec["default"], str):
            return False, "Root default must be string or null"
        if spec["environmentVariable"] is not None and not isinstance(spec["environmentVariable"], str):
            return False, "Root environmentVariable must be string or null"
        if not isinstance(spec["requiresExplicit"], bool):
            return False, "Root requiresExplicit must be boolean"
    if "config" not in data["roots"]:
        return False, "Adapter must declare config root"
    for mapping in data.get("artifactMappings", []):
        allowed = {"artifactId", "artifactType", "root", "relativePath", "stripTopLevel", "native"}
        if set(mapping) - allowed or not mapping.get("artifactType"):
            return False, "Artifact mapping contains invalid fields"
        if mapping.get("root") not in data["roots"]:
            return False, "Artifact mapping references unknown root"
        if not wsr_common.validate_relative_path(mapping.get("relativePath", "")):
            return False, "Artifact mapping escapes root"
    for contract_name in ("router", "state"):
        contract = data.get(contract_name)
        if not isinstance(contract, dict) or contract.get("root") not in data["roots"]:
            return False, "{0} contract references unknown root".format(contract_name)
        if not wsr_common.validate_relative_path(contract.get("path", "")):
            return False, "{0} path escapes root".format(contract_name)
    return True, ""


def _excluded(relative, patterns):
    normalized = relative.replace("\\", "/")
    for pattern in patterns:
        if pattern.endswith("/") and any(
            fnmatch.fnmatch(part, pattern.rstrip("/")) for part in normalized.split("/")
        ):
            return True
        if fnmatch.fnmatch(os.path.basename(normalized), pattern):
            return True
    return False


def _all_package_files(package_root, exclusions):
    files = []
    for root, dirs, names in os.walk(package_root):
        dirs[:] = [name for name in dirs if not _excluded(os.path.relpath(os.path.join(root, name), package_root), exclusions)]
        for name in names:
            relative = os.path.relpath(os.path.join(root, name), package_root).replace("\\", "/")
            if not _excluded(relative, exclusions):
                files.append(relative)
    return sorted(files)


def _read_text(path):
    with open(path, "r", encoding="utf-8", errors="strict") as stream:
        return stream.read()


def _session_schema_ok(schema):
    properties = set(schema.get("properties", {}))
    forbidden = {name for name in properties if re.search(r"approval|permission|token|secret", name, re.I)}
    return (
        schema.get("additionalProperties") is False
        and schema.get("properties", {}).get("schemaVersion", {}).get("const") == 1
        and not forbidden
    )


def _profile_contract_ok(context):
    expected_layers = {
        "startup": ["kernel", "command_index"],
        "command": ["kernel", "command_index", "active_workflow"],
        "task": ["kernel", "command_index", "active_workflow", "matched_skills"],
        "resume": ["kernel", "command_index", "session_descriptor", "session_references"],
        "diagnostic": ["all_declared_artifacts"],
    }
    profiles = context.get("loadProfiles", {})
    if set(profiles) != set(expected_layers):
        return False
    for name, layers in expected_layers.items():
        profile = profiles[name]
        if profile.get("layers") != layers or not isinstance(profile.get("maxTokens"), int):
            return False
    return (
        profiles["startup"]["maxTokens"] <= 1000
        and profiles["resume"]["maxTokens"] <= 4000
        and context.get("tokenBudget") == {
            "estimator": "ceil(utf8_chars/4)", "enforcedPerProfile": True,
        }
    )


def _mapping_contract_ok(adapters, artifacts):
    artifact_by_id = {item.get("id"): item for item in artifacts}
    deploy_types = {"rule", "workflow", "skill", "script"}
    for adapter_name in PRIMARY_ADAPTERS:
        adapter = adapters.get(adapter_name)
        if not adapter:
            return False, "primary adapter missing: {0}".format(adapter_name)
        selectors = set()
        mappings = adapter.get("artifactMappings", [])
        for mapping in mappings:
            selector = (
                "id", mapping.get("artifactId"),
            ) if mapping.get("artifactId") else ("type", mapping.get("artifactType"))
            if selector in selectors:
                return False, "duplicate mapping selector for {0}: {1}".format(adapter_name, selector)
            selectors.add(selector)
            if mapping.get("artifactId"):
                artifact = artifact_by_id.get(mapping["artifactId"])
                if not artifact or artifact.get("type") != mapping.get("artifactType"):
                    return False, "mapping identity/type mismatch for {0}".format(mapping["artifactId"])
        for artifact in artifacts:
            if not artifact.get("deploy") or artifact.get("type") not in deploy_types:
                continue
            if adapter_name not in artifact.get("targets", []):
                continue
            matched = any(
                mapping.get("artifactId") == artifact.get("id")
                or (
                    not mapping.get("artifactId")
                    and mapping.get("artifactType") == artifact.get("type")
                )
                for mapping in mappings
            )
            if not matched:
                return False, "unmapped deploy artifact for {0}: {1}".format(adapter_name, artifact.get("id"))
    return True, ""


def _goal_contract_ok(package_root, context, adapters):
    """Check Goal parser/schema/capability invariants without persisting authority."""
    try:
        goal_schema_path = os.path.join(package_root, "schemas", "wsr-goal-v1.schema.json")
        goal_workflow = os.path.join(package_root, "global_workflows", "goal.md")
        if not os.path.isfile(goal_schema_path) or not os.path.isfile(goal_workflow):
            return False, "Goal schema/workflow is missing"
        goal_schema = load_json(goal_schema_path)
        schema_ok, schema_detail = validate_schema_semantics(goal_schema)
        if not schema_ok:
            return False, schema_detail
        goal_contract = context.get("goalContract", {}) if isinstance(context, dict) else {}
        if goal_contract.get("schema") != "schemas/wsr-goal-v1.schema.json":
            return False, "Goal schema binding mismatch"
        if goal_contract.get("parser") != "scripts/wsr_common.py:parse_goal_prompt":
            return False, "Goal parser binding mismatch"
        command = context.get("commandMap", {}).get("goal", {})
        if command != {
            "workflow": "global_workflows/goal.md",
            "description": "Authorize one bounded Goal execution and its task receipts",
            "readOnly": False,
            "approvalRequired": True,
            "requiredProfile": "task",
        }:
            return False, "Goal command registry entry is not exact"
        threshold = context.get("contextThreshold", {})
        if threshold != {
            "warningPercent": 60,
            "handoffPercent": 75,
            "criticalPercent": 85,
            "action": "checkpoint_then_stop",
        }:
            return False, "Context threshold contract is invalid"
        for name in ("codex", "antigravity"):
            capabilities = adapters.get(name, {}).get("capabilities", {})
            expected = {
                "goalSupport": "native",
                "goalEntrypoint": "native-goal",
                "subagentDispatch": True,
                "receiptContract": "goal-task-v1",
            }
            if any(capabilities.get(key) != value for key, value in expected.items()):
                return False, "{0} Goal capability handshake is incomplete".format(name)
            if not isinstance(capabilities.get("maxParallelTasks"), int) or capabilities["maxParallelTasks"] < 1:
                return False, "{0} maxParallelTasks is invalid".format(name)
        return True, ""
    except (OSError, ValueError, TypeError) as error:
        return False, str(error)


def _evidence_contract_ok(package_root, manifest):
    index_relative = "evidence/cross-ide-conformance/index.json"
    try:
        index = load_json(wsr_common.safe_resolve_path(package_root, index_relative))
        if set(index) != {"schemaVersion", "activeRun", "primaryAdapters"}:
            return False, "evidence index must use the exact v2 contract"
        if index.get("schemaVersion") != 2 or set(index.get("primaryAdapters", [])) != PRIMARY_ADAPTERS:
            return False, "evidence primary adapter contract mismatch"
        active_relative = index.get("activeRun", "")
        declared = {item.get("source") for item in manifest.get("artifacts", []) if item.get("type") == "evidence"}
        if active_relative not in declared:
            return False, "active evidence is not declared in manifest"
        active = load_json(wsr_common.safe_resolve_path(package_root, active_relative))
        required = {"schemaVersion", "buildId", "status", "audit", "doctor", "fixtures", "conformanceCases", "syntax", "adapters"}
        allowed = required | {"manualUat"}
        if not required.issubset(active) or not set(active).issubset(allowed) or active.get("schemaVersion") != 2:
            return False, "active evidence must use the exact v2 result contract"
        if active.get("buildId") != manifest.get("buildId") or active.get("status") != "PASS":
            return False, "active evidence identity/status mismatch"
        manual_uat = active.get("manualUat")
        if manifest.get("status") == "Released" and not isinstance(manual_uat, dict):
            return False, "released evidence requires native Manual UAT"
        if manual_uat is not None:
            manual_ok, manual_detail = wsr_common.validate_manual_uat_record(manual_uat, PRIMARY_ADAPTERS)
            if not manual_ok:
                return False, manual_detail
        if not isinstance(active.get("conformanceCases"), int) or active.get("conformanceCases") < 1:
            return False, "evidence conformance case count is incomplete"
        doctor = active.get("doctor", {})
        if doctor.get("status") != "PASS" or doctor.get("score") != 100 or not isinstance(doctor.get("gates"), int):
            return False, "evidence Doctor result is incomplete"
        adapters = active.get("adapters", {})
        for name in PRIMARY_ADAPTERS:
            result = adapters.get(name, {})
            if result.get("status") != "PASS" or result.get("runtimeDoctor") != "PASS":
                return False, "primary adapter evidence failed: {0}".format(name)
        for section in ("fixtures", "syntax"):
            if active.get(section, {}).get("status") != "PASS":
                return False, "evidence section failed: {0}".format(section)
        audit = active.get("audit", {})
        if audit.get("blockers") or audit.get("high") or audit.get("status") not in {"PASS", "WARN"}:
            return False, "audit evidence contains release-blocking findings"
        return True, ""
    except (OSError, ValueError, TypeError) as error:
        return False, str(error)


def _validate_runtime(package_root, manifest, adapter_name, target_root, root_overrides):
    import sync_config

    adapter = sync_config.load_adapter_config(package_root, adapter_name, manifest)
    roots = sync_config.resolve_roots(adapter, target_root, root_overrides)
    state = adapter["state"]
    marker_path = wsr_common.safe_resolve_path(roots[state["root"]], state["path"])
    if not os.path.isfile(marker_path):
        raise ValueError("Active marker missing: {0}".format(marker_path))
    marker = load_json(marker_path)
    marker_schema = load_json(os.path.join(package_root, "schemas", "wsr-active-v1.schema.json"))
    marker_ok, marker_detail = validate_schema_instance(marker, marker_schema, "activeMarker")
    if not marker_ok:
        raise ValueError(marker_detail)
    required = {
        "schemaVersion", "adapterIdentity", "packageVersion", "buildId",
        "manifestHash", "inventoryHash", "routerHash", "logicalRoots",
        "installTimestamp", "transactionId",
    }
    if set(marker) != required or marker.get("schemaVersion") != 1:
        raise ValueError("Active marker violates v1 contract")
    if marker.get("adapterIdentity") != adapter_name:
        raise ValueError("Active marker adapter mismatch")
    if marker.get("buildId") != manifest.get("buildId") or marker.get("packageVersion") != manifest.get("version"):
        raise ValueError("Active marker identity mismatch")
    manifest_hash = wsr_common.calculate_sha256(os.path.join(package_root, "WSR_MANIFEST.json"))
    if marker.get("manifestHash") != manifest_hash:
        raise ValueError("Active marker manifest hash mismatch")
    checksums = sync_config.compute_checksums(package_root, manifest)
    plan = sync_config.build_deployment_plan(
        package_root, roots["config"], manifest, adapter, checksums,
        root_overrides, workspace_root=os.getcwd(),
    )
    if any(operation["action"] != "unchanged" for operation in plan):
        raise ValueError("Runtime files drift from source")
    if marker.get("inventoryHash") != sync_config.calculate_inventory_hash(plan):
        raise ValueError("Active marker inventory hash mismatch")
    router = next(operation for operation in plan if operation["id"] == "active-router")
    if marker.get("routerHash") != router["src_checksum"]:
        raise ValueError("Active marker router hash mismatch")


def _check_manifest_contracts(package_root, manifest, gate):
    version = manifest.get("version", "")
    build_id = manifest.get("buildId", "")
    status_suffixes = {
        "Review": "REVIEW",
        "ReleaseCandidate": "RELEASE-CANDIDATE",
        "Released": "RELEASE",
    }
    identity_ok = bool(
        manifest.get("schemaVersion") == 2
        and re.fullmatch(r"\d+\.\d+(?:\.\d+)?", version)
        and build_id == "WSR-CORE-{0}-{1}".format(
            version, status_suffixes.get(manifest.get("status"), "INVALID")
        )
    )
    gate("D02_SEMANTIC_IDENTITY", identity_ok, "version/build/status must agree")

    required_top = {
        "schemaVersion", "packageName", "version", "buildId", "status", "createdAt",
        "canonicalLayout", "compatibilityLayouts", "minimumPython", "policySource",
        "checksumsFile", "contextFile", "cleanWhitelist", "packageExclusions",
        "adapters", "artifacts",
    }
    manifest_contract_ok = set(manifest) == required_top and "commands" not in manifest
    manifest_contract_detail = "manifest must be exact and command registry must not be duplicated"
    try:
        manifest_schema = load_json(os.path.join(package_root, "schemas", "wsr-manifest-v2.schema.json"))
        schema_ok, schema_detail = validate_schema_semantics(manifest_schema)
        instance_ok, instance_detail = validate_schema_instance(manifest, manifest_schema, "manifest")
        manifest_contract_ok = manifest_contract_ok and schema_ok and instance_ok
        manifest_contract_detail = schema_detail or instance_detail or manifest_contract_detail
    except Exception as error:
        manifest_contract_ok = False
        manifest_contract_detail = str(error)
    gate("D03_MANIFEST_CONTRACT", manifest_contract_ok, manifest_contract_detail)

    artifacts = manifest.get("artifacts", [])
    ids = [item.get("id") for item in artifacts]
    sources = [item.get("source") for item in artifacts]
    inventory_ok = len(ids) == len(set(ids)) and len(sources) == len(set(sources))
    for item in artifacts:
        source = item.get("source", "")
        if not wsr_common.validate_relative_path(source):
            inventory_ok = False
        if item.get("required"):
            try:
                source_path = wsr_common.safe_resolve_path(package_root, source)
            except ValueError:
                inventory_ok = False
            else:
                if not os.path.isfile(source_path):
                    inventory_ok = False
    gate("D04_ARTIFACT_INVENTORY", inventory_ok, "artifact IDs/sources must be unique, contained and present")

    checksum_ok = True
    checksum_detail = ""
    try:
        checksum_path = wsr_common.safe_resolve_path(package_root, manifest["checksumsFile"])
        checksum_data = load_json(checksum_path)
        expected_checksums = {
            item["source"] for item in artifacts
            if item["source"] != manifest["checksumsFile"]
            and os.path.isfile(wsr_common.safe_resolve_path(package_root, item["source"]))
        }
        if set(checksum_data) != expected_checksums:
            missing = sorted(expected_checksums - set(checksum_data))
            extra = sorted(set(checksum_data) - expected_checksums)
            raise ValueError("checksum inventory mismatch; missing={0}; extra={1}".format(missing, extra))
        if manifest["checksumsFile"] in checksum_data:
            raise ValueError("checksum inventory may not hash itself")
        for source in expected_checksums:
            path = wsr_common.safe_resolve_path(package_root, source)
            expected_hash = checksum_data.get(source)
            if not re.fullmatch(r"[0-9a-f]{64}", expected_hash or ""):
                raise ValueError("invalid checksum value: {0}".format(source))
            if os.path.isfile(path) and expected_hash != wsr_common.calculate_sha256(path):
                raise ValueError("checksum mismatch: {0}".format(source))
    except Exception as error:
        checksum_ok = False
        checksum_detail = str(error)
    gate("D05_CHECKSUM_BINDING", checksum_ok, checksum_detail)

    try:
        context_path = os.path.join(package_root, manifest["contextFile"])
        context = load_json(context_path)
        context_schema = load_json(os.path.join(package_root, "schemas", "wsr-context-v2.schema.json"))
        schema_ok, schema_detail = validate_schema_semantics(context_schema)
        instance_ok, instance_detail = validate_schema_instance(context, context_schema, "context")
        context_ok = (
            schema_ok and instance_ok
            and context.get("schemaVersion") == 2
            and context.get("version") == version
            and context.get("buildId") == build_id
            and context.get("manifestSha256") == wsr_common.calculate_sha256(os.path.join(package_root, "WSR_MANIFEST.json"))
            and context.get("policyFile") == manifest.get("policySource")
        )
        gate("D06_CONTEXT_IDENTITY", context_ok, schema_detail or instance_detail or "context identity/hash/policy mismatch")
    except Exception as error:
        gate("D06_CONTEXT_IDENTITY", False, str(error))
    return version, build_id, artifacts, sources, context


def _check_context_contracts(package_root, manifest, context, gate, adapter_name):
    command_ok = bool(context and isinstance(context.get("commandMap"), dict) and context["commandMap"])
    if command_ok:
        for item in context["commandMap"].values():
            workflow = item.get("workflow")
            if not workflow or not os.path.isfile(os.path.join(package_root, workflow)):
                command_ok = False
            if item.get("aliasOf") and item["aliasOf"] not in context["commandMap"]:
                command_ok = False
    gate("D07_COMMAND_REGISTRY", command_ok, "context must be the only valid command registry")

    skill_ok = bool(context)
    if skill_ok:
        seen = set()
        for item in context.get("skillIndex", []):
            capability = item.get("capabilityId")
            path = os.path.join(package_root, item.get("path", ""))
            if not capability or capability in seen or not os.path.isfile(path):
                skill_ok = False
                break
            seen.add(capability)
            if item.get("contentHash") != wsr_common.calculate_sha256(path):
                skill_ok = False
                break
    gate("D08_SKILL_INDEX", skill_ok, "capability IDs and hashes must be unique and valid")

    profile_ok = bool(context) and _profile_contract_ok(context)
    gate("D09_PROFILE_CONTRACT", profile_ok, "layered profiles or budgets are invalid")

    startup_ok = False
    startup_detail = ""
    try:
        import wsr_reload

        plan = wsr_reload.build_load_plan(package_root, manifest, adapter_name or "codex", "startup")
        roles = [entry["role"] for entry in plan]
        tokens = sum(entry["estimatedTokens"] for entry in plan)
        startup_ok = roles == ["kernel", "command_index"] and tokens <= context["loadProfiles"]["startup"]["maxTokens"]
        if not startup_ok:
            startup_detail = "startup roles/tokens invalid: {0}, {1}".format(roles, tokens)
    except Exception as error:
        startup_detail = str(error)
    gate("D10_STARTUP_BUDGET", startup_ok, startup_detail)

    kernel = ""
    try:
        kernel = _read_text(os.path.join(package_root, manifest["policySource"]))
    except Exception:
        pass
    found_ids = re.findall(r"`([A-Z]+-\d{2})`", kernel)
    gate(
        "D11_IRON_RULE_IDS",
        set(found_ids) == RULE_IDS and len(found_ids) == len(RULE_IDS),
        "iron-rule IDs must be exact and unique",
    )
    gate("D12_KERNEL_SIZE", len(kernel.encode("utf-8")) <= 4096, "kernel exceeds 4 KiB")


def _check_adapter_contracts(package_root, manifest, artifacts, gate, blockers):
    adapter_ok = True
    adapters = {}
    for relative in manifest.get("adapters", []):
        ok, error = check_adapter_file(os.path.join(package_root, relative))
        if not ok:
            adapter_ok = False
            blockers.append("D13_ADAPTER_V3: {0}: {1}".format(relative, error))
        else:
            data = load_json(os.path.join(package_root, relative))
            adapters[data["adapterId"]] = data
    gate("D13_ADAPTER_V3", adapter_ok, "one or more adapters violate v3")

    primary_ok = set(adapters) >= PRIMARY_ADAPTERS and all(
        adapters[name].get("enabled") and adapters[name].get("supportLevel") == "primary-native"
        for name in PRIMARY_ADAPTERS
    )
    gate("D14_PRIMARY_ADAPTERS", primary_ok, "Codex and Antigravity must be primary-native")

    codex = adapters.get("codex", {})
    codex_mappings = {item.get("artifactId"): item for item in codex.get("artifactMappings", [])}
    codex_policy = codex_mappings.get("gemini-policy", {})
    codex_ok = (
        codex.get("router", {}).get("path") == "AGENTS.md"
        and codex.get("roots", {}).get("config", {}).get("default") == "~/.codex"
        and codex.get("roots", {}).get("skills", {}).get("default") == "~/.agents/skills"
        and codex_policy.get("root") == "config"
        and codex_policy.get("relativePath") == ""
        and codex_policy.get("native") is True
        and codex.get("capabilities", {}).get("nativeSlashWorkflows") is False
        and codex.get("capabilities", {}).get("nativeProgressiveSkills") is True
    )
    gate("D15_CODEX_NATIVE", codex_ok, "Codex native bindings are incorrect")

    anti = adapters.get("antigravity", {})
    anti_mappings = {item.get("artifactType"): item for item in anti.get("artifactMappings", [])}
    anti_ok = (
        anti.get("router", {}).get("path") == "GEMINI.md"
        and anti.get("roots", {}).get("config", {}).get("default") == "~/.gemini"
        and anti_mappings.get("workflow", {}).get("relativePath") == "config/global_workflows"
        and anti_mappings.get("skill", {}).get("relativePath") == "antigravity/skills"
        and anti.get("capabilities", {}).get("maxRuleChars") == 12000
        and anti.get("capabilities", {}).get("maxWorkflowChars") == 12000
    )
    gate("D16_ANTIGRAVITY_NATIVE", anti_ok, "Antigravity native bindings are incorrect")

    size_ok = all(
        len(_read_text(os.path.join(package_root, item["source"]))) <= 12000
        for item in artifacts if item.get("type") in {"rule", "workflow"}
    )
    gate("D17_ANTIGRAVITY_SIZE_LIMIT", size_ok, "rule/workflow exceeds 12,000 chars")

    family_ok = True
    family_paths = {}
    for adapter in adapters.values():
        if not adapter.get("enabled"):
            continue
        family = adapter.get("router", {}).get("family")
        path = adapter.get("router", {}).get("path")
        if family in family_paths and family_paths[family] != path:
            family_ok = False
        family_paths[family] = path
    gate("D18_ROUTER_FAMILY_COLLISION", family_ok, "same runtime family maps different router paths")
    return adapters


def _check_source_integrity(package_root, manifest, context, sources, adapters, artifacts, gate):
    session_ok = False
    try:
        session_schema = load_json(os.path.join(package_root, "schemas", "wsr-session-v1.schema.json"))
        session_ok = _session_schema_ok(session_schema) and context.get("resumeContract", {}).get("approvalPersistence") is False
    except Exception:
        pass
    gate("D19_RESUME_AUTHORITY", session_ok, "resume schema may persist authority")

    containment_ok = False
    try:
        probe = os.path.join(package_root, "resume", "checkpoint.json")
        relative = os.path.relpath(probe, package_root)
        containment_ok = wsr_common.safe_resolve_path(package_root, relative) == os.path.realpath(probe)
        try:
            wsr_common.safe_resolve_path(package_root, "../escape")
            containment_ok = False
        except ValueError:
            pass
    except Exception:
        pass
    gate("D20_RESUME_CONTAINMENT", containment_ok, "resume path containment failed")

    syntax_ok = True
    encoding_ok = True
    for relative in _all_package_files(package_root, manifest.get("packageExclusions", [])):
        path = os.path.join(package_root, relative)
        try:
            raw = open(path, "rb").read()
            if raw.startswith(b"\xef\xbb\xbf") or b"\x00" in raw:
                encoding_ok = False
            text = raw.decode("utf-8", errors="strict")
            if "\ufffd" in text:
                encoding_ok = False
            if relative.endswith(".py"):
                ast.parse(text, filename=relative)
        except (OSError, UnicodeError, SyntaxError):
            if relative.endswith(".py"):
                syntax_ok = False
            else:
                encoding_ok = False
    gate("D21_PYTHON_SYNTAX", syntax_ok, "Python syntax failure")
    gate("D22_UTF8", encoding_ok, "invalid UTF-8/BOM/NUL detected")

    forbidden_ok = True
    for relative in ("scripts/wsr_reload.py", "scripts/sync_config.py"):
        text = _read_text(os.path.join(package_root, relative))
        if "ThreadPoolExecutor" in text or "--force-sync" in text or "gitnexus" in text.lower():
            forbidden_ok = False
    gate("D23_RUNTIME_BOUNDARY", forbidden_ok, "forbidden runtime dependency or bypass found")

    declared = set(sources)
    actual = set(_all_package_files(package_root, manifest.get("packageExclusions", [])))
    gate(
        "D24_ORPHAN_FILES",
        actual == declared,
        "undeclared={0}; missing={1}".format(sorted(actual - declared), sorted(declared - actual)),
    )

    router_ok = False
    try:
        import sync_config

        rendered = sync_config.render_router(package_root, manifest)
        router_ok = (
            len(rendered.encode("utf-8")) <= 4096
            and "all_workflows" not in rendered
            and "all_skills" not in rendered
            and manifest["buildId"] in rendered
        )
    except Exception:
        pass
    gate("D25_ROUTER_MINIMAL", router_ok, "router exceeds 4 KiB or requests bulk loading")

    native_plan_ok = True
    try:
        import sync_config

        checksums = sync_config.compute_checksums(package_root, manifest)
        for name in PRIMARY_ADAPTERS:
            adapter = adapters[name]
            probe = os.path.join(package_root, ".doctor-probe", name)
            overrides = {
                root_name: os.path.join(probe, root_name)
                for root_name in adapter["roots"] if root_name != "config"
            }
            plan = sync_config.build_deployment_plan(
                package_root, probe, manifest, adapter, checksums, overrides,
            )
            destinations = [os.path.normcase(item["destination_path"]) for item in plan]
            if len(destinations) != len(set(destinations)):
                raise ValueError("destination collision for {0}".format(name))
    except Exception as error:
        native_plan_ok = False
        native_plan_detail = str(error)
    else:
        native_plan_detail = ""
    gate("D26_NATIVE_PLAN", native_plan_ok, native_plan_detail)

    mapping_ok, mapping_detail = _mapping_contract_ok(adapters, artifacts)
    gate("D31_MAPPING_CONTRACT", mapping_ok, mapping_detail)


def _check_release_contracts(package_root, manifest, context, adapters, version, gate, warnings):
    doc_versions_ok = True
    for relative in ("GEMINI.md", "AGENTS.md", "README.md", "CHANGELOG.md"):
        try:
            text = _read_text(os.path.join(package_root, relative))
            if version not in text:
                doc_versions_ok = False
        except OSError:
            doc_versions_ok = False
    gate("D27_VERSION_DRIFT", doc_versions_ok, "core documents do not carry current semantic version")

    schema_ok = True
    schema_detail = ""
    schema_files = (
        "schemas/wsr-manifest-v2.schema.json", "schemas/wsr-context-v2.schema.json",
        "schemas/wsr-adapter-v3.schema.json", "schemas/wsr-session-v1.schema.json",
        "schemas/wsr-active-v1.schema.json", "schemas/wsr-audit-report-v1.schema.json",
        "schemas/wsr-goal-v1.schema.json",
    )
    for relative in schema_files:
        try:
            schema = load_json(os.path.join(package_root, relative))
            valid, detail = validate_schema_semantics(schema)
            if not valid:
                raise ValueError(detail)
        except Exception as error:
            schema_ok = False
            schema_detail = "{0}: {1}".format(relative, error)
            break
    gate("D28_SCHEMA_SET", schema_ok, schema_detail or "schema set is incomplete or invalid")

    audit_contract_ok = all(os.path.exists(os.path.join(package_root, relative)) for relative in (
        "scripts/wsr_audit.py", "scripts/wsr_audit_checks.py", "skills/wsr-audit/SKILL.md",
        "tests/audit/fixtures.json", "tests/audit/run_fixtures.py",
        "schemas/wsr-audit-report-v1.schema.json", "tests/conformance/run_conformance.py",
    ))
    gate("D30_AUDIT_CONTRACT", audit_contract_ok, "audit runtime, skill, schema and fixtures must be present")

    goal_ok, goal_detail = _goal_contract_ok(package_root, context, adapters)
    gate("D33_GOAL_CONTRACT", goal_ok, goal_detail or "Goal scope, parser, thresholds and native capabilities must agree")

    evidence_ok, evidence_detail = _evidence_contract_ok(package_root, manifest)
    gate("D32_EVIDENCE_BINDING", evidence_ok, evidence_detail)
    if evidence_ok and manifest.get("status") == "Released":
        index = load_json(os.path.join(package_root, "evidence", "cross-ide-conformance", "index.json"))
        active = load_json(wsr_common.safe_resolve_path(package_root, index["activeRun"]))
        audit = active.get("audit", {})
        if audit.get("status") not in {"PASS", "WARN"} or audit.get("blockers", 0) or audit.get("high", 0):
            warnings.append("released evidence contains a non-release-safe audit result")


def _doctor_results(manifest, version, build_id, runtime_mode, strict, blockers, warnings, checks):
    passed = sum(item["status"] == "PASS" for item in checks)
    total = len(checks)
    score = int((passed * 100) / total) if total else 0
    status = "PASS" if passed == total else "FAIL"
    if strict and warnings:
        blockers.extend("STRICT: {0}".format(item) for item in warnings)
        status = "FAIL"
    results = {
        "packageName": manifest.get("packageName"),
        "version": version,
        "buildId": build_id,
        "status": status,
        "score": score,
        "mode": "runtime" if runtime_mode else "source",
        "strict": bool(strict),
        "blockers": blockers,
        "warnings": warnings,
        "checks": checks,
    }
    return results, passed, total


def run_doctor_checks(
    package_root, strict=False, is_json=False, adapter_name=None,
    target_root=None, runtime_mode=False, root_overrides=None, source_mode=None,
):
    package_root = os.path.realpath(os.path.abspath(package_root))
    source_mode = not runtime_mode if source_mode is None else source_mode
    if source_mode and runtime_mode:
        raise ValueError("source mode and runtime mode are mutually exclusive")
    if not source_mode and not runtime_mode:
        raise ValueError("Doctor requires source mode or runtime mode")
    checks = []
    blockers = []
    warnings = []

    def gate(name, passed, detail=""):
        checks.append({"gate": name, "status": "PASS" if passed else "FAIL", "detail": detail})
        if not passed:
            blockers.append("{0}: {1}".format(name, detail or "failed"))

    try:
        manifest = load_json(os.path.join(package_root, "WSR_MANIFEST.json"))
        gate("D01_MANIFEST_PARSE", True)
    except Exception as error:
        manifest = None
        gate("D01_MANIFEST_PARSE", False, str(error))

    if not manifest:
        results = {
            "packageName": None, "version": None, "buildId": None,
            "status": "FAIL", "score": 0, "mode": "runtime" if runtime_mode else "source",
            "strict": bool(strict), "blockers": blockers, "warnings": warnings, "checks": checks,
        }
        return results, 0, len(checks)

    version, build_id, artifacts, sources, context = _check_manifest_contracts(
        package_root, manifest, gate,
    )
    _check_context_contracts(package_root, manifest, context, gate, adapter_name)
    adapters = _check_adapter_contracts(package_root, manifest, artifacts, gate, blockers)
    _check_source_integrity(package_root, manifest, context, sources, adapters, artifacts, gate)
    _check_release_contracts(package_root, manifest, context, adapters, version, gate, warnings)

    if runtime_mode:
        try:
            if not adapter_name or not target_root:
                raise ValueError("runtime mode requires adapter and target root")
            _validate_runtime(package_root, manifest, adapter_name, target_root, root_overrides or {})
            gate("D29_RUNTIME_BINDING", True)
        except Exception as error:
            gate("D29_RUNTIME_BINDING", False, str(error))

    return _doctor_results(
        manifest, version, build_id, runtime_mode, strict, blockers, warnings, checks,
    )


def main():
    parser = argparse.ArgumentParser(description="WSR Core Doctor")
    parser.add_argument("--path", default=None)
    parser.add_argument("--strict", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--source-mode", action="store_true")
    mode.add_argument("--runtime-mode", action="store_true")
    parser.add_argument("--adapter")
    parser.add_argument("--target-root")
    parser.add_argument("--root-override", action="append")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    package_root = os.path.realpath(os.path.abspath(args.path or wsr_common.get_package_root()))
    root_overrides = {}
    try:
        if args.root_override:
            import sync_config
            root_overrides = sync_config.parse_root_overrides(args.root_override)
        results, passed, total = run_doctor_checks(
            package_root, args.strict, args.json, args.adapter, args.target_root,
            args.runtime_mode, root_overrides,
            source_mode=args.source_mode or not args.runtime_mode,
        )
    except Exception as error:
        results = {
            "packageName": None, "version": None, "buildId": None,
            "status": "FAIL", "score": 0, "blockers": [str(error)], "checks": [],
        }
        passed, total = 0, 0

    if args.json:
        wsr_common.print_json_report(results)
    else:
        print("WSR DOCTOR: {0} ({1}/100, {2}/{3} gates)".format(
            results["status"], results["score"], passed, total,
        ))
        for blocker in results["blockers"]:
            print(" - {0}".format(blocker))
    return wsr_common.EXIT_SUCCESS if results["status"] == "PASS" else wsr_common.EXIT_FAIL_FINDING


if __name__ == "__main__":
    sys.exit(main())
