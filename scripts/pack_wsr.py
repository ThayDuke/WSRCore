import argparse
import os
import sys
sys.dont_write_bytecode = True
import zipfile
import json
import tempfile
import wsr_common
import wsr_doctor

STATUS_SUFFIXES = {
    "Released": "RELEASE",
    "Review": "REVIEW",
}


def parse_cli_args(argv=None):
    parser = argparse.ArgumentParser(description="Build a verified WSR-Core release archive")
    return parser.parse_args(argv)

def _artifact_source(artifact):
    """Return one canonical, package-relative artifact source."""
    source = artifact.get("source")
    if not isinstance(source, str) or not source:
        raise ValueError("Artifact source must be a non-empty string")
    normalized = source.replace('\\', '/')
    if normalized != source or any(part in {"", ".", ".."} for part in normalized.split('/')):
        raise ValueError(f"Artifact source is not canonical: {source}")
    if not wsr_common.validate_relative_path(normalized):
        raise ValueError(f"Artifact source escapes package root: {source}")
    return normalized

def run_doctor_preflight(package_root):
    """Run JIT doctor checks directly to verify package state before packaging."""
    try:
        results, gates_passed, gates_total = wsr_doctor.run_doctor_checks(
            package_root, strict=True, is_json=True, runtime_mode=False
        )
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

        source = _artifact_source(art)
        src_path = wsr_common.safe_resolve_path(package_root, source)
        if os.path.exists(src_path):
            checksums[source] = wsr_common.calculate_sha256(src_path)
            
    # Write atomic
    checksums_file = manifest.get("checksumsFile", "WSR_CHECKSUMS.json")
    resolved_path = wsr_common.safe_resolve_path(package_root, checksums_file)
    
    content = json.dumps(checksums, indent=2, sort_keys=True, ensure_ascii=False)
    wsr_common.atomic_write_text(resolved_path, content)
    return checksums

def validate_identity_ledger(package_root, manifest):
    """Reject missing or reused build identities before package mutation."""
    ledger_path = wsr_common.safe_resolve_path(package_root, "release_identity_ledger.json")
    with open(ledger_path, "r", encoding="utf-8") as stream:
        ledger = json.load(stream)
    package_content_hash = wsr_common.calculate_package_content_hash(package_root, manifest)
    bindings = {}
    for entry in ledger.get("entries", []):
        build_id = entry.get("buildId")
        content_hash = entry.get("contentHash")
        if not build_id or not content_hash:
            raise ValueError("Every identity-ledger entry requires buildId and contentHash")
        if build_id in bindings and bindings[build_id] != content_hash:
            raise ValueError(f"Build identity reused with different content: {build_id}")
        bindings[build_id] = content_hash
    if bindings.get(manifest.get("buildId")) != package_content_hash:
        raise ValueError("Current build identity is not bound to the active package content hash")


def validate_manual_uat(package_root, manifest):
    """Require explicit native UAT evidence before packaging a released build."""
    if manifest.get("status") != "Released":
        return
    index_path = wsr_common.safe_resolve_path(
        package_root, "evidence/cross-ide-conformance/index.json",
    )
    with open(index_path, "r", encoding="utf-8") as stream:
        index = json.load(stream)
    active_relative = index.get("activeRun")
    if not isinstance(active_relative, str) or not active_relative:
        raise ValueError("Manual UAT gate requires an active evidence run")
    evidence_path = wsr_common.safe_resolve_path(package_root, active_relative)
    with open(evidence_path, "r", encoding="utf-8") as stream:
        evidence = json.load(stream)
    uat = evidence.get("manualUat", {})
    if evidence.get("buildId") != manifest.get("buildId"):
        raise ValueError("Released packaging requires matching Manual UAT evidence")
    valid, detail = wsr_common.validate_manual_uat_record(uat)
    if not valid:
        raise ValueError(detail)

def verify_zip_archive(zip_filepath, manifest, checksums):
    """Open built ZIP in read-only mode and verify entries and checksums."""
    with zipfile.ZipFile(zip_filepath, 'r') as zipf:
        zip_namelist = zipf.namelist()
        
        # Build normalized POSIX names list
        manifest_sources = [_artifact_source(a) for a in manifest.get("artifacts", [])]
        
        # Verify inventory completeness
        for ms in manifest_sources:
            if ms not in zip_namelist:
                raise RuntimeError(f"ZIP Verification Error: Artifact '{ms}' missing from built ZIP archive")
                
        checksums_file = manifest.get("checksumsFile", "WSR_CHECKSUMS.json")
        for zn in zip_namelist:
            if zn not in manifest_sources:
                raise RuntimeError(f"ZIP Verification Error: File '{zn}' in ZIP is not registered in manifest inventory")
                
            # Verify checksum (except generated files)
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

def main(argv=None):
    parse_cli_args(argv)
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
    status = manifest.get("status")
    status_suffix = STATUS_SUFFIXES.get(status)
    if not status_suffix:
        print(f"[-] Unsupported package status: {status}", file=sys.stderr)
        sys.exit(wsr_common.EXIT_INVALID_ARGS)

    try:
        validate_identity_ledger(package_root, manifest)
        validate_manual_uat(package_root, manifest)
    except Exception as e:
        print(f"[-] Identity ledger safety gate failed: {e}", file=sys.stderr)
        sys.exit(wsr_common.EXIT_SAFETY_REJECTION)
    
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
    repo_root = package_root
    while not os.path.isdir(os.path.join(repo_root, "DOCS")):
        parent = os.path.dirname(repo_root)
        if parent == repo_root:
            raise RuntimeError("Repository DOCS directory not found")
        repo_root = parent
    output_dir = os.path.join(repo_root, "DOCS")
    zip_filename = f"{packageName}_{version}-{status_suffix}.zip"
    zip_filepath = wsr_common.safe_resolve_path(output_dir, zip_filename)
    # Never overwrite a prior archive in place; replace is atomic and only happens
    # after the temporary archive has passed inventory and checksum verification.
    
    print(f"[*] Packaging {packageName} (v{version}) with Build ID: {buildId}...")
    print(f"[*] Output ZIP path: {zip_filepath}")
    
    # Get sorted manifest artifacts to achieve deterministic ordering
    sorted_artifacts = sorted(manifest.get("artifacts", []), key=lambda x: x["source"].replace('\\', '/'))
    
    temp_zip_path = None
    try:
        temp_fd, temp_zip_path = tempfile.mkstemp(
            prefix=f".{zip_filename}.", suffix=".tmp", dir=output_dir,
        )
        os.close(temp_fd)
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for art in sorted_artifacts:
                rel_path = _artifact_source(art)
                abs_path = wsr_common.safe_resolve_path(package_root, rel_path)
                
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
        verify_zip_archive(temp_zip_path, manifest, checksums)
        os.replace(temp_zip_path, zip_filepath)
        temp_zip_path = None
        
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
        if temp_zip_path and os.path.exists(temp_zip_path):
            try:
                os.remove(temp_zip_path)
            except:
                pass
        sys.exit(wsr_common.EXIT_IO_TRANSACTION_ERROR)
        
    sys.exit(wsr_common.EXIT_SUCCESS)

if __name__ == '__main__':
    main()
