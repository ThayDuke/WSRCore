# Regression Checklists

Use these checklists after proposing or applying a DEC fix.

Do not dump a long checklist by default. Select only the checks that match the issue.

## 1. Minimal verification model

Prefer this order:

1. target fix works
2. unrelated behavior remains unchanged
3. shared siblings are not broken

Use more checks only when the issue is clearly shared or high risk.

## 2. Universal compact checklist

Use this when a short checklist is enough:

- confirm the original issue is resolved
- confirm unrelated UI/layout did not change
- confirm logic/data behavior still matches before
- confirm no new export/render issue was introduced

## 3. UI/layout fix checklist

Use when the issue is in live UI only:

- affected element now renders as expected
- spacing/alignment is correct in the affected area
- neighboring elements did not shift unexpectedly
- no duplicate or missing controls were introduced
- tool variant still matches its intended design style

## 4. PDF/export fix checklist

Use when the issue is export-specific:

- exported artifact now matches expected behavior
- live UI remains unchanged
- nearby export content still aligns correctly
- hidden interactive-only elements are still excluded
- no new wrapping, clipping, or spacing regressions appear in adjacent sections

## 5. Conditional-logic fix checklist

Use when labels, badges, repeated items, or conditional sections are involved:

- target condition now applies only where intended
- non-matching items render without the target label/section
- item order and data mapping remain correct
- no duplicated or missing items appear
- stale state is not causing old behavior to persist

## 6. Theme/shell consistency checklist

Use when the issue affects outer background, shell, or shared styling:

- target tool now matches the intended shell/theme behavior
- inner content layout remains unchanged unless explicitly intended
- sibling tools sharing the same shell/theme still look correct
- dark/light or elegant/youth variants remain consistent with their intended rules

## 7. Shared-component checklist

Use when the likely source is shared:

- original issue is resolved in the source tool
- closest sibling tool using the same component still behaves correctly
- no one-off override is masking a deeper shared problem
- the fix is applied at the right abstraction level

## 8. “Previous fix did not work” checklist

Use after a second attempt:

- confirm the correct surface was targeted this time
- confirm the exact artifact with the original bug is now clean
- confirm the previous wrong-path fix did not introduce side effects
- confirm scope was kept narrow

## 9. Escalation signals

Escalate to a broader review when:

- the same issue appears across multiple tools
- the problem involves shell/background/theme rules
- the fix only works in UI but not export, or vice versa
- repeated attempts fail with no visible change
- evidence suggests a shared component or shared render path

## 10. Output preference

When giving a checklist to the user:
- keep it short
- include only relevant checks
- prioritize target fix, collateral safety, and shared-risk checks
