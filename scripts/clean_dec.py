import os
import re
import argparse
from pathlib import Path

# Setup paths
workspace_dir = Path(r"h:\My Drive\1. DEC-Good")
docs_dir = workspace_dir / "DOCS"

def scan_docs_plans():
    plan_pattern = re.compile(r"^planning_(.+)_v(\d+)\.md$", re.IGNORECASE)
    groups = {} # base_name -> list of (version, path, size)
    
    dirs_to_scan = [docs_dir, docs_dir / "Planning"]
    for d in dirs_to_scan:
        if d.exists() and d.is_dir():
            for item in d.iterdir():
                if item.is_file():
                    match = plan_pattern.match(item.name)
                    if match:
                        base_name = match.group(1).lower()
                        version = int(match.group(2))
                        size = item.stat().st_size
                        groups.setdefault(base_name, []).append((version, item, size))
                
    keep_files = []
    remove_files = []
    
    for base_name, files in groups.items():
        # Sắp xếp theo version giảm dần
        files.sort(key=lambda x: x[0], reverse=True)
        # File có version cao nhất
        keep_version, keep_path, keep_size = files[0]
        keep_files.append((keep_path, keep_size, keep_version))
        
        # Các file version thấp hơn
        for ver, path, size in files[1:]:
            remove_files.append((path, size, ver, keep_version))
            
    return keep_files, remove_files

def scan_trash_files():
    # Whitelist các thư mục/file tuyệt đối không được xóa
    whitelist_dirs = [
        ".git",
        ".agents",
        ".vscode",
        ".github",
        "DATA",
        "ENGINE",
        "Template"
    ]
    
    trash_files = []
    
    for root, dirs, files in os.walk(workspace_dir):
        # Lọc các thư mục whitelist tại root
        if Path(root) == workspace_dir:
            dirs[:] = [d for d in dirs if d not in whitelist_dirs]
            
        # Nếu ở trong Tools, loại trừ assets
        if Path(root) == workspace_dir / "Tools":
            dirs[:] = [d for d in dirs if d != "assets"]
            
        # Duyệt qua các tệp tin trong các thư mục được phép quét
        for file in files:
            file_path = Path(root) / file
            file_name_lower = file.lower()
            
            is_trash = False
            if file_name_lower in ["desktop.ini", "thumbs.db", ".ds_store"]:
                is_trash = True
            elif file_name_lower.endswith(".log") or file_name_lower.endswith(".tmp"):
                is_trash = True
            elif "__pycache__" in file_path.parts or ".pytest_cache" in file_path.parts:
                is_trash = True
                
            if is_trash:
                try:
                    size = file_path.stat().st_size
                    trash_files.append((file_path, size))
                except Exception:
                    trash_files.append((file_path, 0))
                    
    return trash_files

def main():
    parser = argparse.ArgumentParser(description="DEC Workspace Cleaner Script")
    parser.add_argument("--delete", action="store_true", help="Xóa thực tế các file đề xuất")
    args = parser.parse_args()
    
    print("=== BẮT ĐẦU QUÉT DỌN DẸP WORKSPACE ===")
    
    # 1. Quét các file kế hoạch cũ trong DOCS
    keep_plans, remove_plans = scan_docs_plans()
    
    # 2. Quét các file rác hệ thống
    trash_files = scan_trash_files()
    
    total_size = 0
    
    # Báo cáo file kế hoạch cũ
    print("\n[FILE KẾ HOẠCH CŨ TRONG DOCS] (Đề xuất xóa):")
    if remove_plans:
        for path, size, ver, max_ver in remove_plans:
            rel_path = path.relative_to(workspace_dir)
            print(f"- {rel_path} (v{ver} < v{max_ver}) - {size} bytes")
            total_size += size
    else:
        print(" Không có file kế hoạch cũ nào.")
        
    # Báo cáo file rác hệ thống
    print("\n[TỆP RÁC HỆ THỐNG] (Đề xuất xóa):")
    if trash_files:
        for path, size in trash_files:
            rel_path = path.relative_to(workspace_dir)
            print(f"- {rel_path} - {size} bytes")
            total_size += size
    else:
        print(" Không có tệp rác hệ thống.")
        
    print(f"\nTổng dung lượng đề xuất giải phóng: {total_size} bytes ({total_size / 1024:.2f} KB)")
    
    if args.delete:
        print("\n--- ĐANG THỰC HIỆN XÓA THỰC TẾ ---")
        deleted_count = 0
        error_count = 0
        
        # Xóa file kế hoạch cũ
        for path, _, _, _ in remove_plans:
            try:
                path.unlink()
                print(f"Đã xóa: {path.relative_to(workspace_dir)}")
                deleted_count += 1
            except Exception as e:
                print(f"Lỗi khi xóa {path.relative_to(workspace_dir)}: {e}")
                error_count += 1
                
        # Xóa file rác
        for path, _ in trash_files:
            try:
                if path.is_file():
                    path.unlink()
                    print(f"Đã xóa: {path.relative_to(workspace_dir)}")
                    deleted_count += 1
            except Exception as e:
                print(f"Lỗi khi xóa {path.relative_to(workspace_dir)}: {e}")
                error_count += 1
                
        print(f"\nHoàn thành! Đã xóa {deleted_count} files, thất bại {error_count} files.")
    else:
        print("\n[LƯU Ý]: Chạy lệnh với tham số '--delete' để thực hiện xóa thực tế.")

if __name__ == "__main__":
    main()
