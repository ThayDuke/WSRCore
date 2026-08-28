import os
import argparse
import sys
sys.dont_write_bytecode = True
import wsr_common

JUNK_FILENAMES = {'.ds_store', 'thumbs.db', 'desktop.ini'}
JUNK_EXTENSIONS = {'.bak', '.tmp', '.temp'}

def is_whitelisted(rel_path, whitelist_patterns):
    """
    Check if a relative path matches any whitelist pattern using path segment matching.
    Avoids false positives like matching 'DATAbase' with 'DATA'.
    """
    rel_path_norm = rel_path.replace('\\', '/').lower()
    rel_parts = rel_path_norm.split('/')
    
    for pat in whitelist_patterns:
        pat_clean = pat.replace('\\', '/').strip('/').lower()
        if not pat_clean:
            continue
        pat_parts = pat_clean.split('/')
        
        # Check if pat_parts is a prefix of rel_parts
        if len(rel_parts) >= len(pat_parts):
            if rel_parts[:len(pat_parts)] == pat_parts:
                return True
    return False

def scan_junk_files(project_root, manifest):
    """
    Scan project root for junk candidates according to strict policies.
    """
    junk_candidates = []
    exclusions = manifest.get("packageExclusions", [])
    whitelist = manifest.get("cleanWhitelist", [])
    
    # Get manifest registered artifacts to prevent deleting them
    registered_sources = {a["source"].replace('\\', '/').lower() for a in manifest.get("artifacts", [])}
    
    for root, dirs, files in os.walk(project_root, followlinks=False):
        # Resolve current relative path for directory pruning
        rel_dir = os.path.relpath(root, project_root).replace('\\', '/')
        if rel_dir == '.':
            rel_dir = ''
            
        # Prune protected/excluded directories in place
        dirs_to_prune = []
        for d in dirs:
            dir_rel_path = os.path.join(rel_dir, d).replace('\\', '/').lower()
            # Prune .git, .venv
            if d.lower() in {'.git', '.venv'}:
                dirs_to_prune.append(d)
            # Prune whitelisted directories to optimize walk
            elif is_whitelisted(dir_rel_path, whitelist):
                dirs_to_prune.append(d)
                
        for d in dirs_to_prune:
            if d in dirs:
                dirs.remove(d)
                
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, project_root).replace('\\', '/')
            rel_path_lower = rel_path.lower()
            
            # Policy Checks
            # 1. Do not delete whitelisted files
            if is_whitelisted(rel_path, whitelist):
                continue
                
            # 2. Do not delete registered manifest artifacts
            if rel_path_lower in registered_sources:
                continue
                
            # 3. Do not delete planning documents
            if 'planning_' in file.lower() and file.endswith('.md'):
                continue
                
            # 4. Check if it matches filename or extension junk rules
            file_lower = file.lower()
            _, ext = os.path.splitext(file_lower)
            
            reason = None
            if file_lower in JUNK_FILENAMES:
                reason = f"Filename matches junk list: {file}"
            elif ext in JUNK_EXTENSIONS:
                # Ensure it's not a temporary file from an ongoing atomic write transaction
                if not file_lower.endswith('.tmp'):
                    reason = f"Extension matches junk suffix: {ext}"
                else:
                    # Only treat as junk if it is not in the transaction directory or is stale
                    reason = f"Stale transaction file: {file}"
                    
            if reason:
                # Containment check before adding to candidates
                try:
                    resolved = wsr_common.safe_resolve_path(project_root, rel_path)
                    size = os.path.getsize(resolved)
                    junk_candidates.append({
                        "absolute_path": resolved,
                        "relative_path": rel_path,
                        "size": size,
                        "reason": reason
                    })
                except ValueError:
                    # Skip files escaping root
                    continue
                    
    return junk_candidates

def parse_args():
    parser = argparse.ArgumentParser(description="WSR Clean Hardening Utility")
    parser.add_argument('--root', type=str, default=None, help="Project root to clean")
    parser.add_argument('--json', action='store_true', help="Output report in JSON format")
    parser.add_argument('--apply', action='store_true', help="Execute deletion of junk files")
    parser.add_argument('--delete', action='store_true', help="Deprecated alias for --apply")
    parser.add_argument('--approval-token', type=str, default=None, help="Approval token matching manifest buildId")
    return parser.parse_args()


def load_manifest_or_exit(project_root, is_json):
    try:
        return wsr_common.load_manifest(project_root)
    except Exception as e:
        if is_json:
            wsr_common.print_json_report({"status": "FAIL", "message": f"Failed to load manifest: {e}"})
        else:
            print(f"[-] Error: Failed to load manifest: {e}", file=sys.stderr)
        sys.exit(wsr_common.EXIT_INVALID_ARGS)


def build_report(manifest, candidates):
    return {
        "status": "SCAN",
        "total_files": len(candidates),
        "total_bytes": sum(candidate["size"] for candidate in candidates),
        "protected_roots": manifest.get("cleanWhitelist", []),
        "candidates": candidates,
        "deletions": []
    }


def validate_approval_or_exit(args, build_id, report):
    if args.approval_token and args.approval_token == build_id:
        return
    report["status"] = "REJECTED"
    report["message"] = "Invalid or missing --approval-token"
    if args.json:
        wsr_common.print_json_report(report)
    else:
        print(
            f"[-] Safety Gate: Rejection! Token '{args.approval_token}' "
            f"does not match buildId '{build_id}'",
            file=sys.stderr,
        )
    sys.exit(wsr_common.EXIT_SAFETY_REJECTION)


def delete_candidates(project_root, candidates, report):
    report["status"] = "SUCCESS"
    deleted_count = 0
    for candidate in candidates:
        abs_path = candidate["absolute_path"]
        rel_path = candidate["relative_path"]
        try:
            wsr_common.safe_resolve_path(project_root, rel_path)
        except ValueError as error:
            report["deletions"].append({
                "file": rel_path,
                "status": "FAILED",
                "error": f"Path containment violation: {error}",
            })
            report["status"] = "PARTIAL_FAIL"
            continue
        if not os.path.exists(abs_path):
            report["deletions"].append({"file": rel_path, "status": "ALREADY_GONE"})
            continue
        try:
            current_size = os.path.getsize(abs_path)
            if abs(current_size - candidate["size"]) > 1024 * 1024:
                raise RuntimeError("File size drifted significantly since scan.")
            os.remove(abs_path)
            deleted_count += 1
            report["deletions"].append({"file": rel_path, "status": "DELETED"})
        except Exception as error:
            report["deletions"].append({"file": rel_path, "status": "FAILED", "error": str(error)})
            report["status"] = "PARTIAL_FAIL"
    return deleted_count


def emit_apply_report(report, is_json, deleted_count):
    if is_json:
        wsr_common.print_json_report(report)
    elif report["status"] == "PARTIAL_FAIL":
        print(f"[-] Clean completed with partial failures. Log: {report['deletions']}", file=sys.stderr)
    else:
        print(f"[+] Successfully deleted {deleted_count} junk files.")


def emit_scan_report(project_root, manifest, report, is_json):
    if is_json:
        wsr_common.print_json_report(report)
        return
    candidates = report["candidates"]
    print("="*60)
    print("WSR CLEAN SCAN REPORT (READ-ONLY)")
    print("="*60)
    print(f"Project Root: {project_root}")
    print(f"Protected Whitelist: {manifest.get('cleanWhitelist')}")
    print("-"*60)
    if not candidates:
        print("No junk files found. Project is clean!")
    else:
        print(f"Found {len(candidates)} junk files (Total {report['total_bytes']} bytes):")
        for candidate in candidates:
            print(
                f" - {candidate['relative_path']} ({candidate['size']} bytes) "
                f"- Reason: {candidate['reason']}"
            )
    print("="*60)
    print("To execute deletions, run with --apply --approval-token <buildId>")
    print("="*60)


def main():
    args = parse_args()
    is_apply = args.apply or args.delete
    project_root = os.path.abspath(args.root) if args.root else wsr_common.get_package_root()
    manifest = load_manifest_or_exit(project_root, args.json)
    candidates = scan_junk_files(project_root, manifest)
    report = build_report(manifest, candidates)

    if args.delete and not args.json:
        print("[!] WARNING: --delete is a deprecated alias. Use --apply instead.", file=sys.stderr)

    if not is_apply:
        emit_scan_report(project_root, manifest, report, args.json)
        sys.exit(wsr_common.EXIT_SUCCESS)

    build_id = manifest.get("buildId")
    validate_approval_or_exit(args, build_id, report)
    deleted_count = delete_candidates(project_root, candidates, report)
    report["receipt"] = {
        "schemaVersion": 1,
        "status": report["status"],
        "buildId": build_id,
        "scanned": len(candidates),
        "deleted": deleted_count,
    }
    emit_apply_report(report, args.json, deleted_count)
    if report["status"] == "PARTIAL_FAIL":
        sys.exit(wsr_common.EXIT_IO_TRANSACTION_ERROR)
    sys.exit(wsr_common.EXIT_SUCCESS)

if __name__ == '__main__':
    main()
