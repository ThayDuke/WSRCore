# DEC Codex Instructions

This repository uses Codex-native project guidance at the repository root and
keeps DEC-specific operating knowledge under `.agents/`.

## Canonical Locations

- Project instructions: [AGENTS.md](file:///h:/My%20Drive/1.%20DEC-Good/.agents/AGENTS.md)
- DEC skill: [.agents/skills/dec-dev-operator/SKILL.md](file:///h:/My%20Drive/1.%20DEC-Good/.agents/skills/dec-dev-operator/SKILL.md) (Hợp nhất từ `DEC_UI_skill.md`)
- Stitch skill: [.agents/skills/stitch-skill/SKILL.md](file:///h:/My%20Drive/1.%20DEC-Good/.agents/skills/stitch-skill/SKILL.md)
- Output skill: [.agents/skills/output-skill/SKILL.md](file:///h:/My%20Drive/1.%20DEC-Good/.agents/skills/output-skill/SKILL.md)
- Effective HTML skill: [.agents/skills/effective-html/SKILL.md](file:///h:/My%20Drive/1.%20DEC-Good/.agents/skills/effective-html/SKILL.md)
- Redesign skill: [.agents/skills/redesign-skill/SKILL.md](file:///h:/My%20Drive/1.%20DEC-Good/.agents/skills/redesign-skill/SKILL.md)
- Soft skill: [.agents/skills/soft-skill/SKILL.md](file:///h:/My%20Drive/1.%20DEC-Good/.agents/skills/soft-skill/SKILL.md)
- DEC decision rules: [.agents/rules/AG_DECISION_RULES.md](file:///h:/My%20Drive/1.%20DEC-Good/.agents/rules/AG_DECISION_RULES.md) (Kế thừa từ `AG_GLOBAL_RULES.md`)
- DEC debug playbook: [.agents/rules/dec-debug-playbook.md](file:///h:/My%20Drive/1.%20DEC-Good/.agents/rules/dec-debug-playbook.md)
- DEC regression checklists: [.agents/rules/regression-checklists.md](file:///h:/My%20Drive/1.%20DEC-Good/.agents/rules/regression-checklists.md)
- DEC lessons memory: [.agents/memory/AG_LESSONS.jsonl](file:///h:/My%20Drive/1.%20DEC-Good/.agents/memory/AG_LESSONS.jsonl)
- DEC backup script: [.agents/scripts/backup_dec.py](file:///h:/My%20Drive/1.%20DEC-Good/.agents/scripts/backup_dec.py)
- Global Config Sync script: [.agents/scripts/sync_config.py](file:///h:/My%20Drive/1.%20DEC-Good/.agents/scripts/sync_config.py)

> [!NOTE]
> The workspace customization folder has been restored to `.agents/` as the default standard.

## Operating Rules

- Respond in Vietnamese for DEC work.
- Load `.agents/skills/dec-dev-operator/SKILL.md` when the task concerns DEC
  debugging, refactoring, UI standards, tooling, generated lessons, or agent
  operating policy.
- Load `.agents/skills/effective-html/SKILL.md` (ehtml/htmle) when proposing visual planning,
  architectural diagrams, or self-contained HTML artifacts.
- **Skill Loading Router:** To optimize token usage and prevent visual conflicts, only load the required design skill file:
  - **Stitch skill** (`.agents/skills/stitch-skill/SKILL.md`): Load ONLY when generating/updating Stitch `DESIGN.md` files.
  - **Redesign skill** (`.agents/skills/redesign-skill/SKILL.md`): Load ONLY when refactoring/upgrading existing legacy UI.
  - **Soft skill** (`.agents/skills/soft-skill/SKILL.md`): Load ONLY when designing high-end visual features/new screens from scratch.
- **Auto-Sync Config:** At the very start of any session or when the workspace is opened, Agent must automatically execute `python .agents/scripts/sync_config.py` to keep the global Agent configuration directories synchronized with the local `.agents/global/` settings.
- Follow `.agents/rules/AG_DECISION_RULES.md` and global rules in `C:\Users\DUKE NGUYEN\.gemini\config\global_rules\AG_GLOBAL_RULES.md` for DEC implementation decisions.
- Query `.agents/memory/AG_LESSONS.jsonl` only when prior lessons are relevant to
  the current file, symptom, tag, or tool surface.
> [!WARNING]
> Prefer focused patches and avoid rewriting Vietnamese files wholesale because
> several legacy files are sensitive to encoding drift.
> 
> Write new Vietnamese-facing documentation, rules, logs, UI copy, and reports in
> standard accented Vietnamese encoded as UTF-8. Do not use unaccented
> Vietnamese as a workaround for mojibake risk. After writing Vietnamese text,
> verify UTF-8 decoding and check that no replacement character `U+FFFD`,
> suspicious ASCII question mark `U+003F`, or invalid UTF-8 mojibake patterns (such as double-encoded UTF-8 strings) were introduced. Valid Vietnamese words containing `ã`, `Ã`, `â`, `Â` (such as "đã", "Đã", "ĐÃ HOÀN THÀNH NHIỆM VỤ") are permitted and must not trigger false alerts.
- Treat existing uncommitted changes as user-owned. Do not revert or clean them
  unless the user explicitly asks.
- **Clean Whitelist (DEC-specific):** When running clean, always whitelist the following DEC-specific directories: `DATA/`, `ENGINE/`, `Tools/assets/`, template folders, and keep them untouched.
- **Luật Sắt (Iron Rule - Chống tự ý thực thi):** Tuyệt đối cấm gọi công cụ ghi/xóa/chạy lệnh thay đổi hệ thống khi trả lời câu hỏi hoặc thảo luận (đặc biệt khi tin nhắn của người dùng có dấu chấm hỏi `?` or không chứa từ khóa phê duyệt rõ ràng như `ok`, `làm đi`). Chỉ sử dụng công cụ đọc. Khi gọi công cụ sửa đổi, bắt buộc phải trích dẫn rõ từ khóa phê duyệt trong `thought` và `Description`. Vi phạm sẽ cấu thành lỗi nghiêm trọng và rollback dự án ngay lập tức.

> [!IMPORTANT]
> **Caveman Style & Flash Guard (Giảm Verbosity):** Mặc định phản hồi siêu ngắn (3-5 câu) kiểu điện tín. Cấm giải thích cơ chế code trừ khi được hỏi "Tại sao?".
> 
> **Cấm vận hành lãng phí:** Cấm tự động chạy test suite nặng (npm test, pytest...); cấm tự ý sử dụng Chrome, browser_subagent, open_browser_url, hoặc chrome-devtools-plugin để test giao diện tự động (chỉ test thủ công); cấm thao tác Git phức tạp (rebase, merge, push); cấm tạo file `implementation_plan.md` vật lý (duyệt trực tiếp trên chat), các tài liệu khác dưới 15 dòng.
> 
> **Giới hạn Code trên Chat (Tuyệt đối):** CẤM HOÀN TOÀN việc in block code (dù ngắn hay dài, HTML, CSS, JS) lên màn hình chat khi thảo luận. Chỉ được phép gạch đầu dòng mô tả tính năng/giao diện và rủi ro. Chỉ in code lên chat khi và chỉ khi nhận được yêu cầu đích danh từ người dùng (ví dụ: "in code cho tôi xem"). Mọi hành vi in code không yêu cầu sẽ bị coi là lỗi vận hành nghiêm trọng.

## DEC Abbreviations

- `TL`: ToolListening
- `TQ`: ToolQuiz
- `TS`: ToolSlide
- `TE`: ToolExam
- `TA`: ToolAdaptive
- `TQI`: ToolQbankImport
- `GL`: Game Lobby (màn hình lobby trung gian ToolGame.html, miễn trừ hoàn toàn DMU)
- `GC`: Game Castle (màn hình game Castle.html, miễn trừ hoàn toàn DMU)
- `GB`: Game Battle (màn hình game Battle.html, miễn trừ hoàn toàn DMU)
- `DMU`: DEC Master UI
- `Theme Y`, `giao dien Y`, `gd y`: Youth theme
- `Theme E`, `giao dien E`, `gd e`: Elegant theme
- `ehtml` hoặc `htmle`: Effective HTML (skill tạo artifact HTML trực quan)
- `wsr` hoặc `wrs`: Bộ ba 'Workflow, Skill, Rule' / 'Workflow, Rule, Skill'

## DEC Workflow Shortcuts

- `/br`: load and follow `.agents/global/workflows/br.md`.
- `/pl`: load and follow `.agents/global/workflows/pl.md`.
- `/reload`: load and follow `.agents/global/workflows/reload.md`.
- `/clean`: load and follow `.agents/global/workflows/clean.md`.
- `/commit`: load and follow `.agents/global/workflows/commit.md`.
- `/backup`: load and follow `.agents/global/workflows/backup.md`.
- `/audit`: load and follow `.agents/global/workflows/audit.md`.
- Treat these as project-local DEC workflow aliases, even when Codex does not
  expose them as native slash commands.

## DEC Backup Shortcut

- `backup dec*` or `bak dec*`: create a `.zip` backup of the entire
  `1. DEC-Good` project.
- Match the shortcut case-insensitively.
- Save the `.zip` file to `E:\BACKUP DukeEnglishCenter`.
- Exclude `.git`, `.venv`, `__pycache__`, `Temp`, and `Backups` from the archive.
- If any text follows `backup dec` or `bak dec`, use that text as the archive
  filename after removing characters invalid for Windows filenames
  (`< > : " / \ | ? *`) and trimming trailing spaces/dots.
- If no filename text follows the shortcut, use
  `DEC_ddMMyyyy_HHmmss.zip`, for example `DEC_07052026_142536.zip`.
- Ensure the final filename ends with `.zip`.

