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
- **Phase-based Lazy Loading:** Mặc định `/reload` chỉ nạp danh sách lệnh trong `AGENTS.md` và checkpoint. Các tệp tin quy tắc cục bộ (`AG_DECISION_RULES.md`, `dec-debug-playbook.md`, `regression-checklists.md`) và bài học (`AG_LESSONS.jsonl`) chỉ được nạp JIT (Just-In-Time) khi bắt đầu thực thi nhiệm vụ cụ thể qua `/br` hoặc `/pl`.
- Query `.agents/memory/AG_LESSONS.jsonl` selectively using `grep_search` to find relevant lessons instead of loading the entire file via `view_file` to conserve token quota.
- Treat uncommitted changes as user-owned. Do not clean them without explicit instructions.
- **Clean Whitelist (DEC-specific):** When running clean, always whitelist: `DATA/`, `ENGINE/`, `Tools/assets/`, and template folders.

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
- `/wsr`: load and follow `.agents/global/workflows/wsr.md`.
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

