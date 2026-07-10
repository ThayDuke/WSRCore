# AdaptiveTemp Refactor Plan

## Pham vi

- Operational Mode: Isolation.
- Failure Layer: UI runtime + adaptive report/export template boundary.
- File nguon chinh: `Template/AdaptiveTemp.html`.
- Must remain unchanged: UI/UX Adaptive, Youth/Elegant theme, Focus mode, keyboard shortcuts, injectedAdaptiveMeta/injectedAdaptiveConfig contract, PDF/report render.

## Danh gia hien trang

- `Template/AdaptiveTemp.html` gom HTML, CSS va JS trong mot file lon khoang 99 KB.
- `ENGINE/launcher_modules/adaptive_api.py` doc template de tao runtime page.
- `ENGINE/launcher_modules/adaptive_report.py` doc template de tao report/PDF HTML.
- Template co hai marker config quan trong: `injectedAdaptiveMeta` va `injectedAdaptiveConfig`.
- Khong phat hien duplicate function runtime trong audit tinh.

## Chien luoc refactor an toan

1. Giu checkpoint UltiTemp rieng truoc khi sua Adaptive.
2. Tach module nguon duoi `Template/AdaptiveTemp/`:
   - `shell.html`
   - `styles.css`
   - `runtime.js`
3. Them helper `ENGINE/launcher_modules/adaptive_template.py` de build inline template trong memory.
4. Them builder `Tools/DevTool/build_adaptive_template.py` de extract/build/check.
5. Chuyen `adaptive_api.py` va `adaptive_report.py` sang dung inline template truoc khi inject config.
6. Build `Template/AdaptiveTemp.html` thanh shell nhe, giu output runtime/report portable.
7. Chay regression checks: build parity, Python compile, JS syntax, injected marker count, injection regex, duplicate function audit.

## Nguyen tac thuc hien

- Khong doi layout, selector, copy UI, theme token hoac logic cham diem neu khong can.
- Khong inject config vao shell nhe truc tiep; luon inject vao inline build.
- Khong sua output/report generated truc tiep.

## Ket qua thuc thi

- Da tach source module:
  - `Template/AdaptiveTemp/shell.html`
  - `Template/AdaptiveTemp/styles.css`
  - `Template/AdaptiveTemp/runtime.js`
- Da them `ENGINE/launcher_modules/adaptive_template.py` de build inline template trong memory.
- Da them `Tools/DevTool/build_adaptive_template.py` de extract/build/check template.
- Da build `Template/AdaptiveTemp.html` thanh shell nhe tham chieu module source.
- Da cap nhat `ENGINE/launcher_modules/adaptive_api.py` va `ENGINE/launcher_modules/adaptive_report.py` de dung inline template truoc khi inject config/report.
- Dung luong `Template/AdaptiveTemp.html` sau refactor: khoang 6.2 KB; inline template build trong memory: khoang 99 KB.

## Regression checks da chay

- `python Tools/DevTool/build_adaptive_template.py check`
- `python -m py_compile Tools/DevTool/build_adaptive_template.py ENGINE/launcher_modules/adaptive_template.py ENGINE/launcher_modules/adaptive_api.py ENGINE/launcher_modules/adaptive_report.py DukeLauncher.pyw`
- `node --check Template/AdaptiveTemp/runtime.js`
- Audit duplicate function trong `Template/AdaptiveTemp/runtime.js`.
- Smoke inline build + marker count cho `injectedAdaptiveMeta` va `injectedAdaptiveConfig`.
- Smoke `adaptive_report.replace_adaptive_template_sections()` tren inline template.
- Mojibake byte-pattern guard cho `Template/AdaptiveTemp.html`.
