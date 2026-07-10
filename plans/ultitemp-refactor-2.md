# UltiTemp Refactor 2 Plan

## Pham vi

- Operational Mode: Isolation.
- Failure Layer: UI runtime + export template boundary.
- File nguon chinh: `Template/UltiTemp.html`.
- Must remain unchanged: lesson UI/UX, Youth/Elegant theme, IPA focus mode, keyboard shortcuts, `const lessonData` injection contract, standalone exported HTML.

## Danh gia hien trang

- `Template/UltiTemp.html` dang gom HTML, CSS va JS trong mot file lon khoang 3.700 dong.
- `DukeLauncher.pyw` va remaster tools tung doc truc tiep `Template/UltiTemp.html`, sau do chen `lessonData`.
- Bai hoc DEC da ghi ro: khong externalize CSS/JS neu chua thay doi pipeline export, vi lesson HTML phai portable.
- No ky thuat thay ro: runtime co hai ham `setIPAVisibility`; ham sau shadow ham truoc va lam shortcut IPA `4` khong co tac dung ro rang.

## Chien luoc refactor an toan

1. Tao checkpoint git truoc khi sua.
2. Tach module nguon duoi `Template/UltiTemp/`:
   - `shell.html`: khung HTML voi placeholder style/runtime.
   - `styles.css`: CSS UltiTemp.
   - `runtime.js`: JS runtime UltiTemp.
3. Them builder `Tools/DevTool/build_ultitemp_template.py` de sinh `Template/UltiTemp.html` dang shell nhe va build inline template trong memory khi export/remaster.
4. Kiem tra parity: shell nhe phai trung voi module source; inline template phai build duoc va con marker `const lessonData`.
5. Sua no ky thuat cuc bo trong module JS, build lai template.
6. Chay regression checks:
   - build parity.
   - marker `const lessonData` con ton tai.
   - khong tang dau hieu mojibake.
   - route/export smoke neu moi truong cho phep.
   - static audit cho duplicate function sau refactor.

## Nguyen tac thuc hien

- Khong doi layout, selector, token mau, class UI neu khong can thiet.
- Khong doi contract file standalone cua `Template/UltiTemp.html`.
- Khong sua output lesson truc tiep.
- Moi thay doi behavior phai nho, co ly do va co regression check.

## Ket qua thuc thi

- Da tao checkpoint git truoc refactor va lam viec tren nhanh rieng.
- Da tach source module:
  - `Template/UltiTemp/shell.html`
  - `Template/UltiTemp/styles.css`
  - `Template/UltiTemp/runtime.js`
- Da them builder `Tools/DevTool/build_ultitemp_template.py`.
- Da build lai `Template/UltiTemp.html` thanh shell nhe tham chieu module source.
- Da them `ENGINE/launcher_modules/ultitemp_template.py` de build inline standalone trong memory cho export/remaster.
- Da cap nhat `DukeLauncher.pyw`, `remasterUltiTemp.py`, `Remaster_IPA_Files.py` de dung inline template truoc khi chen `lessonData`.
- Dung luong `Template/UltiTemp.html` sau refactor: khoang 4.4 KB; inline template export build trong memory: khoang 162 KB.
- Da gop `setIPAVisibility` tu 2 dinh nghia ve 1 dinh nghia duy nhat.
- Da thay inline `btnMic.style.animation` bang class `.btn-mic.is-shaking` va token `--motion-shake-duration`.

## Regression checks da chay

- `python Tools/DevTool/build_ultitemp_template.py check`
- `node --check Template/UltiTemp/runtime.js`
- Audit duplicate function trong `Template/UltiTemp.html` va `Template/UltiTemp/runtime.js`.
- Smoke regex cho injection `lessonData` cua listening/remaster/slide fallback tren inline template.

## Gioi han xac minh

- `Tools/DevTool/smoke_launcher_routes.py` chua chay duoc trong Python mac dinh vi moi truong thieu package `flask`.
