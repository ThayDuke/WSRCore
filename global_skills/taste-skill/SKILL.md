---
name: design-taste-frontend
description: Anti-slop frontend skill for landing pages, portfolios, and redesigns. Infers design brief, dials VARIANCE/MOTION/DENSITY, enforces GSAP motion, and applies strict anti-slop pre-flight checks.
---

# Taste Skill (v2 Anti-Slop Frontend Engine)

> Applied to landing pages, portfolios, redesigns, and marketing sites.
> Detailed GSAP skeletons, typography matrices, and design system maps are in `references/taste-skill-guide.md`.

## 0. Brief Inference & Design Read

Before generating code or tweaking parameters, declare a one-line **Design Read**:
- **Format:** `"Reading this as: <page kind> for <audience>, with a <vibe> language, leaning toward <design system or aesthetic family>."`
- **Signals:** Page kind (landing, portfolio, redesign), vibe keywords (calm, linear, awwwards, luxury, dark-tech), existing brand assets, and audience context.
- **Rule:** If brief is clear, declare the read and proceed immediately. Never ask multiple dump questions.

## 1. The Three Dials Configuration

Tune the 3 core dials based on the design read:
- **`DESIGN_VARIANCE: 8`** (1 = Perfect Symmetry, 10 = Artsy Chaos)
- **`MOTION_INTENSITY: 6`** (1 = Static, 10 = Cinematic / Physics)
- **`VISUAL_DENSITY: 4`** (1 = Airy / Gallery, 10 = Cockpit / Packed Data)
- **Baseline Default:** `8 / 6 / 4`. (Linear-style uses `6 / 4 / 3`, Awwwards-style uses `9 / 8 / 3`).

## 2. Anti-Slop Hard Bans (Zero Tolerance)

1. **Em-Dash Ban:** Never use long em-dashes (`—`) in headings or marketing copy. Use colons, periods, or clean whitespace.
2. **AI Defaults Ban:** Never default to purple radial mesh gradients, centered hero over dark blob, 3 equal-width cards, infinite-loop micro-wiggles, or plain Inter + slate-900.
3. **Typography Rule:** Use high-character font pairs (Display serif/sans + clean body mono/sans). Avoid 6-line text wraps on large screens.
4. **Layout Rule:** Vary section layouts. Mix asymmetric bento grids (8+4, 7+5, 5+7) with full-bleed hero components.
5. **Motion Rule:** Use hardware-accelerated transforms (`transform`, `opacity`). Anchor scroll effects to GSAP ScrollTrigger with pinning and scrubbing.

## 3. Pre-Flight Verification Checklist

Before shipping any frontend output, verify:
- [ ] Stated the one-line Design Read and dial settings.
- [ ] Zero unprompted em-dashes in copy.
- [ ] No generic 3-card-in-a-row layout unless explicitly requested.
- [ ] Spacing scale is generous (section padding >= 80px on desktop).
- [ ] Interactive states (hover, focus, active) have smooth transitions (150-250ms).
- [ ] For complex GSAP motion skeletons or full design-system tokens, consult `references/taste-skill-guide.md`.
