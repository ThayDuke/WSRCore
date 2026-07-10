import os
import shutil
import glob

def copy_images():
    brain_dir = r"C:\Users\DUKE NGUYEN\.gemini\antigravity-ide\brain\e0f729f6-2193-4aa2-9c47-d0e40c5f7573"
    dest_dir = r"h:\My Drive\1. DEC-Good\DOCS\assets"
    
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        print(f"Đã tạo thư mục đích: {dest_dir}")
        
    # Tìm file hero
    hero_pattern = os.path.join(brain_dir, "agent_workflow_hero_*.png")
    hero_files = glob.glob(hero_pattern)
    if hero_files:
        shutil.copy2(hero_files[0], os.path.join(dest_dir, "hero.png"))
        print(f"Đã copy hero image -> hero.png")
        
    # Tìm file pruning
    pruning_pattern = os.path.join(brain_dir, "context_pruning_concept_*.png")
    pruning_files = glob.glob(pruning_pattern)
    if pruning_files:
        shutil.copy2(pruning_files[0], os.path.join(dest_dir, "pruning.png"))
        print(f"Đã copy pruning image -> pruning.png")

    # Tìm file hero_light
    hero_light_pattern = os.path.join(brain_dir, "hero_light_*.png")
    hero_light_files = glob.glob(hero_light_pattern)
    if hero_light_files:
        shutil.copy2(hero_light_files[0], os.path.join(dest_dir, "hero_light.png"))
        print(f"Đã copy hero_light image -> hero_light.png")

    # Tìm file pruning_light
    pruning_light_pattern = os.path.join(brain_dir, "pruning_light_*.png")
    pruning_light_files = glob.glob(pruning_light_pattern)
    if pruning_light_files:
        shutil.copy2(pruning_light_files[0], os.path.join(dest_dir, "pruning_light.png"))
        print(f"Đã copy pruning_light image -> pruning_light.png")

if __name__ == "__main__":
    copy_images()
