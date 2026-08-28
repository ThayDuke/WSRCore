import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True

import wsr_common


ADAPTER_KEYS = {
    "schemaVersion", "adapterId", "runtimeFamily", "enabled", "supportLevel",
    "roots", "discoveryPrecedence", "artifactMappings", "router", "state",
    "capabilities", "legacyRoots", "unsupportedFeatures",
}


def run_doctor_preflight(package_root):
    doctor = os.path.join(package_root, "scripts", "wsr_doctor.py")
    if not os.path.isfile(doctor):
        return False, "wsr_doctor.py not found", wsr_common.EXIT_FAIL_FINDING
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, doctor, "--path", package_root, "--source-mode", "--strict", "--json"],
        capture_output=True, text=True, encoding="utf-8", errors="strict", env=env, check=False,
    )
    return result.returncode == 0, result.stdout or result.stderr, result.returncode


def load_adapter_config(package_root, adapter_name, manifest):
    adapter_rel = "adapters/{0}.json".format(adapter_name)
    if adapter_rel not in manifest.get("adapters", []):
        raise ValueError("Adapter '{0}' is not declared".format(adapter_name))
    with open(os.path.join(package_root, adapter_rel), "r", encoding="utf-8") as stream:
        adapter = json.load(stream)
    if adapter.get("schemaVersion") != 3 or set(adapter) != ADAPTER_KEYS:
        raise ValueError("Adapter '{0}' does not satisfy the exact v3 contract".format(adapter_name))
    if adapter.get("adapterId") != adapter_name:
        raise ValueError("Adapter identity mismatch: {0}".format(adapter_name))
    return adapter


def _resolve_root(spec, override=None):
    value = override
    if not value and spec.get("environmentVariable"):
        value = os.environ.get(spec["environmentVariable"])
    if not value:
        value = spec.get("default")
    if not value:
        if spec.get("requiresExplicit"):
            raise ValueError("Adapter root requires an explicit override")
        raise ValueError("Adapter root could not be resolved")
    return os.path.realpath(os.path.abspath(os.path.expanduser(value)))


def resolve_roots(adapter_config, config_override=None, root_overrides=None):
    overrides = dict(root_overrides or {})
    if config_override:
        overrides["config"] = config_override
    roots = {}
    for name, spec in adapter_config.get("roots", {}).items():
        roots[name] = _resolve_root(spec, overrides.get(name))
    unknown = set(overrides) - set(roots)
    if unknown:
        raise ValueError("Unknown root override(s): {0}".format(sorted(unknown)))
    return roots


def get_target_root(adapter_config, cli_target_root):
    return resolve_roots(adapter_config, config_override=cli_target_root)["config"]


def resolve_logical_roots(target_root, adapter_config):
    return resolve_roots(adapter_config, config_override=target_root)


def select_mapping(artifact, mappings):
    for mapping in mappings:
        if mapping.get("artifactId") == artifact.get("id"):
            return mapping
    for mapping in mappings:
        if not mapping.get("artifactId") and mapping.get("artifactType") == artifact.get("type"):
            return mapping
    return None


def command_index(context):
    rows = []
    for name, item in sorted(context.get("commandMap", {}).items()):
        suffix = " -> /{0}".format(item["aliasOf"]) if item.get("aliasOf") else ""
        rows.append("- `/{0}`{1} => `{2}`: {3}".format(
            name, suffix, item.get("workflow", ""), item.get("description", ""),
        ))
    return "\n".join(rows)


def render_router(package_root, manifest):
    package_root = os.path.realpath(os.path.abspath(package_root))
    template_path = wsr_common.safe_resolve_path(package_root, "bootstrap/router.md.template")
    kernel_path = wsr_common.safe_resolve_path(package_root, "GEMINI.md")
    context_path = wsr_common.safe_resolve_path(
        package_root, manifest.get("contextFile", "WSR_CONTEXT.json"),
    )
    with open(template_path, "r", encoding="utf-8") as stream:
        rendered = stream.read()
    with open(kernel_path, "r", encoding="utf-8") as stream:
        kernel = stream.read().strip()
    with open(context_path, "r", encoding="utf-8") as stream:
        context = json.load(stream)
    replacements = {
        "{{PACKAGE_NAME}}": manifest.get("packageName", "WSR-Core"),
        "{{VERSION}}": manifest.get("version", "unknown"),
        "{{BUILD_ID}}": manifest.get("buildId", "unknown"),
        "{{ACTIVE_SOURCE_ROOT}}": package_root.replace("\\", "/"),
        "{{MANIFEST_SHA256}}": wsr_common.calculate_sha256(os.path.join(package_root, "WSR_MANIFEST.json")),
        "{{KERNEL}}": kernel,
        "{{COMMAND_INDEX}}": command_index(context),
    }
    for token, value in replacements.items():
        rendered = rendered.replace(token, str(value))
    if "{{" in rendered or "}}" in rendered:
        raise ValueError("Router template contains unresolved placeholders")
    return rendered


def compute_checksums(package_root, manifest):
    result = {}
    path = wsr_common.safe_resolve_path(
        package_root, manifest.get("checksumsFile", "WSR_CHECKSUMS.json"),
    )
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as stream:
                result.update(json.load(stream))
        except (OSError, ValueError):
            pass
    for artifact in manifest.get("artifacts", []):
        source = artifact.get("source")
        if not source:
            continue
        source_path = wsr_common.safe_resolve_path(package_root, source)
        if source and source not in result and os.path.isfile(source_path):
            result[source] = wsr_common.calculate_sha256(source_path)
    return result


def _mapping_relative(source, mapping):
    parts = source.replace("\\", "/").split("/")
    if mapping.get("stripTopLevel") and len(parts) > 1:
        parts = parts[1:]
    prefix = mapping.get("relativePath", "")
    return os.path.join(prefix, *parts) if prefix else os.path.join(*parts)


def _operation(artifact_id, source_path, destination, root_name, root_path, source_hash, mutable, rendered=None):
    relative = os.path.relpath(destination, root_path).replace("\\", "/")
    wsr_common.safe_resolve_path(root_path, relative)
    exists = os.path.isfile(destination)
    destination_hash = wsr_common.calculate_sha256(destination) if exists else "N/A"
    action = "unchanged" if exists and destination_hash == source_hash else ("update" if exists else "create")
    item = {
        "id": artifact_id,
        "source_path": source_path,
        "destination_path": destination,
        "root": root_name,
        "root_path": root_path,
        "relative_destination": "{0}:{1}".format(root_name, relative),
        "current_state": "Drift" if exists and action == "update" else ("Exists" if exists else "Missing"),
        "desired_state": "Unchanged" if action == "unchanged" else action.title(),
        "action": action,
        "src_checksum": source_hash,
        "dest_checksum": destination_hash,
        "mutable": mutable,
    }
    if rendered is not None:
        item["rendered_content"] = rendered
    return item


def build_deployment_plan(package_root, target_root, manifest, adapter_config, checksums, root_overrides=None):
    package_root = os.path.realpath(os.path.abspath(package_root))
    roots = resolve_roots(adapter_config, config_override=target_root, root_overrides=root_overrides)
    mappings = adapter_config.get("artifactMappings", [])
    destinations = {}
    plan = []

    for artifact in manifest.get("artifacts", []):
        if not artifact.get("deploy", False):
            continue
        mapping = select_mapping(artifact, mappings)
        if mapping is None:
            continue
        root_name = mapping.get("root")
        if root_name not in roots:
            raise ValueError("Unknown root '{0}' for '{1}'".format(root_name, artifact["id"]))
        source_rel = artifact["source"]
        source_path = wsr_common.safe_resolve_path(package_root, source_rel)
        if not os.path.isfile(source_path):
            if artifact.get("required"):
                raise ValueError("Required artifact missing: {0}".format(source_rel))
            continue
        relative = _mapping_relative(source_rel, mapping)
        destination = wsr_common.safe_resolve_path(roots[root_name], relative)
        key = os.path.normcase(os.path.realpath(destination))
        if key in destinations:
            raise ValueError("Destination collision: '{0}' and '{1}'".format(artifact["id"], destinations[key]))
        destinations[key] = artifact["id"]
        source_hash = checksums.get(source_rel) or wsr_common.calculate_sha256(source_path)
        plan.append(_operation(
            artifact["id"], source_path, destination, root_name, roots[root_name],
            source_hash, artifact.get("mutable", True),
        ))

    router = adapter_config["router"]
    router_root = roots[router["root"]]
    router_destination = wsr_common.safe_resolve_path(router_root, router["path"])
    key = os.path.normcase(os.path.realpath(router_destination))
    if key in destinations:
        raise ValueError("Router destination collision with '{0}'".format(destinations[key]))
    rendered = render_router(package_root, manifest)
    rendered_hash = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    plan.append(_operation(
        "active-router", None, router_destination, router["root"], router_root,
        rendered_hash, True, rendered=rendered,
    ))
    return plan


def public_operation(operation):
    return {key: value for key, value in operation.items() if key not in {"rendered_content", "root_path"}}


def calculate_inventory_hash(plan):
    rows = ["{0}:{1}:{2}".format(op["id"], op["src_checksum"], op["relative_destination"]) for op in plan]
    return hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")).hexdigest()


def parse_root_overrides(values):
    result = {}
    for value in values or []:
        if "=" not in value:
            raise ValueError("Root override must use NAME=PATH")
        name, path = value.split("=", 1)
        if not name or not path or name in result:
            raise ValueError("Invalid or duplicate root override: {0}".format(value))
        result[name] = path
    return result


def _verify_destination(operation):
    relative = os.path.relpath(operation["destination_path"], operation["root_path"])
    return wsr_common.safe_resolve_path(operation["root_path"], relative)


def _write_marker(staging_dir, adapter, manifest, package_root, roots, plan, transaction_id):
    state = adapter["state"]
    marker_path = wsr_common.safe_resolve_path(roots[state["root"]], state["path"])
    content = {
        "schemaVersion": 1,
        "adapterIdentity": adapter["adapterId"],
        "packageVersion": manifest["version"],
        "buildId": manifest["buildId"],
        "manifestHash": wsr_common.calculate_sha256(os.path.join(package_root, "WSR_MANIFEST.json")),
        "inventoryHash": calculate_inventory_hash(plan),
        "routerHash": next(op["src_checksum"] for op in plan if op["id"] == "active-router"),
        "logicalRoots": roots,
        "installTimestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "transactionId": transaction_id,
    }
    staged = os.path.join(staging_dir, "active-marker.json")
    wsr_common.atomic_write_text(staged, json.dumps(content, indent=2))
    return marker_path, staged


def _write_transaction_journal(staging, journal):
    journal["updatedAt"] = time.time()
    path = wsr_common.safe_resolve_path(staging, "transaction.json")
    wsr_common.atomic_write_text(path, json.dumps(journal, indent=2, sort_keys=True))


def _recover_transaction(staging, roots, allow_recent=False):
    journal_path = wsr_common.safe_resolve_path(staging, "transaction.json")
    with open(journal_path, "r", encoding="utf-8", errors="strict") as stream:
        journal = json.load(stream)
    if journal.get("schemaVersion") != 1 or not isinstance(journal.get("operations"), list):
        raise RuntimeError("Transaction journal violates v1 contract: {0}".format(journal_path))
    if not allow_recent and time.time() - float(journal.get("updatedAt", 0)) < 60:
        raise RuntimeError("Another WSR transaction may still be active: {0}".format(staging))

    def paths(record):
        root_name = record.get("root")
        relative = record.get("relative")
        if root_name not in roots or not isinstance(relative, str):
            raise RuntimeError("Transaction journal references an unknown destination root")
        destination = wsr_common.safe_resolve_path(roots[root_name], relative)
        backup_relative = record.get("backupRelative")
        backup = (
            wsr_common.safe_resolve_path(roots[root_name], backup_relative)
            if backup_relative else None
        )
        return destination, backup

    records = list(journal["operations"])
    if journal.get("marker"):
        records.append(journal["marker"])
    if journal.get("committed"):
        for record in records:
            _, backup = paths(record)
            if backup and os.path.isfile(backup):
                os.remove(backup)
    else:
        for record in reversed(records):
            destination, backup = paths(record)
            if record.get("hadDestination"):
                if backup and os.path.isfile(backup):
                    if os.path.isfile(destination):
                        os.remove(destination)
                    os.replace(backup, destination)
                elif not (
                    os.path.isfile(destination)
                    and wsr_common.calculate_sha256(destination) == record.get("previousChecksum")
                ):
                    raise RuntimeError("Original destination cannot be recovered: {0}".format(destination))
            elif os.path.isfile(destination):
                os.remove(destination)

    shutil.rmtree(staging)


def apply_plan(package_root, adapter, manifest, roots, plan):
    changes = [op for op in plan if op["action"] != "unchanged"]
    config_root = roots["config"]
    os.makedirs(config_root, exist_ok=True)
    for name in sorted(os.listdir(config_root)):
        if not name.startswith(".wsr_staging_"):
            continue
        stale = wsr_common.safe_resolve_path(config_root, name)
        if not os.path.isdir(stale):
            raise RuntimeError("Invalid WSR staging entry: {0}".format(stale))
        _recover_transaction(stale, roots)

    transaction_id = "{0}_{1}_{2}".format(manifest["buildId"], time.time_ns(), os.getpid())
    staging = wsr_common.safe_resolve_path(
        config_root, ".wsr_staging_{0}".format(transaction_id),
    )
    os.makedirs(staging)
    staged = []
    journal = {
        "schemaVersion": 1,
        "transactionId": transaction_id,
        "createdAt": time.time(),
        "committed": False,
        "operations": [],
        "marker": None,
    }
    _write_transaction_journal(staging, journal)
    try:
        for index, operation in enumerate(changes):
            staged_path = wsr_common.safe_resolve_path(staging, "{0:04d}".format(index))
            if "rendered_content" in operation:
                wsr_common.atomic_write_text(staged_path, operation["rendered_content"])
            else:
                shutil.copy2(operation["source_path"], staged_path)
            if wsr_common.calculate_sha256(staged_path) != operation["src_checksum"]:
                raise RuntimeError("Staging checksum mismatch for {0}".format(operation["id"]))
            staged.append((staged_path, operation))

        for staged_path, operation in staged:
            destination = _verify_destination(operation)
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            if os.path.exists(destination) and not os.path.isfile(destination):
                raise RuntimeError("Destination is not a regular file: {0}".format(destination))
            had_destination = os.path.isfile(destination)
            backup = None
            backup_relative = None
            previous_checksum = None
            if had_destination:
                previous_checksum = wsr_common.calculate_sha256(destination)
                backup = "{0}.wsr_backup_{1}_tmp".format(destination, transaction_id)
                if os.path.exists(backup):
                    raise RuntimeError("Backup already exists: {0}".format(backup))
                backup_relative = os.path.relpath(backup, operation["root_path"]).replace("\\", "/")
                wsr_common.safe_resolve_path(operation["root_path"], backup_relative)
            journal["operations"].append({
                "root": operation["root"],
                "relative": os.path.relpath(destination, operation["root_path"]).replace("\\", "/"),
                "hadDestination": had_destination,
                "previousChecksum": previous_checksum,
                "backupRelative": backup_relative,
            })
            _write_transaction_journal(staging, journal)
            if backup:
                os.replace(destination, backup)
            shutil.copy2(staged_path, destination)
            if wsr_common.calculate_sha256(destination) != operation["src_checksum"]:
                raise RuntimeError("Destination checksum mismatch for {0}".format(operation["id"]))

        marker_path, marker_staged = _write_marker(staging, adapter, manifest, package_root, roots, plan, transaction_id)
        os.makedirs(os.path.dirname(marker_path), exist_ok=True)
        if os.path.exists(marker_path) and not os.path.isfile(marker_path):
            raise RuntimeError("Active marker is not a regular file: {0}".format(marker_path))
        marker_had_destination = os.path.isfile(marker_path)
        marker_backup = None
        marker_backup_relative = None
        marker_previous_checksum = None
        state = adapter["state"]
        marker_root = roots[state["root"]]
        if marker_had_destination:
            marker_previous_checksum = wsr_common.calculate_sha256(marker_path)
            marker_backup = "{0}.wsr_backup_{1}_tmp".format(marker_path, transaction_id)
            marker_backup_relative = os.path.relpath(marker_backup, marker_root).replace("\\", "/")
            wsr_common.safe_resolve_path(marker_root, marker_backup_relative)
        journal["marker"] = {
            "root": state["root"],
            "relative": os.path.relpath(marker_path, marker_root).replace("\\", "/"),
            "hadDestination": marker_had_destination,
            "previousChecksum": marker_previous_checksum,
            "backupRelative": marker_backup_relative,
        }
        _write_transaction_journal(staging, journal)
        if marker_backup:
            os.replace(marker_path, marker_backup)
        shutil.copy2(marker_staged, marker_path)
        if wsr_common.calculate_sha256(marker_path) != wsr_common.calculate_sha256(marker_staged):
            raise RuntimeError("Active marker checksum mismatch")

        journal["committed"] = True
        _write_transaction_journal(staging, journal)
        try:
            _recover_transaction(staging, roots, allow_recent=True)
        except Exception as cleanup_error:
            print("WSR Sync cleanup deferred: {0}".format(cleanup_error), file=sys.stderr)
        return {
            "schemaVersion": 1,
            "transactionId": transaction_id,
            "status": "COMMITTED",
            "changed": len(changes),
            "inventoryHash": calculate_inventory_hash(plan),
        }
    except Exception as error:
        try:
            _recover_transaction(staging, roots, allow_recent=True)
        except Exception as recovery_error:
            raise RuntimeError(
                "Transaction failed: {0}; recovery failed: {1}".format(error, recovery_error)
            ) from recovery_error
        raise


def main():
    parser = argparse.ArgumentParser(description="WSR v3 multi-root configuration synchronizer")
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--target-root", help="Legacy alias for config root override")
    parser.add_argument("--root-override", action="append", help="Repeatable NAME=PATH root override")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--approval-token")
    parser.add_argument("--allow-review", action="store_true")
    args = parser.parse_args()

    package_root = wsr_common.get_package_root()
    report = {"status": "BLOCKED"}
    try:
        manifest = wsr_common.load_manifest(package_root)
        adapter = load_adapter_config(package_root, args.adapter, manifest)
        if not adapter.get("enabled"):
            raise PermissionError("Adapter '{0}' is disabled".format(args.adapter))
        root_overrides = parse_root_overrides(args.root_override)
        roots = resolve_roots(adapter, config_override=args.target_root, root_overrides=root_overrides)

        healthy, detail, code = run_doctor_preflight(package_root)
        if not healthy:
            raise RuntimeError("Doctor preflight failed: {0}".format(detail.strip()))

        checksums = compute_checksums(package_root, manifest)
        plan = build_deployment_plan(package_root, roots["config"], manifest, adapter, checksums, root_overrides)
        changes = [op for op in plan if op["action"] != "unchanged"]
        router_changed = any(op["id"] == "active-router" and op["action"] != "unchanged" for op in plan)
        report = {
            "status": "PLAN",
            "adapter": args.adapter,
            "roots": roots,
            "build_id": manifest.get("buildId"),
            "total_operations": len(plan),
            "changes_count": len(changes),
            "restart_required": router_changed,
            "plan": [public_operation(op) for op in plan],
        }

        if args.apply:
            if manifest.get("status") == "Review" and not args.allow_review:
                raise PermissionError("Review deployment requires --allow-review")
            if args.approval_token != manifest.get("buildId"):
                raise PermissionError("Invalid or missing --approval-token")
            receipt = apply_plan(package_root, adapter, manifest, roots, plan)
            report["status"] = "SUCCESS"
            report["applied"] = receipt["changed"]
            report["receipt"] = receipt

        if args.json:
            wsr_common.print_json_report(report)
        else:
            print("WSR SYNC {0}: {1} change(s)".format(report["status"], report["changes_count"]))
            for operation in report["plan"]:
                print(" - [{0}] {1}".format(operation["action"].upper(), operation["relative_destination"]))
            if report.get("restart_required"):
                print("RESTART_REQUIRED: start a new IDE session after apply")
        return wsr_common.EXIT_SUCCESS
    except PermissionError as error:
        report.update({"status": "REJECTED", "message": str(error)})
        if args.json:
            wsr_common.print_json_report(report)
        else:
            print("WSR Sync REJECTED: {0}".format(error), file=sys.stderr)
        return wsr_common.EXIT_SAFETY_REJECTION
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        report.update({"status": "BLOCKED", "message": str(error)})
        if args.json:
            wsr_common.print_json_report(report)
        else:
            print("WSR Sync BLOCKED: {0}".format(error), file=sys.stderr)
        return wsr_common.EXIT_FAIL_FINDING


if __name__ == "__main__":
    sys.exit(main())
