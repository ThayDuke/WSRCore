import os
import shutil

def install_taste_skills():
    src_base = r"h:\My Drive\1. DEC-Good\.codex\taste-skill-main\skills"
    dest_base = r"h:\My Drive\1. DEC-Good\.codex\skills"
    
    skills_to_install = [
        "stitch-skill",
        "output-skill",
        "redesign-skill",
        "soft-skill"
    ]
    
    print("Bắt đầu cài đặt các Taste Skills vào dự án...")
    
    for skill in skills_to_install:
        src_dir = os.path.join(src_base, skill)
        dest_dir = os.path.join(dest_base, skill)
        
        if not os.path.exists(src_dir):
            print(f"Lỗi: Không tìm thấy thư mục nguồn {src_dir}")
            continue
            
        # Xóa thư mục đích cũ nếu tồn tại
        if os.path.exists(dest_dir):
            try:
                shutil.rmtree(dest_dir)
            except Exception as e:
                print(f"Không thể xóa thư mục cũ {dest_dir}. {e}")
                
        try:
            shutil.copytree(src_dir, dest_dir)
            print(f"Đã cài đặt: {skill} -> {dest_dir}")
        except Exception as e:
            print(f"Lỗi khi copy skill {skill}: {e}")

if __name__ == "__main__":
    install_taste_skills()
