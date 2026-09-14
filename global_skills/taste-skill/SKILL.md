---
name: frontend-design
description: Minimal frontend design guidance for new, existing, and premium web interfaces.
---

# Frontend Design

Use this single skill for normal web UI, redesign, anti-slop, and premium frontend work.

## Select one profile

- `standard`: clear, accessible, responsive HTML/CSS/JS.
- `existing-project`: preserve the current stack; make focused upgrades only.
- `premium`: stronger typography, spacing, hierarchy, and visual restraint.
- `motion`: add meaningful motion only when interaction or the brief needs it.

If the user does not specify a profile, use `standard`.

## Core rules

- Inspect the existing stack before editing.
- Prefer semantic HTML, native CSS, and existing dependencies.
- Keep the requested scope small and reviewable.
- Preserve working behavior, routes, data, and accessibility.
- Use responsive layout, readable type, visible focus, and 44px touch targets.
- Provide loading, empty, error, and disabled states when the interface needs them.
- Use one coherent palette and avoid generic AI gradients.
- Use CSS Grid for layout; avoid fragile percentage math.
- Animate `transform` and `opacity`, not layout properties.
- Respect reduced-motion preferences.

## Premium profile

Use distinctive typography, deliberate whitespace, asymmetric composition, and restrained surfaces.

Do not force a specific font, card count, hero layout, animation engine, or visual metaphor.

Do not add noise, imagery, glass, gradients, parallax, or GSAP without a concrete benefit.

## Existing-project profile

Audit first. Fix the highest-impact visual or usability issue with the smallest compatible change.

Do not migrate frameworks, add dependencies, or rewrite components without a demonstrated need.

## Motion profile

Use native CSS transitions first. Use GSAP only when the project already uses it or complexity justifies it.

Every animation needs a purpose, a reduced-motion fallback, and a performance check.

## Completion check

Verify responsive behavior, keyboard focus, contrast, real destinations, and the project test command.

Report the selected profile, changed scope, checks run, and any unresolved limitation.
