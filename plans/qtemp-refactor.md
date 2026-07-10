# QTemp Refactor Plan

## Pham vi

- Operational Mode: Isolation.
- Failure Layer: quiz export/remaster template boundary.
- File nguon chinh: `Template/QTemp.html`.
- Must remain unchanged: UI/UX quiz, Youth/Elegant theme, navigation/submit/reset behavior, `fullQuestionBank` injection contract, generated standalone quiz HTML.

## Danh gia hien trang

- `Template/QTemp.html` gom HTML, CSS va JS trong mot file lon khoang 55 KB.
- `/generate_quiz` trong `DukeLauncher.pyw` doc truc tiep template va inject title, `TOTAL_QUESTIONS`, `fullQuestionBank`.
- `Tools/DevTool/Remaster/remasterQTemp.py` doc truc tiep template va inject title + question bank.
- Template co preview block va marker quan trong `const fullQuestionBank =`.
- Audit tinh khong phat hien duplicate function runtime.

## Chien luoc refactor an toan

1. Giu checkpoint AdaptiveTemp rieng truoc khi sua QTemp.
2. Tach module nguon duoi `Template/QTemp/`:
   - `shell.html`
   - `styles.css`
   - `runtime.js`
3. Them helper `ENGINE/launcher_modules/qtemp_template.py` de build inline template trong memory.
4. Them builder `Tools/DevTool/build_qtemp_template.py` de extract/build/check.
5. Chuyen `DukeLauncher.pyw` va `remasterQTemp.py` sang dung inline template truoc khi inject bank.
6. Build `Template/QTemp.html` thanh shell nhe, giu output quiz portable.
7. Chay regression checks: build parity, Python compile, JS syntax, marker count, injection smoke, duplicate function audit.

## Nguyen tac thuc hien

- Khong doi layout, selector, copy UI, theme token hoac quiz behavior neu khong can.
- Khong inject question bank vao shell nhe truc tiep; luon inject vao inline build.
- Khong sua output quiz generated truc tiep.

## Ket qua thuc thi

- Da tach source module:
  - `Template/QTemp/shell.html`
  - `Template/QTemp/styles.css`
  - `Template/QTemp/runtime.js`
- Da them `ENGINE/launcher_modules/qtemp_template.py` de build inline template trong memory.
- Da them `Tools/DevTool/build_qtemp_template.py` de extract/build/check template.
- Da build `Template/QTemp.html` thanh shell nhe tham chieu module source.
- Da cap nhat `DukeLauncher.pyw` va `Tools/DevTool/Remaster/remasterQTemp.py` de dung inline template truoc khi inject `fullQuestionBank`.
- Dung luong `Template/QTemp.html` sau refactor: khoang 2.3 KB; inline template build trong memory: khoang 53 KB.

## Regression checks da chay

- `python Tools/DevTool/build_qtemp_template.py check`
- `python -m py_compile Tools/DevTool/build_qtemp_template.py ENGINE/launcher_modules/qtemp_template.py Tools/DevTool/Remaster/remasterQTemp.py DukeLauncher.pyw`
- `node --check Template/QTemp/runtime.js`
- Audit duplicate function trong `Template/QTemp/runtime.js`.
- Smoke inline build + marker count cho `const fullQuestionBank`.
- Smoke question-bank injection bang regex cua `DukeLauncher.pyw`.
- Smoke `remasterQTemp.replace_fullquestionbank_in_template()` tren inline template.
- Mojibake byte-pattern guard cho `Template/QTemp.html`.
