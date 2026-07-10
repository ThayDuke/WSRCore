# CSS & JS Recipes for Liquid Glass on Web and Windows (v1.0.1)

This reference sheet provides copy-pasteable CSS patterns and JavaScript scripts for creating, remastering, and theme-managing Liquid Glass interfaces.

---

## 1. CSS Design System Variables (`lqdl`)

Apply this base CSS file to establish the theme properties. It supports standard dark/light mode switching via a `data-theme` attribute on the `<html>` or `<body>` element.

```css
:root {
  /* Light Mode - Frosty Apple Glass (Mặc định kính mờ clear) */
  --lg-bg: rgba(255, 255, 255, 0.4);
  --lg-bg-prominent: rgba(255, 255, 255, 0.65);
  --lg-border: rgba(255, 255, 255, 0.45);
  --lg-border-prominent: rgba(255, 255, 255, 0.6);
  --lg-blur: 16px;
  --lg-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.08),
               inset 0 1px 1px 0 rgba(255, 255, 255, 0.3);
  --lg-text: #1d1d1f;
  --lg-tint-color: rgba(59, 130, 246, 0.05); /* Chỉ dùng khi người dùng chỉ định tinted */
}

[data-theme="dark"] {
  /* Dark Mode - Obsidian Liquid Glass (Không dùng màu đen tuyệt đối #000000) */
  --lg-bg: rgba(15, 23, 42, 0.45); /* Màu tối sẫm (dark slate) */
  --lg-bg-prominent: rgba(30, 41, 59, 0.6);
  --lg-border: rgba(255, 255, 255, 0.08);
  --lg-border-prominent: rgba(255, 255, 255, 0.15);
  --lg-blur: 20px;
  --lg-shadow: 0 12px 40px 0 rgba(15, 23, 42, 0.4), /* Dùng màu tối sẫm thay vì đen tuyệt đối */
               inset 0 1px 0px 0 rgba(255, 255, 255, 0.1);
  --lg-text: #f5f5f7;
  --lg-tint-color: rgba(139, 92, 246, 0.05);
}

/* Smooth Transitions */
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
/* Base Container / Card (Clear by default in light mode) */
.liquid-glass-card {
  background: var(--lg-bg);
  backdrop-filter: blur(var(--lg-blur));
  -webkit-backdrop-filter: blur(var(--lg-blur));
  border: 1px solid var(--lg-border);
  box-shadow: var(--lg-shadow);
  border-radius: 16px;
  color: var(--lg-text);
  padding: 24px;
}

/* Tinted variant (Optional, only when tinted effect is specified) */
.liquid-glass-card-tinted {
  background: linear-gradient(
    135deg, 
    var(--lg-bg), 
    var(--lg-tint-color)
  );
}

/* Optional Highlight variant (Not applied by default) */
.liquid-glass-card-highlight {
  border-color: var(--lg-border-prominent);
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.15), var(--lg-shadow);
}

/* Prominent variant (Modals, Active states) */
.liquid-glass-card-prominent {
  background: var(--lg-bg-prominent);
  backdrop-filter: blur(calc(var(--lg-blur) + 4px));
  -webkit-backdrop-filter: blur(calc(var(--lg-blur) + 4px));
  border: 1px solid var(--lg-border-prominent);
  box-shadow: var(--lg-shadow);
}

/* Glass Buttons style */
.liquid-glass-btn {
  background: var(--lg-bg);
  border: 1px solid var(--lg-border);
  color: var(--lg-text);
  padding: 10px 20px;
  border-radius: 9999px;
  font-weight: 500;
  cursor: pointer;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05); /* Tránh màu đen tuyệt đối */
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.liquid-glass-btn:hover {
  transform: translateY(-1px);
  background: var(--lg-bg-prominent);
  border-color: var(--lg-border-prominent);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1);
}

.liquid-glass-btn:active {
  transform: translateY(1px);
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.05);
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
  opacity: 0.7;
  transition: all 0.25s ease;
}

.liquid-glass-icon:hover {
  opacity: 1;
  stroke: var(--lg-accent-color, #3b82f6); /* Đơn sắc khi active/hover */
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
  
  /* Apply Liquid variables (Clear by default) */
  background: var(--lg-bg);
  backdrop-filter: blur(var(--lg-blur));
  -webkit-backdrop-filter: blur(var(--lg-blur));
  border: 1px solid var(--lg-border);
  box-shadow: var(--lg-shadow);
  
  /* Keep layout properties */
  border-radius: 16px;
  padding: 24px;
}

/* Tinted variant if specified */
.card-legacy-remastered-tinted {
  background-image: linear-gradient(
    135deg, 
    var(--lg-bg), 
    var(--lg-tint-color)
  );
}
```

---

## 4. Advanced Interaction: Mouse Cursor Glow (`lqia`)

To create the illusion of light passing through the glass element as the user moves their mouse, attach this JavaScript listener to the glass elements.

### JavaScript:
```javascript
document.querySelectorAll('.liquid-glass-glow').forEach(element => {
  element.addEventListener('mousemove', e => {
    const rect = element.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    element.style.setProperty('--mouse-x', `${x}px`);
    element.style.setProperty('--mouse-y', `${y}px`);
  });
});
```

### CSS:
```css
.liquid-glass-glow {
  position: relative;
  overflow: hidden;
}

.liquid-glass-glow::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(
    300px circle at var(--mouse-x, 0px) var(--mouse-y, 0px),
    rgba(255, 255, 255, 0.15),
    transparent 80%
  );
  z-index: 1;
  pointer-events: none;
  transition: opacity 0.5s ease;
  opacity: 0;
}

.liquid-glass-glow:hover::before {
  opacity: 1;
}
```

---

## 5. Performance Optimization Checklist (`lqpf`)

To prevent performance lag and CPU spike on Windows machines:
1. **Never Nest Blurs**: If a child element is inside a `.liquid-glass-card`, do not apply `backdrop-filter` to the child. Let the parent blur the background.
2. **GPU Acceleration Trigger**: Add `will-change: backdrop-filter, transform` to elements undergoing animations or scrolls.
3. **Static Fallback**: Detect browsers that struggle with backdrop filters and fallback gracefully:
   ```css
   @supports not (backdrop-filter: blur(1px)) {
     .liquid-glass-card {
       background: rgba(255, 255, 255, 0.95); /* Fallback to mostly solid */
     }
   }
   ```
