import os
import sys
sys.dont_write_bytecode = True
import json
import re
import wsr_common

def log_message(msg, is_json, level="INFO"):
    if not is_json:
        if level == "FAIL":
            print(f"[-] ERROR: {msg}")
        elif level == "WARN":
            print(f"[!] WARNING: {msg}")
        else:
            print(f"[+] {msg}")

def check_containment(base_root, relative_path):
    """Strict path containment validation via realpath and commonpath."""
    abs_base = os.path.realpath(base_root)
    # Check if absolute path
    if os.path.isabs(relative_path) or relative_path.replace('\\', '/').startswith('/'):
        return False, "Absolute path not allowed"
        
    try:
        # Prevent sibling prefix bypass (e.g. root = /a/b, target = /a/b-sibling)
        abs_target = os.path.realpath(os.path.join(abs_base, relative_path))
        common = os.path.commonpath([abs_base, abs_target])
    except ValueError as e:
        return False, f"Invalid path or drive mismatch: {e}"
        
    if common != abs_base:
        return False, f"Path escapes root boundary: {relative_path}"
        
    # Symlink verification
    if os.path.islink(abs_target) or os.path.islink(os.path.join(abs_base, relative_path)):
        return False, "Symlinks or junctions are rejected for security"
        
    return True, ""

def validate_schema_semantics(schema):
    """Validate JSON Schema Draft-07 semantics supported by WSR JIT."""
    allowed_types = {"object", "integer", "string", "array", "boolean"}
    
    def validate_node(node, path="root"):
        if not isinstance(node, dict):
            return False, f"Schema node at '{path}' must be a dict"
            
        node_type = node.get("type")
        if not node_type:
            return False, f"Schema node at '{path}' is missing 'type'"
            
        if node_type not in allowed_types:
            return False, f"Unsupported or invalid schema type '{node_type}' at '{path}' (must be lowercase Draft-07: {allowed_types})"
            
        # Validate additional properties constraints
        for k in node.keys():
            if k not in {"type", "properties", "required", "enum", "items", "additionalProperties", "format", "$schema", "title"}:
                return False, f"Unsupported schema keyword '{k}' at '{path}'"
                
        if node_type == "object":
            if "properties" in node:
                if not isinstance(node["properties"], dict):
                    return False, f"'properties' at '{path}' must be a dict"
                for prop_name, prop_node in node["properties"].items():
                    ok, err = validate_node(prop_node, f"{path}.{prop_name}")
                    if not ok:
                        return False, err
            if "additionalProperties" in node:
                add_prop = node["additionalProperties"]
                if isinstance(add_prop, dict):
                    ok, err = validate_node(add_prop, f"{path}.additionalProperties")
                    if not ok:
                        return False, err
                elif not isinstance(add_prop, bool):
                    return False, f"'additionalProperties' at '{path}' must be dict or boolean"
                    
        elif node_type == "array":
            if "items" not in node:
                return False, f"'array' node at '{path}' must define 'items'"
            ok, err = validate_node(node["items"], f"{path}.items")
            if not ok:
                return False, err
                
        if "enum" in node:
            if not isinstance(node["enum"], list):
                return False, f"'enum' at '{path}' must be a list"
                
        return True, ""
        
    return validate_node(schema)

def validate_manifest_by_schema(manifest, schema):
    """Validate manifest data structure recursively against schema definitions JIT."""
    
    def validate_value(val, node_schema, path="manifest"):
        expected_type = node_schema.get("type")
        
        # Check type strictly (distinguishing bool from int)
        if expected_type == "integer":
            if isinstance(val, bool) or not isinstance(val, int):
                return False, f"'{path}' must be an integer, got {type(val).__name__}"
        elif expected_type == "boolean":
            if not isinstance(val, bool):
                return False, f"'{path}' must be a boolean, got {type(val).__name__}"
        elif expected_type == "string":
            if not isinstance(val, str):
                return False, f"'{path}' must be a string, got {type(val).__name__}"
        elif expected_type == "array":
            if not isinstance(val, list):
                return False, f"'{path}' must be an array/list, got {type(val).__name__}"
        elif expected_type == "object":
            if not isinstance(val, dict):
                return False, f"'{path}' must be an object/dict, got {type(val).__name__}"
                
        # Check enum
        if "enum" in node_schema:
            if val not in node_schema["enum"]:
                return False, f"'{path}' value '{val}' is not in allowed enums: {node_schema['enum']}"
                
        # Recursive object validation
        if expected_type == "object":
            # Check required keys
            for req in node_schema.get("required", []):
                if req not in val:
                    return False, f"Missing required property '{req}' at '{path}'"
                    
            properties = node_schema.get("properties", {})
            additional_props = node_schema.get("additionalProperties", True)
            
            for k, v in val.items():
                if k not in properties:
                    if additional_props is False:
                        return False, f"Unexpected property '{k}' at '{path}' (additionalProperties is false)"
                    elif isinstance(additional_props, dict):
                        ok, err = validate_value(v, additional_props, f"{path}.{k}")
                        if not ok:
                            return False, err
                else:
                    ok, err = validate_value(v, properties[k], f"{path}.{k}")
                    if not ok:
                        return False, err
                        
        # Recursive array validation
        elif expected_type == "array":
            items_schema = node_schema.get("items")
            if items_schema:
                for idx, item in enumerate(val):
                    ok, err = validate_value(item, items_schema, f"{path}[{idx}]")
                    if not ok:
                        return False, err
                        
        return True, ""
        
    return validate_value(manifest, schema)

def match_exclusion(rel_path, exclusions):
    import fnmatch
    for pattern in exclusions:
        if pattern.endswith('/'):
            dir_pat = pattern.rstrip('/')
            parts = rel_path.replace('\\', '/').split('/')
            if any(fnmatch.fnmatch(p, dir_pat) for p in parts):
                return True
        else:
            if fnmatch.fnmatch(os.path.basename(rel_path), pattern):
                return True
    return False

def check_adapter_file(adapter_path):
    if not os.path.exists(adapter_path):
        return False, f"Adapter file not found: {adapter_path}"
    try:
        with open(adapter_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Failed to parse adapter JSON: {e}"
        
    exact_fields = {
        "schemaVersion", "adapterId", "runtimeFamily", "enabled",
        "supportLevel", "defaultTargetRoot", "targetRootEnvironmentVariable",
        "requiresExplicitTargetRoot", "logicalRoots", "discoveryPrecedence",
        "artifactMappings", "routerContract", "activeMarkerContract",
        "unsupportedFeatures"
    }
    if data.get("schemaVersion") != 2 or set(data) != exact_fields:
        return False, "Adapter must use the exact v2 top-level contract"
    root_names = {"policyRoot", "rulesRoot", "workflowsRoot", "skillsRoot", "scriptsRoot", "stateRoot"}
    if set(data.get("logicalRoots", {})) != root_names:
        return False, "Adapter logicalRoots contract is incomplete or contains unknown roots"
    for name, value in data["logicalRoots"].items():
        if not isinstance(value, str) or not wsr_common.validate_relative_path(value):
            return False, f"Logical root '{name}' must be target-relative"
    if not isinstance(data.get("artifactMappings"), list):
        return False, "artifactMappings must be a v2 list"
    for mapping in data["artifactMappings"]:
        if not isinstance(mapping, dict) or not set(mapping).issubset({"artifactId", "artifactType", "logicalRoot", "relativePath"}):
            return False, "Adapter mapping contains unknown fields"
        if not mapping.get("artifactType"):
            return False, "Adapter mapping must declare artifactType"
        if mapping.get("logicalRoot") not in root_names:
            return False, f"Adapter mapping references unknown logical root: {mapping.get('logicalRoot')}"
        if not wsr_common.validate_relative_path(mapping.get("relativePath", "")):
            return False, "Adapter mapping relativePath escapes its logical root"
    for contract_name in ("routerContract", "activeMarkerContract"):
        contract = data.get(contract_name)
        if not isinstance(contract, dict) or "path" not in contract:
            return False, f"{contract_name} is invalid"
        if contract.get("path") and not wsr_common.validate_relative_path(contract["path"]):
            return False, f"{contract_name}.path must be target-relative"
    return True, ""

def run_doctor_checks(package_root, strict=False, is_json=False, adapter_name=None, target_root=None, runtime_mode=False):
    """Run all source and optional runtime conformance gates."""
    results = {
        "packageName": None,
        "version": None,
        "buildId": None,
        "status": "FAIL",
        "score": 0,
        "blockers": [],
        "warnings": []
    }
    
    gates_total = 32
    gates_passed = 0
    
    # Gate 1: Manifest parse
    manifest = None
    try:
        manifest = wsr_common.load_manifest(package_root)
        gates_passed += 1
    except Exception as e:
        results["blockers"].append(f"Gate 1 Failed: Manifest load/parse error: {e}")
        
    # Proceed only if manifest loaded
    if manifest:
        results["packageName"] = manifest.get("packageName")
        results["version"] = manifest.get("version")
        results["buildId"] = manifest.get("buildId")
        
        # Load physical schema
        schema = None
        schema_path = os.path.join(package_root, "schemas", "wsr-manifest-v2.schema.json")
        if os.path.exists(schema_path):
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema = json.load(f)
            except Exception as e:
                results["blockers"].append(f"Failed to load physical manifest schema: {e}")
                
        # Gate 2: Schema v2 validation JIT
        if schema:
            schema_sem_ok, schema_sem_msg = validate_schema_semantics(schema)
            if schema_sem_ok:
                schema_ok, schema_msg = validate_manifest_by_schema(manifest, schema)
                if schema_ok:
                    gates_passed += 1
                else:
                    results["blockers"].append(f"Gate 2 Failed: Schema validation: {schema_msg}")
            else:
                results["blockers"].append(f"Gate 2 Failed: Schema semantics invalid: {schema_sem_msg}")
        else:
            results["blockers"].append("Gate 2 Failed: Physical schema file not found")
            
        # Collect physical files
        physical_files = []
        exclusions = manifest.get("packageExclusions", [])
        
        for root, dirs, files in os.walk(package_root, followlinks=False):
            # Prune .git, .venv directories in-place
            dirs_to_remove = []
            for d in dirs:
                rel_d = os.path.relpath(os.path.join(root, d), package_root)
                if d in [".git", ".venv"] or match_exclusion(rel_d, exclusions):
                    dirs_to_remove.append(d)
            for d in dirs_to_remove:
                dirs.remove(d)
                
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, package_root).replace('\\', '/')
                
                # Check exclusion
                if not match_exclusion(rel_path, exclusions):
                    physical_files.append(rel_path)
                    
        # Gate 3: Inventory completeness
        artifact_sources = [a["source"].replace('\\', '/') for a in manifest.get("artifacts", [])]
        missing_in_manifest = []
        for pf in physical_files:
            if pf not in artifact_sources:
                missing_in_manifest.append(pf)
                
        # Validate unique ID and source
        ids = set()
        sources = set()
        unique_check = True
        for art in manifest.get("artifacts", []):
            art_id = art.get("id")
            art_src = art.get("source").replace('\\', '/')
            if art_id in ids:
                unique_check = False
                results["blockers"].append(f"Duplicate artifact ID found in manifest: {art_id}")
            if art_src in sources:
                unique_check = False
                results["blockers"].append(f"Duplicate artifact source found in manifest: {art_src}")
            ids.add(art_id)
            sources.add(art_src)
            
        if not missing_in_manifest and unique_check:
            gates_passed += 1
        else:
            if missing_in_manifest:
                results["blockers"].append(f"Gate 3 Failed: Physical files not registered in manifest: {missing_in_manifest}")
            if not unique_check:
                results["blockers"].append("Gate 3 Failed: Artifacts list contains duplicate IDs or sources")
            
        # Gate 4: Required artifacts exist
        missing_required = []
        for art in manifest.get("artifacts", []):
            if art.get("required", False):
                resolved = os.path.join(package_root, art["source"])
                if not os.path.exists(resolved):
                    missing_required.append(art["source"])
        if not missing_required:
            gates_passed += 1
        else:
            results["blockers"].append(f"Gate 4 Failed: Required artifacts missing from filesystem: {missing_required}")
            
        # Gate 5: Package exclusion works
        exclusion_violation = []
        for art in manifest.get("artifacts", []):
            if match_exclusion(art["source"], exclusions):
                exclusion_violation.append(art["source"])
        if not exclusion_violation:
            gates_passed += 1
        else:
            results["blockers"].append(f"Gate 5 Failed: Excluded file pattern found in manifest inventory: {exclusion_violation}")
            
        # Gate 6: No bytecode or cache in actual directories
        bytecode_files = []
        for root, _, files in os.walk(package_root, followlinks=False):
            if "__pycache__" in root:
                bytecode_files.append(root)
            for file in files:
                if file.endswith(".pyc"):
                    bytecode_files.append(os.path.join(root, file))
        if not bytecode_files:
            gates_passed += 1
        else:
            results["blockers"].append(f"Gate 6 Failed: Pycache or bytecode files found: {bytecode_files[:5]}")
            
        # Gate 7: Workflow commands script exist and options match contract
        missing_commands_scripts = []
        options_drift = False
        allowed_audit_options = {"--mode", "--path", "--json", "--changed"}
        allowed_clean_options = {"--root", "--apply", "--json", "--approval-token"}
        
        commands = manifest.get("commands", {})
        if "audit" in commands:
            audit_opts = set(commands["audit"].get("options", {}).keys())
            if audit_opts != allowed_audit_options:
                options_drift = True
                results["blockers"].append(f"Audit command options drift: manifest has {audit_opts}, expected {allowed_audit_options}")
                
        if "clean" in commands:
            clean_opts = set(commands["clean"].get("options", {}).keys())
            if clean_opts != allowed_clean_options:
                options_drift = True
                results["blockers"].append(f"Clean command options drift: manifest has {clean_opts}, expected {allowed_clean_options}")
                
        for cmd_name, cmd_info in commands.items():
            script_rel = cmd_info.get("script")
            if script_rel and not script_rel.endswith('.md'): # skip md workflows
                resolved_script = os.path.join(package_root, script_rel)
                if not os.path.exists(resolved_script):
                    missing_commands_scripts.append(f"{cmd_name} -> {script_rel}")
        if not missing_commands_scripts and not options_drift:
            gates_passed += 1
        else:
            if missing_commands_scripts:
                results["blockers"].append(f"Gate 7 Failed: Command scripts do not exist: {missing_commands_scripts}")
            if options_drift:
                results["blockers"].append("Gate 7 Failed: CLI options drift detected in manifest")
            
        # Gate 8: Skill path exists JIT validation
        missing_skills = []
        for art in manifest.get("artifacts", []):
            if art.get("type") == "skill":
                resolved_skill = os.path.join(package_root, art["source"])
                if not os.path.exists(resolved_skill):
                    missing_skills.append(art["source"])
                # Containment check
                ok, err = check_containment(package_root, art["source"])
                if not ok:
                    results["blockers"].append(f"Skill containment error: {art['source']} - {err}")
        if not missing_skills:
            gates_passed += 1
        else:
            results["blockers"].append(f"Gate 8 Failed: Skill files missing or escaped root: {missing_skills}")
            
        # Gate 9: Rule path exists JIT validation
        missing_rules = []
        for art in manifest.get("artifacts", []):
            if art.get("type") == "rule":
                resolved_rule = os.path.join(package_root, art["source"])
                if not os.path.exists(resolved_rule):
                    missing_rules.append(art["source"])
                # Containment check
                ok, err = check_containment(package_root, art["source"])
                if not ok:
                    results["blockers"].append(f"Rule containment error: {art['source']} - {err}")
        if not missing_rules:
            gates_passed += 1
        else:
            results["blockers"].append(f"Gate 9 Failed: Rule files missing or escaped root: {missing_rules}")
            
        # Gate 10: Adapter schemas valid
        invalid_adapters = []
        for adapter_rel in manifest.get("adapters", []):
            resolved_adapter = os.path.join(package_root, adapter_rel)
            ok, err_msg = check_adapter_file(resolved_adapter)
            if not ok:
                invalid_adapters.append(f"{adapter_rel}: {err_msg}")
        if not invalid_adapters:
            gates_passed += 1
        else:
            results["blockers"].append(f"Gate 10 Failed: Adapter configuration invalid: {invalid_adapters}")
            
        # Gate 11: Target mapping safety via realpath/commonpath
        invalid_mappings = []
        for adapter_rel in manifest.get("adapters", []):
            resolved_adapter = os.path.join(package_root, adapter_rel)
            if os.path.exists(resolved_adapter):
                try:
                    with open(resolved_adapter, "r", encoding="utf-8") as f:
                        adapter_data = json.load(f)
                    mappings = adapter_data.get("artifactMappings", {})
                    # Simulating a temporary dummy target root to test path containment
                    dummy_target = os.path.join(package_root, "dummy_target_sandbox")
                    mapping_items = []
                    if isinstance(mappings, list):
                        for m in mappings:
                            mapping_items.append((m.get("artifactType", ""), m.get("relativePath", "")))
                    elif isinstance(mappings, dict):
                        for k, v in mappings.items():
                            mapping_items.append((k, v))
                    for k, val in mapping_items:
                        if not val:
                            continue
                        if val.endswith('/') or val.endswith('\\'):
                            test_path = os.path.join(val, "test_file.txt")
                        else:
                            test_path = val
                        ok, err = check_containment(dummy_target, test_path)
                        if not ok:
                            invalid_mappings.append(f"{adapter_rel} mapping '{k}': '{val}' fails containment: {err}")
                except Exception as e:
                    invalid_mappings.append(f"{adapter_rel} parse error during mapping check: {e}")
        if not invalid_mappings:
            gates_passed += 1
        else:
            results["blockers"].append(f"Gate 11 Failed: Adapter mapping safety violation: {invalid_mappings}")
            
        # Gate 12: Policy SSOT exists (GEMINI.md)
        policy_ssot_path = os.path.join(package_root, manifest.get("policySource", "GEMINI.md"))
        if os.path.exists(policy_ssot_path):
            gates_passed += 1
        else:
            results["blockers"].append(f"Gate 12 Failed: Policy SSOT file '{manifest.get('policySource')}' not found")
            
        # Gate 13: README canonical path check
        readme_path = os.path.join(package_root, "README.html")
        readme_canonical_ok = True
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8", errors="strict") as f:
                readme_content = f.read()
            if ".gemini" in readme_content.lower() and "canonical" in readme_content.lower():
                readme_canonical_ok = False
                results["warnings"].append("README mentions .gemini as canonical instead of .agents")
        if readme_canonical_ok:
            gates_passed += 1
        else:
            results["warnings"].append("Gate 13 Warned: README contains potential canonical path drifts")
            
        # Gate 14: Installation Guide build folder check
        install_guide_path = os.path.join(package_root, "Installation_guide.txt")
        guide_clean = True
        if os.path.exists(install_guide_path):
            with open(install_guide_path, "r", encoding="utf-8", errors="strict") as f:
                guide_content = f.read()
            if re.search(r"WSR-Core_v\d+\.\d+\.\d+_\d+", guide_content) or "DOCS/WSR-Core" in guide_content:
                guide_clean = False
                results["warnings"].append("Installation guide contains static build path references")
        if guide_clean:
            gates_passed += 1
        else:
            results["warnings"].append("Gate 14 Warned: Installation guide contains hardcoded build directory paths")
            
        # Gate 15: Debt schema uniformity
        debt_clean = True
        for art in manifest.get("artifacts", []):
            if "debt" in art["id"]:
                resolved_debt = os.path.join(package_root, art["source"])
                if os.path.exists(resolved_debt):
                    with open(resolved_debt, "r", encoding="utf-8") as f:
                        debt_content = f.read()
                    if "dec-debt" in debt_content and "wsr-debt" not in debt_content:
                        debt_clean = False
                        results["warnings"].append(f"Debt artifact {art['source']} uses legacy dec-debt schema without wsr-debt migration")
        if debt_clean:
            gates_passed += 1
        else:
            results["warnings"].append("Gate 15 Warned: Debt schema contains non-canonical references")
            
        # Gate 16: Check checksum coverage and verification & output profile JSON conflict check
        checksums_file = manifest.get("checksumsFile", "WSR_CHECKSUMS.json")
        checksums_path = os.path.join(package_root, checksums_file)
        checksums_verification_ok = True
        
        if os.path.exists(checksums_path):
            try:
                with open(checksums_path, "r", encoding="utf-8") as f:
                    checksums = json.load(f)
                # Verify checksum coverage using a unified expected sources set (excluding the checksum file itself)
                expected_sources = {a["source"].replace('\\', '/') for a in manifest.get("artifacts", []) if a["id"] != "wsr-checksums"}
                
                for art in manifest.get("artifacts", []):
                    rel_src = art["source"].replace('\\', '/')
                    if rel_src not in expected_sources:
                        continue
                    if rel_src not in checksums:
                        checksums_verification_ok = False
                        results["blockers"].append(f"Checksums file is missing entry for artifact: {rel_src}")
                    else:
                        # Verify actual file matches checksum JIT
                        abs_art = os.path.join(package_root, rel_src)
                        if os.path.exists(abs_art):
                            chk = wsr_common.calculate_sha256(abs_art)
                            if chk != checksums[rel_src]:
                                checksums_verification_ok = False
                                results["blockers"].append(f"Checksum mismatch for artifact: {rel_src}")
                                
                # Check for extra checksum entries (not defined in expected manifest artifacts)
                for chk_src in checksums:
                    if chk_src not in expected_sources:
                        checksums_verification_ok = False
                        results["blockers"].append(f"Extra checksum entry found in WSR_CHECKSUMS.json that is not in expected manifest artifacts: {chk_src}")
            except Exception as e:
                checksums_verification_ok = False
                results["blockers"].append(f"Checksums file parse error during preflight: {e}")
        else:
            # If checksums file doesn't exist, we only warn in Review phase, but RC requires it
            if manifest.get("status") in ["ReleaseCandidate", "Released"]:
                checksums_verification_ok = False
                results["blockers"].append(f"Checksums file '{checksums_file}' missing for release candidate status")
                
        # Output profile check: Ensure defaultSafetyModes finalLine is not enforced in JSON outputs
        safety_modes = manifest.get("defaultSafetyModes", {})
        if safety_modes.get("finalLine") == "Important-last" and is_json:
            checksums_verification_ok = False
            results["blockers"].append("Conflict: defaultSafetyModes finalLine is 'Important-last' but output mode is JSON")
            
        # D17: Context schema and identity binding
        context_ok = True
        context_file_rel = manifest.get("contextFile", "WSR_CONTEXT.json")
        context_path = os.path.join(package_root, context_file_rel)
        context_schema_path = os.path.join(package_root, "schemas", "wsr-context-v1.schema.json")

        if not os.path.exists(context_schema_path):
            context_ok = False
            results["blockers"].append("D17 Failed: Physical context schema file not found")
        elif not os.path.exists(context_path):
            context_ok = False
            results["blockers"].append(f"D17 Failed: Context file '{context_file_rel}' not found")
        else:
            try:
                with open(context_schema_path, "r", encoding="utf-8") as f:
                    ctx_schema = json.load(f)
                with open(context_path, "r", encoding="utf-8") as f:
                    ctx_data = json.load(f)

                sem_ok, sem_err = validate_schema_semantics(ctx_schema)
                if not sem_ok:
                    context_ok = False
                    results["blockers"].append(f"D17 Failed: Context schema semantics invalid: {sem_err}")
                else:
                    val_ok, val_err = validate_manifest_by_schema(ctx_data, ctx_schema)
                    if not val_ok:
                        context_ok = False
                        results["blockers"].append(f"D17 Failed: Context file validation error: {val_err}")
                    else:
                        # Identity binding check between manifest and context (C01, C02, D17)
                        m_ver, m_build = manifest.get("version"), manifest.get("buildId")
                        c_ver, c_build = ctx_data.get("version"), ctx_data.get("buildId")
                        if m_ver != c_ver or m_build != c_build:
                            context_ok = False
                            results["blockers"].append(f"D17 Failed: Identity binding mismatch: manifest ({m_ver} / {m_build}) vs context ({c_ver} / {c_build})")
                        manifest_hash = wsr_common.calculate_sha256(os.path.join(package_root, "WSR_MANIFEST.json"))
                        if ctx_data.get("manifestSha256") != manifest_hash:
                            context_ok = False
                            results["blockers"].append("D17 Failed: Context manifestSha256 does not match the active manifest")

                        # Validate 1-to-1 command contract coverage
                        manifest_cmds = set(manifest.get("commands", {}).keys())
                        ctx_cmds = set(ctx_data.get("commandMap", {}).keys())
                        if manifest_cmds != ctx_cmds:
                            context_ok = False
                            results["blockers"].append(f"D17 Failed: Command contract drift between manifest {manifest_cmds} and context {ctx_cmds}")
            except Exception as e:
                context_ok = False
                results["blockers"].append(f"D17 Failed: Context validation error: {e}")

        if context_ok:
            gates_passed += 1

        # D22-D23: Active marker presence and identity/hash binding
        marker_presence_ok = True
        marker_binding_ok = True
        if runtime_mode and (not adapter_name or not target_root):
            marker_presence_ok = False
            marker_binding_ok = False
            results["blockers"].append("D22 Failed: Runtime mode requires --adapter and --target-root")
        elif runtime_mode:
            try:
                adapter_path = os.path.join(package_root, "adapters", f"{adapter_name}.json")
                adapter_valid, adapter_error = check_adapter_file(adapter_path)
                if not adapter_valid:
                    raise ValueError(adapter_error)
                with open(adapter_path, "r", encoding="utf-8") as f:
                    runtime_adapter = json.load(f)
                marker_rel = runtime_adapter["activeMarkerContract"]["path"]
                marker_path = wsr_common.safe_resolve_path(target_root, marker_rel)
                if runtime_adapter["activeMarkerContract"].get("required") and not os.path.exists(marker_path):
                    raise FileNotFoundError(f"Required active marker not found: {marker_path}")
                marker_presence_ok = os.path.exists(marker_path)
                with open(marker_path, "r", encoding="utf-8") as f:
                    marker_data = json.load(f)
                marker_schema_path = os.path.join(package_root, "schemas", "wsr-active-v1.schema.json")
                with open(marker_schema_path, "r", encoding="utf-8") as f:
                    marker_schema = json.load(f)
                valid_marker, marker_error = validate_manifest_by_schema(marker_data, marker_schema)
                if not valid_marker:
                    raise ValueError(marker_error)
                manifest_hash = wsr_common.calculate_sha256(os.path.join(package_root, "WSR_MANIFEST.json"))
                if marker_data.get("adapterIdentity") != adapter_name:
                    raise ValueError("Active marker adapterIdentity mismatch")
                if marker_data.get("packageVersion") != manifest.get("version") or marker_data.get("buildId") != manifest.get("buildId"):
                    raise ValueError("Active marker package identity mismatch")
                if marker_data.get("manifestHash") != manifest_hash:
                    raise ValueError("Active marker manifestHash mismatch")
                import sync_config
                runtime_checksums = sync_config.compute_checksums(package_root, manifest)
                runtime_plan = sync_config.build_deployment_plan(package_root, target_root, manifest, runtime_adapter, runtime_checksums)
                if marker_data.get("inventoryHash") != sync_config.calculate_inventory_hash(runtime_plan):
                    raise ValueError("Active marker inventoryHash mismatch")
                router_path = wsr_common.safe_resolve_path(target_root, runtime_adapter["routerContract"]["path"])
                if os.path.exists(router_path) and marker_data.get("routerHash") != wsr_common.calculate_sha256(router_path):
                    raise ValueError("Active marker routerHash mismatch")
            except Exception as e:
                marker_presence_ok = marker_presence_ok and not isinstance(e, FileNotFoundError)
                marker_binding_ok = False
                if not marker_presence_ok:
                    results["blockers"].append(f"D22 Failed: {e}")
                results["blockers"].append(f"D23 Failed: Active marker validation error: {e}")
        if marker_presence_ok:
            gates_passed += 1
        if marker_binding_ok:
            gates_passed += 1

        # D18: Startup load-plan existence, hashes, and containment
        load_plan_ok = True
        try:
            import wsr_reload
            checked_adapter = adapter_name or "codex"
            startup_plan = wsr_reload.build_load_plan(package_root, manifest, checked_adapter, profile="startup")
            valid_roles = {"policy", "config", "adapter", "workflow", "skill", "reference", "document", "rule", "script", "schema", "state", "template", "evidence", "test"}
            if not startup_plan:
                raise ValueError("Startup load plan is empty")
            for entry in startup_plan:
                entry_path = entry.get("absolutePath")
                if not entry_path or not os.path.isfile(entry_path):
                    raise ValueError(f"Load-plan entry missing: {entry_path}")
                if os.path.commonpath([os.path.realpath(package_root), os.path.realpath(entry_path)]) != os.path.realpath(package_root):
                    raise ValueError(f"Load-plan entry escapes source root: {entry_path}")
                if entry.get("role") not in valid_roles or not entry.get("sha256"):
                    raise ValueError(f"Load-plan entry metadata invalid: {entry_path}")
        except Exception as e:
            load_plan_ok = False
            results["blockers"].append(f"D18 Failed: {e}")
        if load_plan_ok:
            gates_passed += 1

        # D25: Skill capability uniqueness and content-hash binding
        skill_uniq_ok = True
        ctx_file_path = os.path.join(package_root, manifest.get("contextFile", "WSR_CONTEXT.json"))
        if os.path.exists(ctx_file_path):
            try:
                with open(ctx_file_path, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                seen_caps = {}
                for sk in cdata.get("skillIndex", []):
                    cap = sk.get("capabilityId")
                    spath = sk.get("path")
                    if cap in seen_caps and seen_caps[cap] != spath:
                        skill_uniq_ok = False
                        results["blockers"].append(f"D25 Failed: Skill capability collision for '{cap}': {seen_caps[cap]} vs {spath}")
                    seen_caps[cap] = spath
                    skill_path = os.path.join(package_root, spath)
                    if not os.path.exists(skill_path) or sk.get("contentHash") != wsr_common.calculate_sha256(skill_path):
                        skill_uniq_ok = False
                        results["blockers"].append(f"D25 Failed: Skill contentHash mismatch for '{cap}'")
            except Exception as e:
                skill_uniq_ok = False
                results["blockers"].append(f"D25 Failed: Skill uniqueness parse error: {e}")
        if skill_uniq_ok:
            gates_passed += 1

        # D27: Startup memory exclusion verification
        memory_excl_ok = True
        ctx_file_path = os.path.join(package_root, manifest.get("contextFile", "WSR_CONTEXT.json"))
        if os.path.exists(ctx_file_path):
            try:
                with open(ctx_file_path, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                startup_policies = cdata.get("policyFiles", [])
                if any("project_checkpoint" in p or "memory/" in p for p in startup_policies):
                    memory_excl_ok = False
                    results["blockers"].append("D27 Failed: Memory checkpoint leaked into startup core policies")
            except Exception as e:
                memory_excl_ok = False
                results["blockers"].append(f"D27 Failed: Memory exclusion check error: {e}")
        if memory_excl_ok:
            gates_passed += 1

        # D28: Startup token budget computed from the real load plan
        budget_ok = True
        total_chars = 0
        try:
            import wsr_reload
            budget_plan = wsr_reload.build_load_plan(package_root, manifest, adapter_name or "codex", profile="startup")
            for entry in budget_plan:
                with open(entry["absolutePath"], "r", encoding="utf-8", errors="ignore") as f:
                    total_chars += len(f.read())
            with open(context_path, "r", encoding="utf-8") as f:
                budget_context = json.load(f)
        except Exception as e:
            budget_ok = False
            results["blockers"].append(f"D28 Failed: Cannot build startup load plan: {e}")
        est_tokens = int(total_chars / 4)
        startup_max = budget_context.get("tokenBudget", {}).get("startupMax", 12000) if "budget_context" in locals() else 12000
        if est_tokens > startup_max:
            budget_ok = False
            results["blockers"].append(f"D28 Failed: Startup token budget exceeded: estimated {est_tokens} tokens > {startup_max} max")
        if budget_ok:
            gates_passed += 1

        # D29: Router template and rendered identity binding
        router_ok = True
        try:
            import sync_config
            router_text = sync_config.render_router(package_root, manifest)
            manifest_hash = wsr_common.calculate_sha256(os.path.join(package_root, "WSR_MANIFEST.json"))
            normalized_root = os.path.realpath(package_root).replace('\\', '/')
            if normalized_root not in router_text or manifest_hash not in router_text or manifest.get("buildId", "") not in router_text:
                raise ValueError("Rendered router is not bound to absolute source identity")
        except Exception as e:
            router_ok = False
            results["blockers"].append(f"D29 Failed: {e}")
        if router_ok:
            gates_passed += 1

        # D19: Manifest/context command registry is one-to-one and executable
        command_registry_ok = True
        try:
            with open(context_path, "r", encoding="utf-8") as f:
                command_context = json.load(f)
            manifest_commands = manifest.get("commands", {})
            context_commands = command_context.get("commandMap", {})
            if set(manifest_commands) != set(context_commands):
                raise ValueError("Manifest and context command names differ")
            for command_name, command in context_commands.items():
                workflow = command.get("workflow")
                if not workflow or not os.path.isfile(os.path.join(package_root, workflow)):
                    raise ValueError(f"Command '{command_name}' has no valid workflow")
        except Exception as e:
            command_registry_ok = False
            results["blockers"].append(f"D19 Failed: {e}")
        if command_registry_ok:
            gates_passed += 1

        # D20: Every declared adapter satisfies only the v2 contract
        adapter_schema_ok = True
        for adapter_rel in manifest.get("adapters", []):
            valid_adapter, adapter_error = check_adapter_file(os.path.join(package_root, adapter_rel))
            if not valid_adapter:
                adapter_schema_ok = False
                results["blockers"].append(f"D20 Failed: {adapter_rel}: {adapter_error}")
        if adapter_schema_ok:
            gates_passed += 1

        # D21: Runtime family and all logical roots resolve inside target boundaries
        logical_roots_ok = True
        try:
            import sync_config
            families = set()
            for adapter_rel in manifest.get("adapters", []):
                with open(os.path.join(package_root, adapter_rel), "r", encoding="utf-8") as f:
                    adapter_data = json.load(f)
                family = adapter_data.get("runtimeFamily")
                if not family or family in families:
                    raise ValueError(f"Duplicate or empty runtimeFamily: {family}")
                families.add(family)
                probe_root = os.path.join(package_root, ".doctor-logical-root", adapter_data["adapterId"])
                resolved_roots = sync_config.resolve_logical_roots(probe_root, adapter_data)
                if set(resolved_roots) != set(adapter_data["logicalRoots"]):
                    raise ValueError(f"Logical roots unresolved for {adapter_data['adapterId']}")
            invalid_source = os.path.join(package_root, "__missing_source__")
            failed_closed = False
            try:
                wsr_common.resolve_source_root(explicit_source_root=invalid_source)
            except (FileNotFoundError, ValueError):
                failed_closed = True
            if not failed_closed:
                raise ValueError("Invalid explicit source silently fell back")
            unresolved_target, origin = wsr_common.resolve_target_root()
            if unresolved_target is not None or origin != "unresolved":
                raise ValueError("Target resolver silently fell back")
        except Exception as e:
            logical_roots_ok = False
            results["blockers"].append(f"D21 Failed: {e}")
        if logical_roots_ok:
            gates_passed += 1

        # D24: A build identity may bind to exactly one manifest content hash
        identity_ok = True
        try:
            ledger_path = os.path.join(package_root, "release_identity_ledger.json")
            with open(ledger_path, "r", encoding="utf-8") as f:
                ledger = json.load(f)
            seen_builds = {}
            for entry in ledger.get("entries", []):
                build = entry.get("buildId")
                content_hash = entry.get("contentHash")
                if not build or not content_hash:
                    raise ValueError(f"Ledger entry lacks buildId/contentHash: {entry}")
                if build in seen_builds and seen_builds[build] != content_hash:
                    raise ValueError(f"Reused buildId with different contentHash: {build}")
                seen_builds[build] = content_hash
            current_hash = wsr_common.calculate_package_content_hash(package_root, manifest)
            if seen_builds.get(manifest.get("buildId")) != current_hash:
                raise ValueError("Current buildId is not bound to the active package content hash")
        except Exception as e:
            identity_ok = False
            results["blockers"].append(f"D24 Failed: {e}")
        if identity_ok:
            gates_passed += 1

        # D26: Capability paths cannot collide across roots
        capability_roots_ok = True
        try:
            with open(context_path, "r", encoding="utf-8") as f:
                capability_context = json.load(f)
            path_owners = {}
            for skill in capability_context.get("skillIndex", []):
                normalized_path = os.path.normcase(os.path.realpath(os.path.join(package_root, skill.get("path", ""))))
                owner = skill.get("capabilityId")
                if normalized_path in path_owners and path_owners[normalized_path] != owner:
                    raise ValueError(f"Capability path collision: {path_owners[normalized_path]} and {owner}")
                path_owners[normalized_path] = owner
        except Exception as e:
            capability_roots_ok = False
            results["blockers"].append(f"D26 Failed: {e}")
        if capability_roots_ok:
            gates_passed += 1

        # D30: Quick Audit must reject zero coverage
        zero_coverage_ok = True
        try:
            audit_path = os.path.join(package_root, "scripts", "wsr_audit.py")
            with open(audit_path, "r", encoding="utf-8") as f:
                audit_source = f.read()
            required_guards = ("zero_coverage_check", "EXIT_FAIL_FINDING")
            if not all(guard in audit_source for guard in required_guards):
                raise ValueError("Quick Audit has no explicit zero-coverage failure guard")
        except Exception as e:
            zero_coverage_ok = False
            results["blockers"].append(f"D30 Failed: {e}")
        if zero_coverage_ok:
            gates_passed += 1

        # D31-D32: Immutable transaction and adapter conformance evidence
        transaction_evidence_ok = True
        adapter_evidence_ok = True
        try:
            evidence_index_path = os.path.join(package_root, "evidence", "cross-ide-conformance", "index.json")
            with open(evidence_index_path, "r", encoding="utf-8") as f:
                evidence_index = json.load(f)
            run_rel = evidence_index.get("activeRun", "")
            run_path = wsr_common.safe_resolve_path(package_root, run_rel)
            with open(run_path, "r", encoding="utf-8") as f:
                evidence = json.load(f)
            if evidence.get("buildId") != manifest.get("buildId") or not evidence.get("immutable"):
                raise ValueError("Evidence identity or immutable flag is invalid")
            transaction = evidence.get("transaction", {})
            required_transaction_proofs = {"apply", "markerSchema", "rollback", "sentinelPreserved"}
            if set(transaction) != required_transaction_proofs or any(value != "PASS" for value in transaction.values()):
                transaction_evidence_ok = False
                results["blockers"].append("D31 Failed: Transaction evidence is incomplete")
            adapter_results = evidence.get("adapters", {})
            enabled_adapters = set()
            for adapter_rel in manifest.get("adapters", []):
                with open(os.path.join(package_root, adapter_rel), "r", encoding="utf-8") as f:
                    adapter_data = json.load(f)
                if adapter_data.get("enabled"):
                    enabled_adapters.add(adapter_data["adapterId"])
            if set(adapter_results) != enabled_adapters or any(value != "PASS" for value in adapter_results.values()):
                adapter_evidence_ok = False
                results["blockers"].append("D32 Failed: Enabled adapter conformance evidence is incomplete")
            fixture_results = evidence.get("negativeFixtures", {})
            expected_gates = {f"D{number}" for number in range(17, 33)}
            if set(fixture_results) != expected_gates or any(value != "PASS" for value in fixture_results.values()):
                adapter_evidence_ok = False
                results["blockers"].append("D32 Failed: D17-D32 negative fixture evidence is incomplete")
            fixtures_path = os.path.join(package_root, "tests", "conformance", "fixtures.json")
            with open(fixtures_path, "r", encoding="utf-8") as f:
                fixtures = json.load(f)
            fixture_contracts = fixtures.get("gates", {})
            if set(fixture_contracts) != expected_gates:
                raise ValueError("D17-D32 fixture contracts are incomplete")
            for gate_name, fixture in fixture_contracts.items():
                if not fixture.get("positiveFixture") or not fixture.get("negativeFixture") or not isinstance(fixture.get("expectedExit"), int):
                    raise ValueError(f"Fixture contract invalid for {gate_name}")
        except Exception as e:
            transaction_evidence_ok = False
            adapter_evidence_ok = False
            results["blockers"].append(f"D31 Failed: {e}")
            results["blockers"].append(f"D32 Failed: {e}")
        if transaction_evidence_ok:
            gates_passed += 1
        if adapter_evidence_ok:
            gates_passed += 1

        if checksums_verification_ok:
            gates_passed += 1
            
    # Calculate Score
    results["score"] = int((gates_passed / gates_total) * 100)
    
    is_failed = len(results["blockers"]) > 0
    if strict and len(results["warnings"]) > 0:
        is_failed = True
        results["blockers"].append("Strict mode: warnings treated as blockers")
        
    results["status"] = "FAIL" if is_failed else "PASS"
    return results, gates_passed, gates_total

def main():
    import argparse
    parser = argparse.ArgumentParser(description="WSR Doctor Utility v3")
    parser.add_argument("--path", help="Path to package root")
    parser.add_argument("--adapter", help="Check specific adapter configuration")
    parser.add_argument("--target-root", help="Check specific target root resolution")
    parser.add_argument("--json", action="store_true", help="Output machine readable JSON")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--source-mode", action="store_true", help="Validate the source package without a runtime marker")
    mode_group.add_argument("--runtime-mode", action="store_true", help="Validate a deployed runtime and require its marker")
    
    args = parser.parse_args()
    is_json = args.json
    strict = args.strict
    
    package_root = args.path if args.path else wsr_common.get_package_root()
    package_root = os.path.abspath(package_root)
    
    results, gates_passed, gates_total = run_doctor_checks(
        package_root,
        strict=strict,
        is_json=is_json,
        adapter_name=args.adapter,
        target_root=os.path.realpath(os.path.abspath(args.target_root)) if args.target_root else None,
        runtime_mode=args.runtime_mode,
    )
    
    if is_json:
        wsr_common.print_json_report(results)
    else:
        print("="*60)
        print("WSR DOCTOR REPORT")
        print("="*60)
        print(f"Package: {results['packageName']} (v{results['version']})")
        print(f"Build ID: {results['buildId']}")
        print(f"Status:  {results['status']}")
        print(f"Score:   {results['score']}% ({gates_passed}/{gates_total} gates passed)")
        print("-"*60)
        if results["blockers"]:
            print("BLOCKERS (FAILED GATES):")
            for blocker in results["blockers"]:
                print(f" - {blocker}")
        if results["warnings"]:
            print("WARNINGS:")
            for warn in results["warnings"]:
                print(f" - {warn}")
        print("="*60)
        
    if results["status"] == "PASS":
        sys.exit(wsr_common.EXIT_SUCCESS)
    else:
        has_safety = any("escapes root" in b or "escaped root" in b or "containment" in b or "Symlinks" in b or "safety violation" in b or "escapes target root" in b for b in results["blockers"])
        sys.exit(wsr_common.EXIT_SAFETY_REJECTION if has_safety else wsr_common.EXIT_FAIL_FINDING)

if __name__ == "__main__":
    main()
