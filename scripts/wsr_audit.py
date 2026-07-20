import os
import sys
sys.dont_write_bytecode = True
import re
import argparse
import json
import ast
import subprocess
import wsr_common
import wsr_doctor

def check_utf8_and_mojibake(filepath):
    """Kiểm tra file có UTF-8 hợp lệ và không chứa ký tự U+FFFD (mojibake)"""
    try:
        with open(filepath, 'rb') as f:
            content_bytes = f.read()
            
        try:
            content_str = content_bytes.decode('utf-8')
        except UnicodeDecodeError as e:
            return False, f"Lỗi giải mã UTF-8: {e}", ""
            
        if b'\xef\xbf\xbd' in content_bytes or '\ufffd' in content_str:
            return False, "Phát hiện ký tự Mojibake (U+FFFD)", content_str
            
        return True, "OK", content_str
    except Exception as e:
        return False, f"Không thể đọc file: {e}", ""

def check_python_syntax(filepath):
    """Kiểm tra cú pháp Python bằng AST (không sinh bytecode)"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content, filename=filepath)
        return True, "OK"
    except SyntaxError as e:
        return False, f"Lỗi cú pháp Python: {e}"
    except Exception as e:
        return False, f"Lỗi parse Python: {e}"

def check_planning_doc(filepath):
    """Kiểm tra file kế hoạch planning.md không chứa code block quá dài"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        in_block = False
        block_lines = 0
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith('```'):
                if in_block:
                    if block_lines > 25:
                        return False, f"Cảnh báo: Code block dòng {line_num - block_lines} dài quá 25 dòng. Hãy dùng pseudocode."
                    in_block = False
                    block_lines = 0
                else:
                    in_block = True
            elif in_block:
                block_lines += 1
                
        return True, "OK"
    except Exception as e:
        return False, f"Lỗi đọc planning: {e}"

def check_readme_drift(readme_path, gemini_path):
    """Kiểm tra README.html có đồng bộ với GEMINI.md không"""
    try:
        if not os.path.exists(readme_path) or not os.path.exists(gemini_path):
            return True, "Bỏ qua (thiếu file để đối chiếu)"
            
        with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
            readme = f.read()
        with open(gemini_path, 'r', encoding='utf-8', errors='ignore') as f:
            gemini = f.read()
            
        if ".agents" in gemini and ".codex" in readme and ".agents" not in readme:
            return False, "README vẫn dùng .codex làm canonical folder trong khi GEMINI dùng .agents"
            
        return True, "OK"
    except Exception as e:
        return False, f"Lỗi check drift: {e}"

def check_skill_start_blocks(skill_path):
    """Kiểm tra nhãn START_BLOCK trong skill.md có khớp cấu trúc đóng mở không"""
    try:
        with open(skill_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        starts = re.findall(r'<!--\s*START_BLOCK:\s*(\w+)\s*-->', content)
        ends = re.findall(r'<!--\s*END_BLOCK:\s*(\w+)\s*-->', content)
        
        if len(starts) != len(ends):
            return False, f"Lệch số lượng nhãn START_BLOCK ({len(starts)}) và END_BLOCK ({len(ends)})"
            
        for s in starts:
            if s not in ends:
                return False, f"Thiếu nhãn kết thúc cho block: {s}"
                
        return True, "OK"
    except Exception as e:
        return False, f"Lỗi check skill block: {e}"

def check_hardcoded_paths(filepath, content_str):
    """Kiểm tra đường dẫn cứng DOCS/WSR-Core trong tài liệu và rules."""
    filename = os.path.basename(filepath)
    # Bỏ qua việc tự check trong các script scan chính nó
    if filename in ["wsr_audit.py", "wsr_doctor.py", "wsr_clean.py"]:
        return True, "OK"
        
    if "DOCS/WSR-Core" in content_str:
        # Check if it is a genuine hardcoded path usage (not inside changelog for past references)
        if filename != "CHANGELOG.md":
            return False, "Phát hiện đường dẫn cứng DOCS/WSR-Core"
            
    return True, "OK"

def get_git_changed_files(root_dir):
    """Lấy danh sách files thay đổi từ Git, ném lỗi rõ ràng nếu lệnh thất bại"""
    files = []
    
    res1 = subprocess.run(['git', 'diff', '--name-only'], cwd=root_dir, capture_output=True, text=True)
    if res1.returncode != 0:
        raise RuntimeError(f"git diff failed (exit code {res1.returncode}): {res1.stderr.strip()}")
    files.extend([os.path.normpath(os.path.join(root_dir, f)) for f in res1.stdout.splitlines() if f])
    
    res2 = subprocess.run(['git', 'diff', '--cached', '--name-only'], cwd=root_dir, capture_output=True, text=True)
    if res2.returncode != 0:
        raise RuntimeError(f"git diff cached failed (exit code {res2.returncode}): {res2.stderr.strip()}")
    files.extend([os.path.normpath(os.path.join(root_dir, f)) for f in res2.stdout.splitlines() if f])
    
    res3 = subprocess.run(['git', 'status', '--porcelain'], cwd=root_dir, capture_output=True, text=True)
    if res3.returncode != 0:
        raise RuntimeError(f"git status failed (exit code {res3.returncode}): {res3.stderr.strip()}")
    for line in res3.stdout.splitlines():
        if line.startswith('?? '):
            files.append(os.path.normpath(os.path.join(root_dir, line[3:].strip())))
            
    return list(set(files))

def main():
    parser = argparse.ArgumentParser(description="WSR Audit Tool package-local v3")
    parser.add_argument('--path', type=str, default=None, help="Thư mục cần quét")
    parser.add_argument('--mode', type=str, choices=['quick', 'deep'], default='quick', help="Chế độ quét")
    parser.add_argument('--json', action='store_true', help="Xuất kết quả JSON")
    parser.add_argument('--changed', action='store_true', help="Chỉ quét các file thay đổi trong Git")
    
    args = parser.parse_args()
    
    if args.path:
        scan_dir = os.path.abspath(args.path)
    else:
        scan_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
    project_root = wsr_common.get_package_root()
    if args.path:
        project_root = os.path.dirname(scan_dir)
        
    report = {
        'summary': {'total_checked': 0, 'pass_count': 0, 'fail_count': 0, 'score': 100, 'status': 'FAIL'},
        'results': []
    }
    
    # Đọc manifest
    manifest = None
    manifest_path = os.path.join(scan_dir, 'WSR_MANIFEST.json')
    if os.path.exists(manifest_path):
        try:
            manifest = wsr_common.load_manifest(scan_dir)
            # Check required artifacts exist
            for art in manifest.get('artifacts', []):
                if art.get('required', False):
                    req_path = os.path.join(scan_dir, art['source'])
                    if not os.path.exists(req_path):
                        report['results'].append({
                            'file': art['source'],
                            'test': 'required_file_check',
                            'status': 'FAIL',
                            'message': f"Thiếu file bắt buộc theo manifest: {art['source']}"
                        })
        except Exception as e:
            report['results'].append({
                'file': 'WSR_MANIFEST.json',
                'test': 'manifest_parse',
                'status': 'FAIL',
                'message': f"Lỗi đọc manifest: {e}"
            })
            
    # Tái sử dụng Doctor checks trong Deep Mode
    doctor_ran = False
    if args.mode == 'deep':
        doctor_ran = True
        try:
            doc_results, _, _ = wsr_doctor.run_doctor_checks(scan_dir, strict=False, is_json=True)
            for blocker in doc_results.get("blockers", []):
                report['results'].append({
                    'file': 'manifest_schema',
                    'test': 'Doctor_Gate',
                    'status': 'FAIL',
                    'message': f"Doctor Blocker: {blocker}"
                })
            for warning in doc_results.get("warnings", []):
                report['results'].append({
                    'file': 'manifest_schema',
                    'test': 'Doctor_Warning',
                    'status': 'WARN',
                    'message': f"Doctor Warning: {warning}"
                })
        except Exception as e:
            report['results'].append({
                'file': 'wsr_doctor.py',
                'test': 'Doctor_Execution',
                'status': 'FAIL',
                'message': f"Doctor execution failed during preflight: {e}"
            })
            
    # Danh sách file quét
    files_to_check = []
    git_error_occurred = False
    
    if args.changed or args.mode == 'quick':
        try:
            changed_files = get_git_changed_files(project_root)
            for f in changed_files:
                if f.startswith(os.path.normpath(scan_dir)) and os.path.isfile(f):
                    files_to_check.append(f)
        except Exception as e:
            git_error_occurred = True
            report['results'].append({
                'file': 'git',
                'test': 'git_changed_files',
                'status': 'FAIL',
                'message': f"Git failure: {e}"
            })
    else:
        # Deep mode: quét toàn bộ file trong scan_dir dựa trên manifest inventory
        if manifest:
            for art in manifest.get('artifacts', []):
                # Bỏ qua generated checksums
                if art['id'] == 'wsr-checksums':
                    continue
                full_path = os.path.join(scan_dir, art['source'])
                if os.path.isfile(full_path):
                    files_to_check.append(full_path)
        else:
            for root, dirs, files in os.walk(scan_dir, followlinks=False):
                dirs[:] = [d for d in dirs if d not in {'.git', '.venv', '__pycache__', 'DATA', 'Temp', '.agents', '.codex'}]
                for file in files:
                    files_to_check.append(os.path.join(root, file))
                    
    # Bỏ qua các file nhị phân, zip, desktop.ini, pyc
    ignore_extensions = ('.zip', '.png', '.jpg', '.ico', '.ini', '.gif', '.pyc', '.mp3', '.MP3', '.mp4', '.wav', '.psd', '.PSD', '.woff', '.woff2', '.ttf', '.TTF', '.eot', '.pdf', '.webp', '.WEBP', '.cer', '.CER')
    files_to_check = [f for f in files_to_check if not f.endswith(ignore_extensions)]
    
    # Tiến hành audit từng file
    for filepath in files_to_check:
        rel_path = os.path.relpath(filepath, scan_dir).replace('\\', '/')
        report['summary']['total_checked'] += 1
        
        # 1. Kiểm tra UTF-8 và Mojibake (Mọi file text)
        utf8_ok, utf8_msg, content_str = check_utf8_and_mojibake(filepath)
        if not utf8_ok:
            report['results'].append({'file': rel_path, 'test': 'UTF8_Mojibake', 'status': 'FAIL', 'message': utf8_msg})
            continue
            
        # Kiểm tra hardcoded paths (Chống build paths cứng)
        path_ok, path_msg = check_hardcoded_paths(filepath, content_str)
        if not path_ok:
            report['results'].append({'file': rel_path, 'test': 'Hardcoded_Paths', 'status': 'FAIL', 'message': path_msg})
            continue
            
        # 2. Kiểm tra syntax theo loại file
        if filepath.endswith('.py'):
            syntax_ok, syntax_msg = check_python_syntax(filepath)
            if not syntax_ok:
                report['results'].append({'file': rel_path, 'test': 'Python_Syntax', 'status': 'FAIL', 'message': syntax_msg})
                continue
                
        # 3. Kiểm tra file kế hoạch planning
        if 'planning_' in filepath.lower() and filepath.endswith('.md'):
            plan_ok, plan_msg = check_planning_doc(filepath)
            if not plan_ok:
                report['results'].append({'file': rel_path, 'test': 'Planning_Format', 'status': 'FAIL', 'message': plan_msg})
                continue
                
        # 4. Kiểm tra drift README.html
        if rel_path == 'README.html':
            gemini_path = os.path.join(scan_dir, 'GEMINI.md')
            drift_ok, drift_msg = check_readme_drift(filepath, gemini_path)
            if not drift_ok:
                report['results'].append({'file': rel_path, 'test': 'Readme_Drift', 'status': 'FAIL', 'message': drift_msg})
                continue
                
        # 5. Kiểm tra skill start blocks
        if 'skills' in filepath and filepath.endswith('.md'):
            block_ok, block_msg = check_skill_start_blocks(filepath)
            if not block_ok:
                report['results'].append({'file': rel_path, 'test': 'Skill_Start_Block', 'status': 'FAIL', 'message': block_msg})
                continue
                
        report['results'].append({'file': rel_path, 'test': 'All_checks', 'status': 'PASS', 'message': 'OK'})
 
    # Tính điểm scorecard trung thực phản ánh mọi gate
    fails = [r for r in report['results'] if r['status'] == 'FAIL']
    report['summary']['fail_count'] = len(fails)
    report['summary']['pass_count'] = max(0, report['summary']['total_checked'] - len([f for f in fails if f['test'] not in ['Doctor_Gate', 'required_file_check', 'manifest_parse']]))
    
    total_denom = report['summary']['total_checked']
    # Cộng thêm các gate phi-file (Doctor gates, manifest parse, v.v.) vào denominator nếu thất bại
    non_file_fails = len([f for f in fails if f['test'] in ['Doctor_Gate', 'required_file_check', 'manifest_parse']])
    total_denom += non_file_fails
    
    if total_denom > 0:
        score = int((report['summary']['pass_count'] / total_denom) * 100)
        report['summary']['score'] = score
        is_failed = len(fails) > 0 or git_error_occurred
        report['summary']['status'] = 'FAIL' if is_failed or report['summary']['score'] < 100 else 'PASS'
    else:
        report['summary']['score'] = 0
        report['summary']['status'] = 'WARN'
        report['results'].append({
            'file': 'inventory',
            'test': 'zero_coverage_check',
            'status': 'WARN',
            'message': 'Zero files checked during audit — zero-coverage rejection'
        })
        if args.mode == 'deep':
            report['summary']['status'] = 'FAIL'
    
    # Xuất kết quả
    if args.json:
        wsr_common.print_json_report(report)
    else:
        print("==================================================")
        print("   WSR-AUDIT (WSR CORE)")
        print("==================================================")
        print(f"Tổng số file quét: {report['summary']['total_checked']}")
        print(f"Thành công: {report['summary']['pass_count']} | Thất bại: {report['summary']['fail_count']}")
        print("--------------------------------------------------")
        
        for r in report['results']:
            if r['status'] == 'FAIL':
                print(f"[FAIL] {r['file']} | {r['test']}: {r['message']}")
            elif r['status'] == 'WARN':
                print(f"[WARN] {r['file']} | {r['test']}: {r['message']}")
            elif args.mode == 'deep':
                print(f"[PASS] {r['file']} | {r['test']}")
                
        print("==================================================")
        print("             WSR AUDIT SCORECARD")
        print("==================================================")
        print(f"Điểm số: {report['summary']['score']}/100")
        print(f"Trạng thái: {report['summary']['status']}")
        print("==================================================")
        
    sys.exit(wsr_common.EXIT_SUCCESS if report['summary']['status'] == 'PASS' else wsr_common.EXIT_FAIL_FINDING)

if __name__ == '__main__':
    main()
