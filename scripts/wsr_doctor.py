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
        
    required_fields = [
        "adapterId", "displayName", "enabled", "targetRootEnvironmentVariable",
        "requiresExplicitTargetRoot", "skillLoadingMode", "artifactMappings",
        "unsupportedFeatures", "pathStyle"
    ]
    for field in required_fields:
        if field not in data:
            return False, f"Adapter {adapter_path} missing field: {field}"
    return True, ""

def main():
    import argparse
    parser = argparse.ArgumentParser(description="WSR Doctor Utility v3")
    parser.add_argument("--path", help="Path to package root")
    parser.add_argument("--adapter", help="Check specific adapter configuration")
    parser.add_argument("--target-root", help="Check specific target root resolution")
    parser.add_argument("--json", action="store_true", help="Output machine readable JSON")
def run_doctor_checks(package_root, strict=False, is_json=False):
    """Run all 16 integrity and configuration validation checks and return results."""
    results = {
        "packageName": None,
        "version": None,
        "buildId": None,
        "status": "FAIL",
        "score": 0,
        "blockers": [],
        "warnings": []
    }
    
    gates_total = 16
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
                    for k, val in mappings.items():
                        # Test path containment
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
    
    args = parser.parse_args()
    is_json = args.json
    strict = args.strict
    
    package_root = args.path if args.path else wsr_common.get_package_root()
    package_root = os.path.abspath(package_root)
    
    results, gates_passed, gates_total = run_doctor_checks(package_root, strict=strict, is_json=is_json)
    
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
