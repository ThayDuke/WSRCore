# DEC Codex Knowledge Layout

This directory is the project-local Codex knowledge base for DEC.

## Canonical Sources

- `DOCS/WSR-Duke-All-2.3.9`: generic WSR source package.
- `DOCS/WSR-DEC`: DEC-specific WSR source package.

## Codex Mapping

- `global/GEMINI.md`: global operating instructions snapshot.
- `global/rules/`: global rules imported from WSR-Duke.
- `global/workflows/`: slash workflows imported from WSR-Duke.
- `skills/output-skill/`: strict output completion skill.
- `skills/redesign-skill/`: existing UI redesign skill.
- `skills/soft-skill/`: high-end new UI design skill.
- `skills/stitch-skill/`: Stitch DESIGN.md skill and reference.
- `skills/dec-dev-operator/`: DEC local operator skill.
- `rules/`: DEC decision rules, debug playbook, prompt patterns, regression checks.
- `scripts/`: DEC support scripts used by workflows.
- `memory/AG_LESSONS.jsonl`: reusable lessons and observed fixes.
- `memory/project_checkpoint.yaml`: latest project WSR checkpoint.
- `metadata.json`: version and ownership metadata.
- `CHANGELOG.md`: historical change log.

## Active Rule

Treat `.codex/` plus root `AGENTS.md` as the Codex-native memory for this
project. Treat the two `DOCS/WSR-*` folders as import/export source packages.
