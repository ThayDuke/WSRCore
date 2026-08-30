---
name: liquid-glass-web-win
description: Tạo mới (lqcr), nâng cấp (lqre), phối màu sáng/tối (lqdl), hoặc tích hợp giao diện kính mờ Liquid Glass (Apple Glassmorphism) chuẩn quang học cho Web và Windows (Tauri/Electron).
version: 1.1.0
---

# Liquid Glass Web & Windows Skill (Optical Benchmark Enhanced)

## Overview
Use this skill to implement Apple Liquid Glass aesthetics for Web applications and Windows local apps. It defines workflows for creating glassmorphism layouts with physical optical accuracy (Fresnel reflections, chromatic dispersion edges, layered shadows, Apple squircle curvature) and high-performance dark/light toggles.

---

## Workflow Decision Tree

### 1) Create a new Liquid Glass UI (`lqcr`)
- Select layout (Cards, Buttons, Navbars, Sidebars, Modals).
- Apply base CSS variables for glass materials with directional Fresnel borders and layered shadows.
- Use Apple squircle curvature for continuous organic corners.

### 2) Remaster an existing interface (`lqre`)
- Locate target containers and elements in DOM.
- Strip legacy solid background colors, borders, and heavy boxes.
- Replace with translucency, blur filters, directional Fresnel borders, and multi-tier ambient shadows.

### 3) Configure theme modes (`lqdl`)
- Declare custom properties for background colors, borders, and shadows under `:root` and `[data-theme="dark"]` (or `.dark-mode`).
- Implement seamless transition effects.

### 4) Optimize Performance (`lqpf`)
- Avoid stacking multiple nested glass components with `backdrop-filter`.
- Apply `transform: translate3d(0, 0, 0)` or `will-change` to offload rendering to the GPU.
- Implement fallbacks for older Windows browsers.

### 5) Add Dynamic Animations & Glare Angle (`lqia`)
- Add cursor-following hover effects using JS and CSS radial-gradients.
- Implement spring-like click scaling animations and dynamic glare reflections.

### 6) WebGL/Canvas Hero Extension (`lqsh`) (Optional)
- For high-impact Hero banners, Splash screens, or 3D interactive badges, use an isolated WebGL2 canvas shader with true ray refraction and dispersion without burdening standard DOM UI.

---

## Core Guidelines

1. **Material Properties**: 
   - Light Theme: Highly translucent white background, directional Fresnel border reflection, clear frosted core. Mặc định dùng kính mờ (clear), không tự động pha màu (tinted) trừ khi được chỉ định.
   - Dark Theme: Translucent dark slate/dark blue/dark gray background (tránh màu đen tuyệt đối #000000), faint Fresnel border, strong dark ambient shadow (ví dụ: dùng shadow màu tối sẫm như dark blue/slate thay vì đen).
2. **Backdrop Blur**: Use `backdrop-filter: blur(16px)` to `blur(24px)` as the core material.
3. **Directional Fresnel Borders**: Simulate real optical reflection using 135deg gradient borders (bright top-left incident light, soft vanishing bottom-right edge).
4. **Chromatic Dispersion Shadows**: Multi-layered shadow combining contact shadow, soft ambient diffusion, and an ultra-subtle chromatic fringe (optical dispersion).
5. **Apple Squircle Curvature**: Apply continuous curvature (`border-radius: 20px` with squircle geometry) instead of abrupt circular fillets.
6. **Performance**: Limit the use of `backdrop-filter` to 3 active overlay areas at once to avoid layout thrashing on Windows.
7. **No Auto Highlight**: Mặc định các card không được tự động bật highlight. Chỉ áp dụng highlight qua class hoặc chỉ định riêng.
8. **Icons**: Sử dụng icon đơn sắc, nét mảnh, không có màu sắc rực rỡ (giống phong cách icon kính lúp), trừ khi có yêu cầu cụ thể.

---

## Commands & Action Steps

### `lqcr` - Create Giao diện Liquid Glass mới
1. Define the HTML structure.
2. Link the core CSS sheet containing variables.
3. Assign the `.liquid-glass-card` class to the component.
4. Customize shapes using squircle proportions.
5. Adjust inner padding to give the glass content "room to breathe".

### `lqre` - Sửa đổi giao diện cũ sang Liquid Glass
1. Trace the parent elements that should become the glass containers.
2. Replace:
   - `background-color: #fff` -> `background: var(--lg-bg)`
   - `border: 1px solid #ccc` -> `border: 1px solid var(--lg-border)` with Fresnel overlay
   - Add `backdrop-filter: blur(var(--lg-blur))`
   - Add `box-shadow: var(--lg-shadow-combined)`
3. Group sibling cards to share the same backdrop context where possible.

### `lqdl` - Cấu hình Dark/Light theme
1. Set up standard selectors for theme switching (e.g. `body.light` / `body.dark` or `html[data-theme]`).
2. Map the variables:
   - `--lg-bg`
   - `--lg-border` / `--lg-border-fresnel`
   - `--lg-shadow-combined`
3. Add a CSS transition property: `transition: background 0.35s ease, border-color 0.35s ease, box-shadow 0.35s ease`.

### `lqsh` - Triển khai WebGL Shader Hero (Tùy chọn)
1. Use only when the project explicitly requests a standalone 3D/physics optical liquid glass canvas.
2. Mount canvas in an isolated container without affecting surrounding DOM text/forms.

---

## Quick Reference & Snippets
See the detailed implementation recipes and CSS/Shader code snippets in the [liquid-glass-web.md](references/liquid-glass-web.md) file.
