---
name: liquid-glass-web-win
description: Create (lqcr), remaster (lqre), or add dark-light theme modes (lqdl) for Liquid Glass interfaces on Web (HTML/JS/CSS) and Windows local apps (Tauri/Electron) - Version 1.0.1.
version: 1.0.1
---

# Liquid Glass Web & Windows Skill

## Overview
Use this skill to implement Apple Liquid Glass aesthetics for Web applications and Windows local apps. It defines specific workflows for creating brand new glassmorphism layouts, remastering legacy designs into glass layouts, and configuring high-performance dark/light toggles.

---

## Workflow Decision Tree

### 1) Create a new Liquid Glass UI (`lqcr`)
- Select layout (Cards, Buttons, Navbars, Sidebars, Modals).
- Apply base CSS variables for glass materials.
- Set up responsive layouts and clean shadow fallbacks.

### 2) Remaster an existing interface (`lqre`)
- Locate target containers and elements in DOM.
- Strip legacy solid background colors, borders, and heavy boxes.
- Replace with translucency, blur filters, and thin borders.

### 3) Configure theme modes (`lqdl`)
- Declare custom properties for background colors, borders, and shadows under `:root` and `[data-theme="dark"]` (or `.dark-mode`).
- Implement seamless transition effects.

### 4) Optimize Performance (`lqpf`)
- Avoid stacking multiple nested glass components with `backdrop-filter`.
- Apply `transform: translate3d(0, 0, 0)` or `will-change` to offload rendering to the GPU.
- Implement fallbacks for older Windows browsers.

### 5) Add Dynamic Animations (`lqia`)
- Add cursor-following hover effects using JS and CSS radial-gradients.
- Implement spring-like click scaling animations.

---

## Core Guidelines

1. **Material Properties**: 
   - Light Theme: Highly translucent white background, thick white border reflection, medium shadow. Mặc định dùng kính mờ (clear), không tự động pha màu (tinted) trừ khi được chỉ định.
   - Dark Theme: Translucent dark slate/dark blue/dark gray background (tránh màu đen tuyệt đối #000000), faint border, strong dark shadow (ví dụ: dùng shadow màu tối sẫm như dark blue/slate thay vì đen).
2. **Backdrop Blur**: Use `backdrop-filter: blur(12px)` to `blur(20px)` as the core material.
3. **Double borders**: To simulate light reflection, use a 1px border with a semi-transparent gradient, or an inner box-shadow.
4. **Performance**: Limit the use of `backdrop-filter` to 3 active overlay areas at once to avoid layout thrashing on Windows.
5. **No Auto Highlight**: Mặc định các card không được tự động bật highlight. Chỉ áp dụng highlight qua class hoặc chỉ định riêng.
6. **Icons**: Sử dụng icon đơn sắc, nét mảnh, không có màu sắc rực rỡ (giống phong cách icon kính lúp), trừ khi có yêu cầu cụ thể.

---

## Commands & Action Steps

### `lqcr` - Create Giao diện Liquid Glass mới
1. Define the HTML structure.
2. Link the core CSS sheet containing variables.
3. Assign the `.liquid-glass` class to the component.
4. Customize shapes using `border-radius`.
5. Adjust inner padding to give the glass content "room to breathe".

### `lqre` - Sửa đổi giao diện cũ sang Liquid Glass
1. Trace the parent elements that should become the glass containers.
2. Replace:
   - `background-color: #fff` -> `background: var(--lg-bg)`
   - `border: 1px solid #ccc` -> `border: 1px solid var(--lg-border)`
   - Add `backdrop-filter: blur(var(--lg-blur))`
   - Add `box-shadow: var(--lg-shadow)`
3. Group sibling cards to share the same backdrop context where possible.

### `lqdl` - Cấu hình Dark/Light theme
1. Set up standard selectors for theme switching (e.g. `body.light` / `body.dark` or `html[data-theme]`).
2. Map the variables:
   - `--lg-bg`
   - `--lg-border`
   - `--lg-shadow`
3. Add a CSS transition property: `transition: background 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease`.

---

## Quick Reference & Snippets
See the detailed implementation recipes and CSS code snippets in the [liquid-glass-web.md](references/liquid-glass-web.md) file.
