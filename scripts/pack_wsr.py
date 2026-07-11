import os
import sys
sys.dont_write_bytecode = True
import zipfile
import json
import wsr_common
import wsr_doctor

def run_doctor_preflight(package_root):
    """Run JIT doctor checks directly to verify package state before packaging."""
    try:
        results, gates_passed, gates_total = wsr_doctor.run_doctor_checks(package_root, strict=False, is_json=True)
        if results["status"] != "PASS":
            return False, f"Doctor checks failed: {results['blockers']}"
        return True, ""
    except Exception as e:
        return False, f"Doctor check exception: {e}"

def generate_checksums_file(package_root, manifest):
    """Calculate SHA-256 for all artifacts except WSR_CHECKSUMS.json and write it."""
    checksums = {}
    for art in manifest.get("artifacts", []):
        if art["id"] == "wsr-checksums":
            continue
            
        src_path = os.path.join(package_root, art["source"])
        if os.path.exists(src_path):
            checksums[art["source"]] = wsr_common.calculate_sha256(src_path)
            
    # Write atomic
    checksums_file = manifest.get("checksumsFile", "WSR_CHECKSUMS.json")
    resolved_path = os.path.join(package_root, checksums_file)
    
    content = json.dumps(checksums, indent=2, sort_keys=True, ensure_ascii=False)
    wsr_common.atomic_write_text(resolved_path, content)
    return checksums

def verify_zip_archive(zip_filepath, manifest, checksums):
    """Open built ZIP in read-only mode and verify entries and checksums."""
    with zipfile.ZipFile(zip_filepath, 'r') as zipf:
        zip_namelist = zipf.namelist()
        
        # Build normalized POSIX names list
        manifest_sources = [a["source"].replace('\\', '/') for a in manifest.get("artifacts", [])]
        
        # Verify inventory completeness
        for ms in manifest_sources:
            if ms not in zip_namelist:
                raise RuntimeError(f"ZIP Verification Error: Artifact '{ms}' missing from built ZIP archive")
                
        for zn in zip_namelist:
            if zn not in manifest_sources:
                raise RuntimeError(f"ZIP Verification Error: File '{zn}' in ZIP is not registered in manifest inventory")
                
            # Verify checksum (except generated files)
            checksums_file = manifest.get("checksumsFile", "WSR_CHECKSUMS.json")
            if zn == checksums_file:
                continue
                
            with zipf.open(zn) as zf:
                data = zf.read()
                
            import hashlib
            hasher = hashlib.sha256()
            hasher.update(data)
            zip_hash = hasher.hexdigest()
            
            expected_hash = checksums.get(zn)
            if zip_hash != expected_hash:
                raise RuntimeError(f"ZIP Verification Error: Checksum mismatch for '{zn}'. Expected: {expected_hash}, Got: {zip_hash}")

def main():
    package_root = wsr_common.get_package_root()
    
    # 1. Load manifest
    try:
        manifest = wsr_common.load_manifest(package_root)
    except Exception as e:
        print(f"[-] Error: Failed to load manifest: {e}", file=sys.stderr)
        sys.exit(wsr_common.EXIT_INVALID_ARGS)
        
    packageName = manifest.get("packageName", "WSR_Package")
    version = manifest.get("version", "1.0.0")
    buildId = manifest.get("buildId", "N_A")
    
    # 2. Generate checksums FIRST to let doctor validate successfully
    print("[*] Generating new WSR_CHECKSUMS.json...")
    try:
        checksums = generate_checksums_file(package_root, manifest)
    except Exception as e:
        print(f"[-] Error: Failed to generate checksums file: {e}", file=sys.stderr)
        sys.exit(wsr_common.EXIT_IO_TRANSACTION_ERROR)
        
    # 3. Run preflight doctor check AFTER checksums updated
    print("[*] Running preflight doctor checks...")
    doctor_ok, doctor_err = run_doctor_preflight(package_root)
    if not doctor_ok:
        print("[-] Preflight Safety Gate: Doctor check failed. Packaging aborted!", file=sys.stderr)
        print(doctor_err, file=sys.stderr)
        sys.exit(wsr_common.EXIT_FAIL_FINDING)
        
    # 4. Perform deterministic zip package build
    output_dir = os.path.dirname(package_root)
    zip_filename = f"{packageName}_v{version}_{buildId}.zip"
    zip_filepath = os.path.join(output_dir, zip_filename)
    
    print(f"[*] Packaging {packageName} (v{version}) with Build ID: {buildId}...")
    print(f"[*] Output ZIP path: {zip_filepath}")
    
    # Get sorted manifest artifacts to achieve deterministic ordering
    sorted_artifacts = sorted(manifest.get("artifacts", []), key=lambda x: x["source"].replace('\\', '/'))
    
    try:
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for art in sorted_artifacts:
                rel_path = art["source"].replace('\\', '/')
                abs_path = os.path.join(package_root, rel_path)
                
                # Check file existence
                if not os.path.exists(abs_path):
                    if art.get("required", False):
                        raise FileNotFoundError(f"Required artifact not found: {rel_path}")
                    continue
                    
                # Read content for deterministic compression
                with open(abs_path, 'rb') as f:
                    content = f.read()
                    
                # Setup deterministic metadata
                zinfo = zipfile.ZipInfo(filename=rel_path)
                zinfo.date_time = (2026, 7, 11, 23, 0, 0) # Fixed timestamp
                zinfo.compress_type = zipfile.ZIP_DEFLATED
                # Unix permissions: 0o644 -> rw-r--r--
                zinfo.external_attr = 0o644 << 16
                
                zipf.writestr(zinfo, content)
                
        # 5. Post-build verification
        verify_zip_archive(zip_filepath, manifest, checksums)
        
        print("="*60)
        print("WSR PACKAGING SUCCESSFUL")
        print("="*60)
        print(f"Package:     {packageName} (v{version})")
        print(f"Build ID:    {buildId}")
        print(f"Source:      {package_root}")
        print(f"ZIP Archive: {zip_filepath}")
        print(f"Total files: {len(sorted_artifacts)}")
        print("="*60)
        
    except Exception as e:
        print(f"[-] Packaging failed during ZIP creation or verification: {e}", file=sys.stderr)
        if os.path.exists(zip_filepath):
            try:
                os.remove(zip_filepath)
            except:
                pass
        sys.exit(wsr_common.EXIT_IO_TRANSACTION_ERROR)
        
    sys.exit(wsr_common.EXIT_SUCCESS)

if __name__ == '__main__':
    main()
