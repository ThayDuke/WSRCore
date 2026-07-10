# UltiTemp production refactor execution

Date: 2026-05-05

## Scope

- Source file: `Template/UltiTemp.html`.
- Planning artifact: `.codex/plans/ultitemp-production-refactor-execution.md`.
- Do not edit generated lesson HTML files.
- Do not externalize CSS/JS in this pass because `DukeLauncher.pyw` reads `Template/UltiTemp.html` as a standalone export template for Listening, Slide, and IPA output.

## Diagnosis

- The template is a valid source layer, not generated output.
- The file is intentionally standalone, but its internal CSS/JS sections need production hygiene.
- No HTML `style=` attributes or inline DOM event handlers were found.
- Remaining CSS issues: keyword color literals such as `white`/`transparent`, repeated non-semantic visual values, and a few control styles that should consume local DEC-compatible tokens.
- Remaining JS issues are mostly runtime measurement/animation writes via `.style.*`; these must stay dynamic. Only non-behavioral cleanup is allowed.

## Must remain unchanged

- Export compatibility with `DukeLauncher.pyw`.
- `// [DUKE PREVIEW DATA START]` and `// [DUKE PREVIEW DATA END]` markers.
- All existing `id`, class names, and DOM API hooks.
- Visual dimensions of the 900px container, card layout, progress bar, controls, IPA mode, Focus mode, game mode, and Youth/Elegant themes.
- Dynamic JS style writes used for bubble animation, drag clone movement, and Focus zoom measurement.

## Execution steps

1. Add semantic local tokens for common surfaces, transparent color, foreground-on-accent, and font weights.
2. Replace remaining CSS keyword color literals with tokens without changing computed colors.
3. Replace repeated `font-weight: bold` / raw 800 declarations with local weight tokens where safe.
4. Remove obvious duplicate or dead JS statements only if behavior is provably unchanged.
5. Verify:
   - no `style=` or inline event handlers;
   - no `dashed` / `dotted`;
   - JS extracted from template passes syntax check;
   - preview data markers remain intact;
   - `git diff` is scoped and visual values are preserved through tokens.
