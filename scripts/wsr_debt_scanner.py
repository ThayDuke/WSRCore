import os
import sys
sys.dont_write_bytecode = True
import re
import argparse
import json
import subprocess
import wsr_common

DEFAULT_EXCLUDE = {'.git', '.venv', '__pycache__', 'Temp'}
# Keywords to search
KEYWORDS = ['wsr-debt:', 'dec-debt:', 'TODO:', 'FIXME:', 'HACK:']

def parse_debt_line(line, filepath, line_num, is_md):
    """
    Parse a line to detect technical debt tags.
    Returns a list of finding dicts or empty list.
    """
    findings = []
    
    # Simple regex to search for keywords
    # Matches comments or text with tag
    for kw in KEYWORDS:
        # Case sensitive matching for the keyword
        idx = line.find(kw)
        if idx != -1:
            tag = kw
            content = line[idx + len(kw):].strip()
            
            # Escape pipes and newlines for markdown table compatibility
            safe_content = content.replace('|', '\\|').replace('\n', ' ')
            
            # Severity mapping: FAIL for missing core schema, WARN for missing owner, INFO/WARN for others
            severity = "INFO"
            note = ""
            owner = "Unknown"
            ceiling = "N/A"
            upgrade = "N/A"
            status = "Open"
            
            # Check owner in content (e.g. @username or [username])
            owner_match = re.search(r'(?:@|\[)([a-zA-Z0-9_\-]+)(?:\])?', content)
            if owner_match:
                owner = owner_match.group(1)
            
            # Check migration warning for dec-debt
            if tag == 'dec-debt:':
                severity = "WARN"
                note = "Migration required: dec-debt tag is deprecated. Use wsr-debt."
                # Extract ceiling/upgrade if present
                c_match = re.search(r'ceiling:\s*([^;]+)', content, re.IGNORECASE)
                u_match = re.search(r'upgrade:\s*([^;]+)', content, re.IGNORECASE)
                if c_match: ceiling = c_match.group(1).strip()
                if u_match: upgrade = u_match.group(1).strip()
            elif tag == 'wsr-debt:':
                # Check ceiling and upgrade
                c_match = re.search(r'ceiling:\s*([^;]+)', content, re.IGNORECASE)
                u_match = re.search(r'upgrade:\s*([^;]+)', content, re.IGNORECASE)
                
                if c_match: ceiling = c_match.group(1).strip()
                if u_match: upgrade = u_match.group(1).strip()
                
                if not c_match or not u_match:
                    severity = "FAIL"
                    note = "Missing required ceiling or upgrade field."
                else:
                    severity = "INFO"
            else:
                # TODO, FIXME, HACK require an owner
                if owner == "Unknown":
                    severity = "WARN"
                    note = "Missing owner identifier (@owner or [owner])."
            
            findings.append({
                'file': filepath,
                'line': line_num,
                'tag': tag.rstrip(':'),
                'severity': severity,
                'owner': owner,
                'ceiling': ceiling.replace('|', '\\|'),
                'upgrade': upgrade.replace('|', '\\|'),
                'status': status,
                'content': safe_content,
                'note': note
            })
            
    return findings

def scan_file(filepath, project_root):
    rel_path = os.path.relpath(filepath, project_root).replace('\\', '/')
    findings = []
    is_md = filepath.endswith('.md')
    in_block = False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if is_md:
                    # Skip fenced code blocks
                    if line.strip().startswith('```'):
                        in_block = not in_block
                        continue
                    if in_block:
                        continue
                    # Skip inline code spans by stripping backticks
                    line = re.sub(r'`[^`]+`', ' ', line)
                    
                # Skip schema examples or definitions to avoid false positives
                if 'wsr-debt: [mô tả' in line or 'dec-debt: [lý do' in line or 'KEYWORDS' in line:
                    continue
                    
                line_findings = parse_debt_line(line, rel_path, line_num, is_md)
                findings.extend(line_findings)
    except Exception as e:
        findings.append({
            'file': rel_path,
            'line': 0,
            'tag': 'ERROR',
            'severity': 'FAIL',
            'owner': 'System',
            'ceiling': 'N/A',
            'upgrade': 'N/A',
            'status': 'Error',
            'content': f"Failed to read file: {e}",
            'note': f"Read error"
        })
    return findings

def get_git_changed_files(root_dir):
    try:
        res = subprocess.run(['git', 'status', '--porcelain'], cwd=root_dir, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"git status failed: {res.stderr}")
        files = []
        for line in res.stdout.splitlines():
            if len(line) > 3:
                # Format: XY path
                filepath = line[3:].strip()
                files.append(os.path.normpath(os.path.join(root_dir, filepath)))
        return files
    except Exception as e:
        raise RuntimeError(f"Failed to query git status: {e}")

def scan_project(root_dir, exclude_dirs, include_docs=False, include_planning=False, changed_only=False):
    findings = []
    
    if changed_only:
        try:
            changed_files = get_git_changed_files(root_dir)
        except Exception as e:
            # Propagate error as a finding
            findings.append({
                'file': 'git',
                'line': 0,
                'tag': 'ERROR',
                'severity': 'FAIL',
                'owner': 'System',
                'ceiling': 'N/A',
                'upgrade': 'N/A',
                'status': 'Error',
                'content': f"Git failure during scan: {e}",
                'note': "Git lookup failed"
            })
            return findings
            
        for filepath in changed_files:
            if not os.path.isfile(filepath):
                continue
            
            # Check exclusions
            rel_path = os.path.relpath(filepath, root_dir)
            parts = rel_path.split(os.sep)
            if any(part in exclude_dirs for part in parts):
                continue
                
            # Filter file types
            is_valid_type = filepath.endswith(('.py', '.js', '.html', '.css', '.bat', '.sh'))
            if include_docs and filepath.endswith('.md'):
                # Check planning doc rule
                if 'planning_' in os.path.basename(filepath).lower():
                    if include_planning:
                        is_valid_type = True
                else:
                    is_valid_type = True
                    
            if is_valid_type:
                if 'wsr_debt_scanner.py' in filepath or 'debt_ledger.md' in filepath:
                    continue
                findings.extend(scan_file(filepath, root_dir))
    else:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Prune directories in place
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
            
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if 'wsr_debt_scanner.py' in filepath or 'debt_ledger.md' in filepath:
                    continue
                    
                is_valid_type = filename.endswith(('.py', '.js', '.html', '.css', '.bat', '.sh'))
                if include_docs and filename.endswith('.md'):
                    if 'planning_' in filename.lower():
                        if include_planning:
                            is_valid_type = True
                    else:
                        is_valid_type = True
                        
                if is_valid_type:
                    findings.extend(scan_file(filepath, root_dir))
                    
    return findings

def generate_ledger_markdown(findings):
    lines = [
        "# Technical Debt Ledger\n",
        "> [!NOTE]",
        "> Generated automatically by `wsr_debt_scanner.py`.",
        "> Do not modify this file manually.\n",
        "| File | Line | Type | Severity | Owner | Ceiling | Upgrade | Status | Note |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    ]
    for item in findings:
        file_link = f"[{item['file']}](file:///{item['file']})"
        line = f"| {file_link} | {item['line']} | `{item['tag']}` | {item['severity']} | `{item['owner']}` | {item['ceiling']} | {item['upgrade']} | {item['status']} | {item['note']} |"
        lines.append(line)
        
    lines.append(f"\n---\nTotal tags detected: {len(findings)}")
    return "\n".join(lines) + "\n"

def main():
    parser = argparse.ArgumentParser(description="WSR Technical Debt Scanner")
    parser.add_argument('--root', type=str, default=None, help="Root folder to scan")
    parser.add_argument('--exclude', action='append', default=[], help="Exclude additional directory/file")
    parser.add_argument('--include-docs', action='store_true', help="Scan markdown documentation files")
    parser.add_argument('--include-planning', action='store_true', help="Scan planning md files inside DOCS/Planning")
    parser.add_argument('--changed', action='store_true', help="Only scan files modified in Git")
    parser.add_argument('--json', action='store_true', help="Output structured JSON results")
    parser.add_argument('--fail-on-warn', action='store_true', help="Exit with code 1 on any warning")
    
    # Mutually exclusive flags
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true', help="Dry-run audit check, no output file write")
    group.add_argument('--write', action='store_true', help="Write findings to ledger file")
    
    parser.add_argument('--output', type=str, default=None, help="Ledger output path (defaults to debt_ledger.md in root)")
    
    args = parser.parse_args()
    
    # If both are missing or neither is specified, default to check
    action_check = args.check or (not args.write)
    
    if args.root:
        project_root = os.path.abspath(args.root)
    else:
        project_root = wsr_common.get_package_root()
        
    exclude_dirs = set(DEFAULT_EXCLUDE)
    for exc in args.exclude:
        exclude_dirs.add(exc)
        
    findings = scan_project(
        project_root, 
        exclude_dirs, 
        include_docs=args.include_docs, 
        include_planning=args.include_planning, 
        changed_only=args.changed
    )
    
    # Check severity counts
    fail_count = len([f for f in findings if f['severity'] == "FAIL"])
    warn_count = len([f for f in findings if f['severity'] == "WARN"])
    
    if args.json:
        wsr_common.print_json_report(findings)
    else:
        print(f"Scanning for technical debt in {project_root}...")
        print(f"Findings: {len(findings)} | FAIL: {fail_count} | WARN: {warn_count}")
        for item in findings:
            prefix = f"[{item['severity']}]"
            print(f"{prefix} {item['file']}:{item['line']} | {item['tag']} - {item['content']} (Owner: {item['owner']})")
            if item['note']:
                print(f"   Note: {item['note']}")
                
    if args.write and not action_check:
        output_path = args.output if args.output else os.path.join(project_root, 'debt_ledger.md')
        # Validate output containment
        try:
            resolved_output = wsr_common.safe_resolve_path(project_root, os.path.relpath(output_path, project_root))
            markdown_content = generate_ledger_markdown(findings)
            wsr_common.atomic_write_text(resolved_output, markdown_content)
            if not args.json:
                print(f"Ledger file written successfully to {resolved_output}")
        except Exception as e:
            print(f"Failed to write ledger file: {e}", file=sys.stderr)
            sys.exit(wsr_common.EXIT_IO_TRANSACTION_ERROR)
            
    # Exit code determination
    if fail_count > 0:
        sys.exit(wsr_common.EXIT_FAIL_FINDING)
    if args.fail_on_warn and warn_count > 0:
        sys.exit(wsr_common.EXIT_FAIL_FINDING)
        
    sys.exit(wsr_common.EXIT_SUCCESS)

if __name__ == '__main__':
    main()
