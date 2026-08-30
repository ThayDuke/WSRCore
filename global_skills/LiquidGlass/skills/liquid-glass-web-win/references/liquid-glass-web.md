# CSS & WebGL Recipes for Liquid Glass on Web and Windows (v1.1.0)

This reference sheet provides copy-pasteable CSS patterns and optional WebGL shader snippets for creating, remastering, and theme-managing physically grounded Liquid Glass interfaces.

---

## 1. CSS Design System Variables (`lqdl`)

Apply this base CSS file to establish the theme properties. It supports standard dark/light mode switching via a `data-theme` attribute on the `<html>` or `<body>` element.

```css
:root {
  /* Light Mode - Frosty Apple Glass (Mặc định kính mờ clear) */
  --lg-bg: rgba(255, 255, 255, 0.45);
  --lg-bg-prominent: rgba(255, 255, 255, 0.70);
  --lg-blur: 20px;
  
  /* Directional Fresnel Border (Sáng góc 135 độ trên-trái, tắt mép dưới-phải) */
  --lg-border-color: rgba(255, 255, 255, 0.5);
  --lg-border-fresnel: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.75) 0%,
    rgba(255, 255, 255, 0.25) 45%,
    rgba(255, 255, 255, 0.05) 100%
  );
  
  /* Layered Optical Shadow (Contact + Ambient + Chromatic Edge Dispersion) */
  --lg-shadow-contact: 0 2px 4px rgba(15, 23, 42, 0.04);
  --lg-shadow-ambient: 0 12px 32px -4px rgba(31, 38, 135, 0.08);
  --lg-shadow-chromatic: 0 0 20px rgba(59, 130, 246, 0.04), 0 0 40px rgba(236, 72, 153, 0.02);
  --lg-shadow-inner: inset 0 1px 1px 0 rgba(255, 255, 255, 0.6), inset 0 -1px 1px 0 rgba(0, 0, 0, 0.02);
  --lg-shadow-combined: var(--lg-shadow-contact), var(--lg-shadow-ambient), var(--lg-shadow-chromatic), var(--lg-shadow-inner);
  
  --lg-text: #0f172a;
  --lg-text-secondary: #475569;
  --lg-tint-color: rgba(59, 130, 246, 0.05); /* Chỉ dùng khi người dùng chỉ định tinted */
  --lg-radius-squircle: 20px;
}

[data-theme="dark"] {
  /* Dark Mode - Obsidian Liquid Glass (Không dùng màu đen tuyệt đối #000000) */
  --lg-bg: rgba(15, 23, 42, 0.50); /* Màu tối sẫm dark slate */
  --lg-bg-prominent: rgba(30, 41, 59, 0.65);
  --lg-blur: 24px;
  
  /* Directional Fresnel Border for Dark Mode */
  --lg-border-color: rgba(255, 255, 255, 0.10);
  --lg-border-fresnel: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.22) 0%,
    rgba(255, 255, 255, 0.06) 50%,
    rgba(255, 255, 255, 0.01) 100%
  );
  
  /* Layered Optical Shadow for Dark Mode */
  --lg-shadow-contact: 0 2px 6px rgba(0, 0, 0, 0.25);
  --lg-shadow-ambient: 0 16px 48px -8px rgba(2, 6, 23, 0.65);
  --lg-shadow-chromatic: 0 0 24px rgba(99, 102, 241, 0.05), 0 0 48px rgba(168, 85, 247, 0.03);
  --lg-shadow-inner: inset 0 1px 0px 0 rgba(255, 255, 255, 0.15), inset 0 -1px 0px 0 rgba(0, 0, 0, 0.3);
  --lg-shadow-combined: var(--lg-shadow-contact), var(--lg-shadow-ambient), var(--lg-shadow-chromatic), var(--lg-shadow-inner);
  
  --lg-text: #f8fafc;
  --lg-text-secondary: #94a3b8;
  --lg-tint-color: rgba(139, 92, 246, 0.06);
  --lg-radius-squircle: 20px;
}

/* Smooth Optical Transitions */
.liquid-glass-transition {
  transition: background 0.35s cubic-bezier(0.25, 0.8, 0.25, 1),
              border-color 0.35s cubic-bezier(0.25, 0.8, 0.25, 1),
              box-shadow 0.35s cubic-bezier(0.25, 0.8, 0.25, 1),
              backdrop-filter 0.35s ease;
}
```

---

## 2. Core Liquid Glass Utility Classes (`lqcr`)

Apply these base classes to create different elements of Liquid Glass:

```css
/* Base Container / Card with Fresnel Border Simulation */
.liquid-glass-card {
  position: relative;
  background: var(--lg-bg);
  backdrop-filter: blur(var(--lg-blur));
  -webkit-backdrop-filter: blur(var(--lg-blur));
  border: 1px solid transparent;
  background-clip: padding-box;
  box-shadow: var(--lg-shadow-combined);
  border-radius: var(--lg-radius-squircle);
  color: var(--lg-text);
  padding: 24px;
}

/* Pseudo-element for pure continuous Fresnel Gradient border */
.liquid-glass-card::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: calc(var(--lg-radius-squircle) + 1px);
  padding: 1px;
  background: var(--lg-border-fresnel);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

/* Tinted variant (Optional, only when tinted effect is specified) */
.liquid-glass-card-tinted {
  background: linear-gradient(
    135deg, 
    var(--lg-bg), 
    var(--lg-tint-color)
  );
  background-clip: padding-box;
}

/* Optional Highlight variant (Not applied by default) */
.liquid-glass-card-highlight {
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.2), var(--lg-shadow-combined);
}

/* Prominent variant (Modals, Active states) */
.liquid-glass-card-prominent {
  background: var(--lg-bg-prominent);
  backdrop-filter: blur(calc(var(--lg-blur) + 6px));
  -webkit-backdrop-filter: blur(calc(var(--lg-blur) + 6px));
  box-shadow: var(--lg-shadow-combined);
}

/* Glass Buttons style */
.liquid-glass-btn {
  position: relative;
  background: var(--lg-bg);
  border: 1px solid var(--lg-border-color);
  color: var(--lg-text);
  padding: 10px 22px;
  border-radius: 9999px;
  font-weight: 500;
  cursor: pointer;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: var(--lg-shadow-contact), var(--lg-shadow-inner);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.liquid-glass-btn:hover {
  transform: translateY(-1px);
  background: var(--lg-bg-prominent);
  box-shadow: var(--lg-shadow-contact), var(--lg-shadow-ambient), var(--lg-shadow-inner);
}

.liquid-glass-btn:active {
  transform: translateY(1px);
  box-shadow: var(--lg-shadow-contact);
}

/* Monochrome Thin-outline Icons (giống phong cách icon kính lúp) */
.liquid-glass-icon {
  fill: none;
  stroke: var(--lg-text);
  stroke-width: 1.5; /* Nét mảnh */
  stroke-linecap: round;
  stroke-linejoin: round;
  width: 20px;
  height: 20px;
  opacity: 0.75;
  transition: all 0.25s ease;
}

.liquid-glass-icon:hover {
  opacity: 1;
  stroke: var(--lg-accent-color, #3b82f6);
}
```

---

## 3. Remastering Legacy Containers (`lqre`)

Follow this CSS pattern to clean up legacy layouts and overlay glass attributes.

### Before (Legacy solid layout):
```css
.card-legacy {
  background-color: #ffffff;
  border: 1px solid #e0e0e0;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}
```

### After (Remastered Liquid Glass):
```css
.card-legacy-remastered {
  /* Remove solid backgrounds */
  background-color: transparent;
  
  /* Apply Liquid variables */
  background: var(--lg-bg);
  backdrop-filter: blur(var(--lg-blur));
  -webkit-backdrop-filter: blur(var(--lg-blur));
  border: 1px solid var(--lg-border-color);
  box-shadow: var(--lg-shadow-combined);
  
  /* Keep layout properties with Apple Squircle radius */
  border-radius: var(--lg-radius-squircle);
  padding: 24px;
}
```

---

## 4. Advanced Interaction: Dynamic Glare Angle & Glow (`lqia`)

Simulate optical light reflection moving across the surface as the cursor moves:

### JavaScript:
```javascript
document.querySelectorAll('.liquid-glass-glow').forEach(element => {
  element.addEventListener('mousemove', e => {
    const rect = element.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Normalized light angle (-1 to 1)
    const angleX = ((x / rect.width) - 0.5) * 2;
    const angleY = ((y / rect.height) - 0.5) * 2;
    
    element.style.setProperty('--mouse-x', `${x}px`);
    element.style.setProperty('--mouse-y', `${y}px`);
    element.style.setProperty('--glare-tilt', `${angleX * 15}deg`);
  });
});
```

### CSS:
```css
.liquid-glass-glow {
  position: relative;
  overflow: hidden;
}

.liquid-glass-glow::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(
    280px circle at var(--mouse-x, 0px) var(--mouse-y, 0px),
    rgba(255, 255, 255, 0.18),
    transparent 75%
  );
  z-index: 1;
  pointer-events: none;
  transition: opacity 0.4s ease;
  opacity: 0;
}

.liquid-glass-glow:hover::after {
  opacity: 1;
}
```

---

## 5. Performance Optimization Checklist (`lqpf`)

To prevent performance lag and CPU spikes on Windows machines:
1. **Never Nest Blurs**: If a child element is inside a `.liquid-glass-card`, do not apply `backdrop-filter` to the child. Let the parent blur the background.
2. **GPU Acceleration Trigger**: Add `will-change: backdrop-filter, transform` to elements undergoing animations or scrolls.
3. **Hardware Fallback**:
   ```css
   @supports not (backdrop-filter: blur(1px)) {
     .liquid-glass-card {
       background: rgba(255, 255, 255, 0.95); /* Fallback to solid */
     }
   }
   ```

---

## 6. Optional Standalone WebGL2 Hero Canvas (`lqsh`)

When the user explicitly asks for an interactive 3D liquid refraction hero banner, use this zero-dependency vanilla WebGL2 canvas snippet:

```javascript
// Standalone Liquid Glass WebGL2 Canvas Boilerplate (Zero dependencies)
export function initLiquidGlassHero(canvasElement) {
  const gl = canvasElement.getContext('webgl2');
  if (!gl) return;

  const vsSource = `#version 300 es
    in vec2 position;
    out vec2 vUv;
    void main() {
      vUv = position * 0.5 + 0.5;
      gl_Position = vec4(position, 0.0, 1.0);
    }
  `;

  // Fragment shader computing ray refraction + chromatic dispersion (RGB offset)
  const fsSource = `#version 300 es
    precision highp float;
    in vec2 vUv;
    out vec4 fragColor;
    uniform vec2 uResolution;
    uniform vec2 uMouse;
    uniform float uTime;

    // Superellipse SDF function
    float sdSquircle(vec2 p, vec2 r, float n) {
      vec2 d = abs(p);
      return pow(pow(d.x / r.x, n) + pow(d.y / r.y, n), 1.0 / n) - 1.0;
    }

    void main() {
      vec2 p = (gl_FragCoord.xy * 2.0 - uResolution) / min(uResolution.x, uResolution.y);
      vec2 m = (uMouse * 2.0 - uResolution) / min(uResolution.x, uResolution.y);
      
      float d = sdSquircle(p - m * 0.2, vec2(0.55, 0.35), 4.0);
      float edge = smoothstep(0.01, -0.01, d);
      
      // Chromatic dispersion offsets (RGB refraction channels)
      vec3 col = vec3(0.0);
      col.r = smoothstep(0.015, -0.015, d - 0.008);
      col.g = smoothstep(0.010, -0.010, d);
      col.b = smoothstep(0.005, -0.005, d + 0.008);
      
      fragColor = vec4(col * 0.4 + vec3(0.95) * edge * 0.15, edge * 0.85);
    }
  `;

  // Compile, link quad and render loop...
}
```
