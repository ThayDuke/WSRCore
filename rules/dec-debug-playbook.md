# DEC Diagnostic Playbook

Heuristics for identifying and fixing common DEC issues. Use this for triage only.

## 1. UI vs PDF Mismatches

- **Symptom:** UI looks correct, exported PDF is broken.
- **Root Cause:** Export context uses different width/rendering assumptions than browser.
- **Fix:** Target `export/render layer` only. Group text blocks as atomic. **Never** change live UI for an export bug.

## 2. Text Wrapping & Layout

- **Symptom:** Metric cards wrap in PDF but fit on one line in UI.
- **Heuristic:** Use atomic grouping (white-space: nowrap or specific container widths) in the `@media print` or export section.
- **Suspect:** Check `zoom` or `scale` factors that might thicken borders or distort flow in export.

## 3. Theme & Shell Issues

- **Symptom:** Background outside the main container is wrong.
- **Heuristic:** Target the `body` or `root` shell layer. Check if the theme (Elegant/Youth) state is correctly propagated to the outer wrapper.
- **Regression:** Check sibling tools that share the same shell logic.

## 4. Conditional Logic in Lists

- **Symptom:** Labels appear on wrong items in a repeated list.
- **Heuristic:** Display rules must be **deterministic** (index-based or data-key based). Explicitly define the hidden state for non-matching items.

## 5. Runtime / Jitter

- **Symptom:** UI flickers or layout shifts during theme change.
- **Fix:** Disable transitions during state measurement or fit-to-screen logic. Use a "loading/pending" class to hide intermediate states.

## 6. Prompt Failure Triage

- AG says "Fixed" but nothing changed:
    - 36. **Leaf-only Edit (Sửa Ngọn):**
        - AG says "Fixed" and it works temporarily, but changes disappear after refresh/regeneration.
        - **Root Cause:** Targeted a generated file (e.g. `DukeEnglishCenter.html`) instead of the source (`Template/Dashboard.css`).
        - **Fix:** Locate the generation source/template and re-apply the fix there.
    - 37. Cache/Stale browser view.
    - 38. Missing `!important` in CSS where shared themes override local styles.
    - 39. **Hardcode Violation:** Sử dụng giá trị số trực tiếp (`500`, `#ccc`) thay vì Token `var(--)`. Bắt buộc refactor sang Token ngay khi phát hiện.

---
*Refer to [AG_DECISION_RULES.md](AG_DECISION_RULES.md) for action protocols.*