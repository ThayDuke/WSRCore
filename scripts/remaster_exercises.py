import os
import sys
import re
import json
from pathlib import Path

# Add ENGINE to path to import template module
SELF_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SELF_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "ENGINE"))

from launcher_modules.ultitemp_template import build_inline_html
import eng_to_ipa as ipa

TEMPLATE_FILE = PROJECT_ROOT / "Template" / "UltiTemp.html"

def get_ipa_map(text_content):
    try:
        # Extract individual English words, ignore punctuation
        words = re.findall(r"\b[a-zA-Z']+\b", text_content)
        word_map = {}
        for w in words:
            w_lower = w.lower()
            if w_lower not in word_map:
                converted = ipa.convert(w_lower)
                if converted:
                    word_map[w_lower] = converted.replace("*", "")
        return word_map
    except Exception as e:
        print(f"  [IPA MAP ERROR] {e}")
        return {}

def remaster_file(file_path):
    try:
        print(f"Processing: {file_path.relative_to(PROJECT_ROOT)}...")
        content = file_path.read_text(encoding="utf-8")
        
        # 1. Extract lessonData block
        data_match = re.search(r'const\s+lessonData\s*=\s*(\[[\s\S]*?\]);', content)
        if not data_match:
            print(f"  [Error] No lessonData found in {file_path.name}")
            return False
            
        lesson_data_str = data_match.group(1)
        
        # Extract all texts to generate IPA map
        all_texts = re.findall(r'"(?:text|title)"\s*:\s*"(.*?)"', lesson_data_str)
        combined_text = " ".join(all_texts)

        # 2. Determine Level
        parent_dir = file_path.parent.name.upper()
        grandparent_dir = file_path.parent.parent.name.upper()
        
        level = "B"
        if "LEVEL A" in grandparent_dir or "LEVEL A" in parent_dir:
            level = "A"
        elif "LEVEL C" in grandparent_dir or "LEVEL C" in parent_dir:
            level = "C"

        # 3. Extract title
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
        title = title_match.group(1) if title_match else file_path.stem

        # 4. Extract data-mode
        mode_match = re.search(r'<body[^>]*data-mode="([^"]+)"', content, re.IGNORECASE)
        mode = mode_match.group(1) if mode_match else "listening"

        # 5. Build HTML from template
        html_content = build_inline_html(TEMPLATE_FILE)

        # Set runtime mode in body attribute
        if mode == "ipa":
            html_content = html_content.replace("<body", '<body data-mode="ipa"')
        else:
            html_content = html_content.replace("<body", '<body data-mode="listening"')

        # Inject title
        safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").strip()
        html_content = re.sub(
            r"<title>.*?</title>",
            f"<title>{safe_title}</title>",
            html_content,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )
        html_content = html_content.replace("${LESSONTITLE}", title)
        html_content = html_content.replace("${lessonTitle}", title)
        html_content = html_content.replace("Luyện Nghe: From Shy to Happy", title)

        # Inject lessonLevel and placeholder for LESSON_TARGET_PHONETICS
        html_content = html_content.replace(
            "const LESSON_TARGET_PHONETICS = {};",
            'const lessonLevel = "' + level + '";\n        const LESSON_TARGET_PHONETICS = {};'
        )

        # Inject lessonData
        html_content = re.sub(
            r'const\s+lessonData\s*=\s*\[[\s\S]*?\];',
            'const lessonData = ' + lesson_data_str + ';',
            html_content,
            count=1,
        )

        # Inject dynamic LESSON_TARGET_PHONETICS map
        ipa_map = get_ipa_map(combined_text)
        ipa_json = json.dumps(ipa_map, ensure_ascii=False, indent=8)
        html_content = html_content.replace(
            "const LESSON_TARGET_PHONETICS = {};",
            'const LESSON_TARGET_PHONETICS = ' + ipa_json + ';',
            1
        )

        # Fix margins
        html_content = re.sub(r'<img[^>]*class="app-logo"[^>]*>', '', html_content)
        html_content = html_content.replace('margin-left: 70px;', 'margin-left: 0;')
        html_content = html_content.replace('margin-right: 70px;', 'margin-right: 0;')
        html_content = html_content.replace('margin-left: 56px;', 'margin-left: 0;')
        html_content = html_content.replace('margin-right: 56px;', 'margin-right: 0;')

        # Save HTML
        file_path.write_text(html_content, encoding="utf-8")
        print(f"  [Success] Remastered {file_path.name}")
        return True
    except Exception as e:
        print(f"  [Error] Failed to remaster {file_path.name}: {e}")
        return False

def main():
    target_dirs = [
        PROJECT_ROOT / "1. LEVEL A" / "A4. LUYỆN NGHE SƠ CẤP",
        PROJECT_ROOT / "2. LEVEL B" / "B4. LUYỆN NGHE TRUNG CẤP",
        PROJECT_ROOT / "3. LEVEL C" / "C4. LUYỆN NGHE NÂNG CAO"
    ]
    
    total = 0
    success = 0
    
    for d in target_dirs:
        if not d.exists():
            print(f"Directory not found: {d}")
            continue
            
        for file in d.glob("*.html"):
            total += 1
            if remaster_file(file):
                success += 1
                
    print(f"\nCompleted! Remastered {success}/{total} files successfully.")

if __name__ == "__main__":
    main()
