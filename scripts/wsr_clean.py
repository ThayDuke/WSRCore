import os
import argparse
import sys
sys.dont_write_bytecode = True
import json
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

def main():
    parser = argparse.ArgumentParser(description="WSR Clean Hardening Utility")
    parser.add_argument('--root', type=str, default=None, help="Project root to clean")
    parser.add_argument('--json', action='store_true', help="Output report in JSON format")
    
    # Mutually exclusive flags
    parser.add_argument('--apply', action='store_true', help="Execute deletion of junk files")
    parser.add_argument('--delete', action='store_true', help="Deprecated alias for --apply")
    
    parser.add_argument('--approval-token', type=str, default=None, help="Approval token matching manifest buildId")
    
    args = parser.parse_args()
    
    is_apply = args.apply or args.delete
    is_json = args.json
    
    if args.root:
        project_root = os.path.abspath(args.root)
    else:
        project_root = wsr_common.get_package_root()
        
    try:
        manifest = wsr_common.load_manifest(project_root)
    except Exception as e:
        if is_json:
            wsr_common.print_json_report({"status": "FAIL", "message": f"Failed to load manifest: {e}"})
        else:
            print(f"[-] Error: Failed to load manifest: {e}", file=sys.stderr)
        sys.exit(wsr_common.EXIT_INVALID_ARGS)
        
    build_id = manifest.get("buildId")
    
    # Scan for candidates
    candidates = scan_junk_files(project_root, manifest)
    total_size = sum(c["size"] for c in candidates)
    
    report = {
        "status": "SCAN",
        "total_files": len(candidates),
        "total_bytes": total_size,
        "protected_roots": manifest.get("cleanWhitelist", []),
        "candidates": candidates,
        "deletions": []
    }
    
    # Warning for deprecated --delete flag
    if args.delete and not is_json:
        print("[!] WARNING: --delete is a deprecated alias. Use --apply instead.", file=sys.stderr)
        
    if is_apply:
        # Approval Token Validation
        if not args.approval_token or args.approval_token != build_id:
            report["status"] = "REJECTED"
            report["message"] = "Invalid or missing --approval-token"
            if is_json:
                wsr_common.print_json_report(report)
            else:
                print(f"[-] Safety Gate: Rejection! Token '{args.approval_token}' does not match buildId '{build_id}'", file=sys.stderr)
            sys.exit(wsr_common.EXIT_SAFETY_REJECTION)
            
        # Execute deletions
        report["status"] = "SUCCESS"
        deleted_count = 0
        for cand in candidates:
            # Revalidate file before removing
            abs_path = cand["absolute_path"]
            rel_path = cand["relative_path"]
            
            # Double check containment
            try:
                wsr_common.safe_resolve_path(project_root, rel_path)
            except ValueError as e:
                report["deletions"].append({"file": rel_path, "status": "FAILED", "error": f"Path containment violation: {e}"})
                report["status"] = "PARTIAL_FAIL"
                continue
                
            if os.path.exists(abs_path):
                try:
                    # Double check metadata size hasn't drifted wildly or if file was replaced
                    current_size = os.path.getsize(abs_path)
                    if abs(current_size - cand["size"]) > 1024 * 1024: # 1MB drift safety limit
                        raise RuntimeError("File size drifted significantly since scan.")
                        
                    os.remove(abs_path)
                    deleted_count += 1
                    report["deletions"].append({"file": rel_path, "status": "DELETED"})
                except Exception as e:
                    report["deletions"].append({"file": rel_path, "status": "FAILED", "error": str(e)})
                    report["status"] = "PARTIAL_FAIL"
            else:
                report["deletions"].append({"file": rel_path, "status": "ALREADY_GONE"})
                
        if is_json:
            wsr_common.print_json_report(report)
        else:
            if report["status"] == "PARTIAL_FAIL":
                print(f"[-] Clean completed with partial failures. Log: {report['deletions']}", file=sys.stderr)
            else:
                print(f"[+] Successfully deleted {deleted_count} junk files.")
                
        if report["status"] == "PARTIAL_FAIL":
            sys.exit(wsr_common.EXIT_IO_TRANSACTION_ERROR)
    else:
        # Scan-only mode
        if is_json:
            wsr_common.print_json_report(report)
        else:
            print("="*60)
            print("WSR CLEAN SCAN REPORT (READ-ONLY)")
            print("="*60)
            print(f"Project Root: {project_root}")
            print(f"Protected Whitelist: {manifest.get('cleanWhitelist')}")
            print("-"*60)
            if not candidates:
                print("No junk files found. Project is clean!")
            else:
                print(f"Found {len(candidates)} junk files (Total {total_size} bytes):")
                for cand in candidates:
                    print(f" - {cand['relative_path']} ({cand['size']} bytes) - Reason: {cand['reason']}")
            print("="*60)
            print("To execute deletions, run with --apply --approval-token <buildId>")
            print("="*60)
            
    sys.exit(wsr_common.EXIT_SUCCESS)

if __name__ == '__main__':
    main()
