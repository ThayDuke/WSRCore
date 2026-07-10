import os
import shutil
import zipfile
import re
import sys

def get_latest_version(docs_dir):
    pattern = re.compile(r'^WSR-Duke-All-(\d+)\.(\d+)\.(\d+)$')
    versions = []
    for name in os.listdir(docs_dir):
        path = os.path.join(docs_dir, name)
        if os.path.isdir(path):
            match = pattern.match(name)
            if match:
                major, minor, patch = map(int, match.groups())
                versions.append((major, minor, patch, name))
    if not versions:
        return (2, 4, 2, "WSR-Duke-All-2.4.2")
    versions.sort()
    return versions[-1]

def increment_version(version_tuple):
    major, minor, patch, name = version_tuple
    return major, minor, patch + 1

def create_zip(source_dir, output_zip):
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(source_dir))
                zipf.write(file_path, arcname)

def update_readme(readme_path, old_ver_str, new_ver_str, change_title, change_details):
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Sửa các chuỗi phiên bản trong tiêu đề và nội dung bằng regex
    content = re.sub(r'<title>Duke Workflow V\d+\.\d+\.\d+ — Hướng Dẫn Vận Hành Chuyên Sâu</title>', f'<title>Duke Workflow V{new_ver_str} — Hướng Dẫn Vận Hành Chuyên Sâu</title>', content)
    content = re.sub(r'<p>Release v\d+\.\d+\.\d+\s*\([^)]*\)</p>', f'<p>Release v{new_ver_str} ({change_title})</p>', content)
    content = re.sub(r'AI Developer V\d+\.\d+\.\d+', f'AI Developer V{new_ver_str}', content)
    content = re.sub(r'Chi tiết các thay đổi và tối ưu hóa trong phiên bản WSR-Duke-All-\d+\.\d+\.\d+ so với \d+\.\d+\.\d+\.?', f'Chi tiết các thay đổi và tối ưu hóa trong phiên bản WSR-Duke-All-{new_ver_str} so với {old_ver_str}.', content)
    content = re.sub(r'Detailed changes and optimizations in WSR-Duke-All-\d+\.\d+\.\d+ compared to \d+\.\d+\.\d+\.?', f'Detailed changes and optimizations in WSR-Duke-All-{new_ver_str} compared to {old_ver_str}.', content)
    content = re.sub(r'Triển khai bản \d+\.\d+\.\d+ toàn cục:', f'Triển khai bản {new_ver_str} toàn cục:', content)
    content = re.sub(r'Global \d+\.\d+\.\d+ Deployment Warnings:', f'Global {new_ver_str} Deployment Warnings:', content)


    # Tạo mã HTML cho row changelog mới
    details_html = "".join([f"                <li>{detail.strip()}</li>\n" for detail in change_details.split(";") if detail.strip()])
    
    new_row_html = f"""        <!-- Row 00: WSR-Duke-All-{new_ver_str} ({change_title}) -->
        <div class="changelog-row-outer">
          <div class="changelog-row-inner">
            <div class="changelog-meta">
              <div class="card-icon" style="color: var(--primary-teal); background-color: var(--primary-teal-glow);"><i data-lucide="zap"></i></div>
              <div class="changelog-meta-text">
                <h3>{change_title}</h3>
              </div>
            </div>
            <div class="changelog-details">
              <ul>
{details_html}              </ul>
            </div>
          </div>
        </div>

"""

    # Chèn vào đầu danh sách changelog
    list_marker = '<div class="changelog-list">'
    if list_marker in content:
        parts = content.split(list_marker, 1)
        content = parts[0] + list_marker + "\n" + new_row_html + parts[1]
    else:
        print("Warning: Could not find changelog list marker in README.html")

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    docs_dir = os.path.join(project_root, "DOCS")
    agents_dir = os.path.join(project_root, ".agents")
    global_dir = os.path.join(agents_dir, "global")

    # Đọc đối số dòng lệnh
    change_title = "Cập nhật & Sửa lỗi hệ thống"
    change_details = "Chỉnh sửa quy tắc duyệt pl trong GEMINI.md;Cải thiện độ sắc nét icon taskbar trên Windows"
    if len(sys.argv) > 1:
        change_title = sys.argv[1]
    if len(sys.argv) > 2:
        change_details = sys.argv[2]

    # 1. Tìm phiên bản hiện tại và tăng phiên bản
    latest = get_latest_version(docs_dir)
    major, minor, patch, old_name = latest
    new_major, new_minor, new_patch = increment_version(latest)
    old_ver_str = f"{major}.{minor}.{patch}"
    new_ver_str = f"{new_major}.{new_minor}.{new_patch}"
    new_name = f"WSR-Duke-All-{new_ver_str}"
    
    old_dir_path = os.path.join(docs_dir, old_name)
    new_dir_path = os.path.join(docs_dir, new_name)
    new_zip_path = os.path.join(docs_dir, f"{new_name}.zip")

    print(f"Phiên bản hiện tại: {old_ver_str} ({old_name})")
    print(f"Phiên bản mới sẽ tạo: {new_ver_str} ({new_name})")

    # 2. Tạo thư mục mới và sao chép cấu trúc
    if os.path.exists(new_dir_path):
        shutil.rmtree(new_dir_path)
    os.makedirs(new_dir_path)

    # Copy các thư mục WSR global hiện tại
    shutil.copy2(os.path.join(global_dir, "GEMINI.md"), os.path.join(new_dir_path, "GEMINI.md"))
    shutil.copytree(os.path.join(global_dir, "rules"), os.path.join(new_dir_path, "global_rules"))
    shutil.copytree(os.path.join(agents_dir, "skills"), os.path.join(new_dir_path, "global_skills"))
    shutil.copytree(os.path.join(global_dir, "workflows"), os.path.join(new_dir_path, "global_workflows"))
    shutil.copy2(os.path.join(global_dir, "desktop.ini"), os.path.join(new_dir_path, "desktop.ini"))
    shutil.copy2(os.path.join(global_dir, "Installation_guide.txt"), os.path.join(new_dir_path, "Installation_guide.txt"))

    # Copy README.html gốc từ global_dir sang phiên bản mới
    new_readme = os.path.join(new_dir_path, "README.html")
    shutil.copy2(os.path.join(global_dir, "README.html"), new_readme)

    # 3. Cập nhật README.html
    update_readme(new_readme, old_ver_str, new_ver_str, change_title, change_details)
    print("Đã cập nhật README.html với thông tin changelog mới.")

    # 4. Nén thành file .zip
    if os.path.exists(new_zip_path):
        os.remove(new_zip_path)
    create_zip(new_dir_path, new_zip_path)
    print(f"Đã đóng gói thành công file nén: {new_name}.zip")

    # Đồng bộ hóa README.html mới này ngược lại thư mục global/ của .agents để làm tài liệu chuẩn gốc
    shutil.copy2(new_readme, os.path.join(global_dir, "README.html"))
    print("Đã đồng bộ README.html mới vào thư mục global của Agent.")

if __name__ == "__main__":
    main()
