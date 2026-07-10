import os
import shutil

def sync_config():
    # Thư mục nguồn cục bộ trong repo
    local_global_dir = r"h:\My Drive\1. DEC-Good\.agents\global"
    
    # Thư mục đích global của Agent
    user_profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    target_base_dir = os.path.join(user_profile, ".gemini", "config")
    
    # Định nghĩa ánh xạ thư mục
    mappings = {
        "rules": os.path.join(target_base_dir, "global_rules"),
        "workflows": os.path.join(target_base_dir, "global_workflows")
    }
    
    print("Bắt đầu đồng bộ hóa cấu hình Agent toàn cục...")
    
    # 1. Đồng bộ file GEMINI.md global
    src_gemini = os.path.join(local_global_dir, "GEMINI.md")
    dest_gemini = os.path.join(user_profile, ".gemini", "GEMINI.md")
    if os.path.exists(src_gemini):
        try:
            shutil.copy2(src_gemini, dest_gemini)
            print(f"Đã đồng bộ file GEMINI.md -> {dest_gemini}")
        except Exception as e:
            print(f"Lỗi khi copy GEMINI.md: {e}")
            
    # 2. Đồng bộ các folder rules và workflows
    for src_sub, dest_dir in mappings.items():
        src_dir = os.path.join(local_global_dir, src_sub)
        if not os.path.exists(src_dir):
            continue
            
        if not os.path.exists(dest_dir):
            try:
                os.makedirs(dest_dir)
                print(f"Đã tạo thư mục đích: {dest_dir}")
            except Exception as e:
                print(f"Lỗi: Không thể tạo thư mục {dest_dir}. {e}")
                continue
                
        # Copy các file
        for file in os.listdir(src_dir):
            src_file = os.path.join(src_dir, file)
            dest_file = os.path.join(dest_dir, file)
            if os.path.isfile(src_file):
                try:
                    shutil.copy2(src_file, dest_file)
                    print(f"Đã đồng bộ: {file} -> {dest_file}")
                except Exception as e:
                    print(f"Lỗi khi copy {file}: {e}")

if __name__ == "__main__":
    sync_config()
