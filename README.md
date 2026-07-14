# WSR Core

WSR is a lightweight, high-performance, and secure Agentic Workflow framework designed for AI coding assistants (such as Gemini, Claude, Cursor, and Antigravity). It restricts AI from making arbitrary changes (Iron Rule), prevents over-engineering (YAGNI & Native-first), and optimizes context usage (Anti-Waste) through telegraphic rules and automated CLI scripts.

This directory contains the independent standalone version of **WSR Core**, ready to be initialized as a submodule or an independent repository.

---

## 1. Core Architecture

WSR functions by deploying specific components into the `.agents/` (canonical) or `.codex/` (fallback) folder at the root of a target repository:

```
.agents/ (or WSR Release Package)
├── adapters/             # Environment & model mappings for Cursor, Gemini, Claude, etc.
├── global_rules/         # Core coding principles (YAGNI, Minimal Coding, Risk Gate)
├── global_skills/        # Reusable instruction bundles (Brutalist, Liquid Glass, Output Enforcement)
├── global_workflows/     # Step-by-step markdown workflows triggered by slash commands
├── scripts/              # Python utilities for automation, audits, and health diagnostics
├── debt_ledger.md        # Technical debt ledger tracking tag triggers
├── WSR_MANIFEST.json     # Master configuration index specifying active rules and files
└── WSR_CHECKSUMS.json    # SHA-256 integrity mapping to protect against file corruption
```

---

## 2. Standard Slash Commands

When an AI agent is initialized with WSR, it responds to the following standardized workflows:

- **`/br` (Brainstorm):** Default chat mode. Analyzes system layer requirements and presents solutions. **Direct code modification is strictly forbidden.**
- **`/pl` (Planning):** Creates a design plan at `DOCS/Planning/planning_[task_name].md` and halts. AI must wait for explicit user approval before execution.
- **`/audit` (Quality Audit):** Runs `wsr_audit.py` on modified files to verify syntax structure and prevent UTF-8 mojibake.
- **`/clean` (Clean Room):** Triggers `wsr_clean.py` to scan the workspace and safely purge obsolete plans, temp files, and build cache.
- **`/wsr` (Package Release):** Runs `pack_wsr.py` to bump versioning metadata, update HTML documentation, and archive WSR into a distribution `.zip`.
- **`/reload` (Hot Reload):** Re-evaluates local rules, active skills, and lessons learned without clearing conversation history.

---

## 3. Automation Scripts (`scripts/`)

WSR includes a suite of robust CLI scripts to manage the developer-agent interaction:

1. **`wsr_audit.py`:** Performs static code auditing. Checks for syntax validity, removes unresolved placeholders, and scans for character encoding issues.
2. **`wsr_debt_scanner.py`:** Scans files for technical debt triggers (e.g., `# wsr-debt:` comments) and logs them into `debt_ledger.md`.
3. **`wsr_clean.py`:** Parses rules to locate and wipe redundant markdown files, old planning states, and lockfiles.
4. **`wsr_doctor.py`:** Performs system diagnostic checks on active rule paths and resolves mojibake errors.
5. **`sync_config.py`:** Integrates global rules into local IDE presets.

---

## 4. How to Deploy

To install WSR in any workspace:

1. **Copy the Package:** Clone or copy this WSR package into the `.agents/` folder at the root of your target project.
2. **Synchronize System Config:** Execute the sync script to bind active adapter policies to your local developer workspace:
   ```bash
   python .agents/scripts/sync_config.py --apply
   ```
3. **Verify Integrity:** Run the system diagnosis tool to verify that all modules are mapped correctly:
   ```bash
   python .agents/scripts/wsr_doctor.py
   ```
4. **Start Coding:** Prompt your AI assistant. It will auto-detect `.agents/GEMINI.md` and inherit all rules.
