import os
import shutil

def clear_and_create_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def ignore_trash(dir_path, filenames):
    ignored = []
    for f in filenames:
        f_lower = f.lower()
        if f_lower in ["desktop.ini", "thumbs.db", ".ds_store"] or f_lower.endswith(".tmp") or f_lower.endswith(".pyc") or "__pycache__" in f_lower:
            ignored.append(f)
    return ignored

def export_generic_wsr(project_dir, local_global_dir):
    dest_dir = os.path.join(project_dir, "DOCS", "WSR-Duke-All-2.4.2")
    print(f"\n--- [1] XUẤT GÓI GENERIC WSR: {dest_dir} ---")
    
    # Dọn dẹp thư mục đích cũ nếu có để tránh file rác
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir)
        
    # Copy các file ở root gói
    shutil.copy2(os.path.join(local_global_dir, "GEMINI.md"), os.path.join(dest_dir, "GEMINI.md"))
    shutil.copy2(os.path.join(local_global_dir, "README.html"), os.path.join(dest_dir, "README.html"))
    shutil.copy2(os.path.join(local_global_dir, "hero_light.png"), os.path.join(dest_dir, "hero_light.png"))
    shutil.copy2(os.path.join(local_global_dir, "pruning_light.png"), os.path.join(dest_dir, "pruning_light.png"))
    print("Đã xuất: GEMINI.md, README.html, assets")

    # Copy rules và workflows toàn cục
    shutil.copytree(os.path.join(local_global_dir, "rules"), os.path.join(dest_dir, "global_rules"), ignore=ignore_trash, dirs_exist_ok=True)
    shutil.copytree(os.path.join(local_global_dir, "workflows"), os.path.join(dest_dir, "global_workflows"), ignore=ignore_trash, dirs_exist_ok=True)
    print("Đã xuất: global_rules/, global_workflows/")

    # Copy global skills
    local_skills_dir = os.path.join(project_dir, ".agents", "skills")
    dest_skills_dir = os.path.join(dest_dir, "global_skills")
    global_skills = ["output-skill", "redesign-skill", "soft-skill", "stitch-skill"]
    
    if os.path.exists(local_skills_dir):
        os.makedirs(dest_skills_dir, exist_ok=True)
        for skill in global_skills:
            src = os.path.join(local_skills_dir, skill)
            if os.path.exists(src):
                shutil.copytree(src, os.path.join(dest_skills_dir, skill), ignore=ignore_trash, dirs_exist_ok=True)
                print(f"  + Đã xuất skill: {skill}")

    # Tạo file nén zip cho gói generic WSR
    zip_path = dest_dir + ".zip"
    if os.path.exists(zip_path):
        os.remove(zip_path)
    shutil.make_archive(dest_dir, 'zip', dest_dir)
    print(f"Đã nén thành công: {dest_dir}.zip")

def export_dec_wsr(project_dir):
    dest_dir = os.path.join(project_dir, "DOCS", "WSR-DEC")
    print(f"\n--- [2] XUẤT GÓI ĐẶC THÙ DEC (WSR-DEC): {dest_dir} ---")
    
    # Dọn dẹp thư mục đích cũ nếu có để tránh file rác
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir)
        
    # Copy ReadmeDEC.html cục bộ của DEC
    src_readme_dec = os.path.join(project_dir, ".agents", "ReadmeDEC.html")
    if os.path.exists(src_readme_dec):
        shutil.copy2(src_readme_dec, os.path.join(dest_dir, "README.html"))
        print("Đã xuất: ReadmeDEC.html thành README.html")
        
    # Copy AGENTS.md cục bộ của DEC
    src_agents = os.path.join(project_dir, ".agents", "AGENTS.md")
    if os.path.exists(src_agents):
        shutil.copy2(src_agents, os.path.join(dest_dir, "AGENTS.md"))
        print("Đã xuất: AGENTS.md (DEC version)")

    # Copy rules cục bộ (AG_DECISION_RULES.md, Playbook, Checklist, v.v.)
    src_rules = os.path.join(project_dir, ".agents", "rules")
    if os.path.exists(src_rules):
        shutil.copytree(src_rules, os.path.join(dest_dir, "local_rules"), ignore=ignore_trash, dirs_exist_ok=True)
        print("Đã xuất: local_rules/ (AG_DECISION_RULES.md, playbook...)")

    # Copy local skill (dec-dev-operator)
    src_operator = os.path.join(project_dir, ".agents", "skills", "dec-dev-operator")
    if os.path.exists(src_operator):
        shutil.copytree(src_operator, os.path.join(dest_dir, "local_skills", "dec-dev-operator"), ignore=ignore_trash, dirs_exist_ok=True)
        print("Đã xuất: local_skills/dec-dev-operator/")

    # Copy local scripts (backup_dec.py, sync_config.py, wsr_audit.py)
    dest_scripts = os.path.join(dest_dir, "local_scripts")
    os.makedirs(dest_scripts, exist_ok=True)
    
    scripts = [
        (os.path.join(project_dir, ".agents", "scripts", "backup_dec.py"), "backup_dec.py"),
        (os.path.join(project_dir, ".agents", "scripts", "sync_config.py"), "sync_config.py"),
        (os.path.join(project_dir, ".agents", "scripts", "export_wsr_all.py"), "export_wsr_all.py"),
        (os.path.join(project_dir, "ENGINE", "wsr_audit.py"), "wsr_audit.py")
    ]
    for src, name in scripts:
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dest_scripts, name))
            print(f"  + Đã xuất script: {name}")

def main():
    project_dir = r"h:\My Drive\1. DEC-Good"
    local_global_dir = os.path.join(project_dir, ".agents", "global")
    
    if not os.path.exists(local_global_dir):
        print(f"Lỗi: Không tìm thấy thư mục nguồn {local_global_dir}")
        return
        
    export_generic_wsr(project_dir, local_global_dir)
    export_dec_wsr(project_dir)
    print("\n[Thành công]: Quá trình xuất WSR hoàn tất!")

if __name__ == "__main__":
    main()
