import os
import zipfile
import datetime
import sys
import re
import io

# Cấu hình stdout hỗ trợ UTF-8 để in tiếng Việt không bị lỗi encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def clean_filename(filename):
    # Loại bỏ các ký tự không hợp lệ cho Windows filename: < > : " / \ | ? *
    cleaned = re.sub(r'[<>:"/\\|?*]', '', filename).strip().rstrip('. ')
    return cleaned

def backup_dec(custom_name=None):
    source_dir = r"h:\My Drive\1. DEC-Good"
    target_base_dir = r"E:\BACKUP DukeEnglishCenter"
    
    # Kiểm tra thư mục nguồn
    if not os.path.exists(source_dir):
        print(f"Lỗi: Không tìm thấy thư mục nguồn {source_dir}")
        return

    # Tạo thư mục đích nếu chưa tồn tại
    if not os.path.exists(target_base_dir):
        try:
            os.makedirs(target_base_dir)
            print(f"Đã tạo thư mục lưu trữ: {target_base_dir}")
        except Exception as e:
            print(f"Lỗi: Không thể tạo thư mục đích {target_base_dir}. {e}")
            return

    # Xử lý tên file
    now = datetime.datetime.now()
    if custom_name:
        filename = clean_filename(custom_name)
        if not filename:
            filename = f"DEC_{now.strftime('%d%m%Y_%H%M%S')}"
    else:
        filename = f"DEC_{now.strftime('%d%m%Y_%H%M%S')}"
    
    if not filename.lower().endswith('.zip'):
        filename += '.zip'
        
    target_path = os.path.join(target_base_dir, filename)

    print(f"Đang tiến hành nén dự án... (Loại trừ .git)")
    
    try:
        count = 0
        with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                # Loại bỏ thư mục .git và các thư mục không cần thiết
                if '.git' in dirs:
                    dirs.remove('.git')
                if '.venv' in dirs:
                    dirs.remove('.venv')
                if '__pycache__' in dirs:
                    dirs.remove('__pycache__')

                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
                    count += 1
                    
        print(f"--------------------------------------------------")
        print(f"HOÀN TẤT BACKUP!")
        print(f"Tổng số file đã nén: {count}")
        print(f"Vị trí lưu: {target_path}")
        print(f"--------------------------------------------------")
    except Exception as e:
        print(f"Lỗi nghiêm trọng trong quá trình nén: {e}")

if __name__ == "__main__":
    # Nhận toàn bộ tham số truyền vào từ dòng lệnh
    arg_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    backup_dec(arg_text)
