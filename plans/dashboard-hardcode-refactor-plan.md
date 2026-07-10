# Dashboard Hardcode Refactor Plan

Operational Mode: Isolation
Layer: UI / CSS / JS / Engine

## Goal

Rao soat va xu ly Dashboard theo chuan DEC Master UI ma khong lam thay doi UI/UX hien co ngoai cac loi ky thuat can duoc khu.

## Source Boundary

- Source HTML: `Template/DashboardTemp.html`
- Source CSS: `Template/Dashboard.css`
- Source JS: `Template/Dashboard.js`
- Render engine: `ENGINE/launcher_modules/dashboard.py`
- Generated output, khong sua truc tiep: `DukeEnglishCenter.html`

## Must Remain Unchanged

- Layout Dashboard, thu tu section, text hien thi va flow su dung hien tai.
- Youth / Elegant theme behavior.
- Search, level tabs, expand/collapse folders, update Dashboard, restart server.
- Output generated tu source phai tiep tuc duoc serve qua launcher.

## Audit Findings

1. Engine con sinh inline handler `onclick="toggleFolder(this)"`.
2. Engine con sinh inline style mau folder icon.
3. JS con gan `style.pointerEvents`, `style.opacity`, `style.display` truc tiep cho state runtime.
4. JS con dung `innerHTML` cho UI state co the tao markup hardcode va kho troubleshoot.
5. CSS co duplicate `.theme-toggle-switch` block, trung voi shared DMU `Tools/assets/shared/dec-ui-theme-toggle.css`.
6. CSS selectors con nhieu gia tri truc tiep. Giai phap an toan la uu tien gom cac state/variant dang sua vao token/class truoc, khong rewrite toan bo visual trong mot buoc.

## Fix Sequence

### Step 1 - Engine Inline Cleanup

- Thay inline `onclick` bang delegated listener trong `Template/Dashboard.js`.
- Thay inline icon color bang folder kind class/data attribute.
- Them CSS token/class de giu mau hien tai.

Verify:
- `rg` khong con `onclick=` hoac `style=` trong Dashboard generated tree HTML source.
- Click folder van expand/collapse.

### Step 2 - JS State Cleanup

- Thay direct style mutations bang class state.
- Dung `hidden`/class cho search visibility neu khong lam thay doi layout.
- Giam `innerHTML` o cac state button khi co the tao DOM bang helper.

Verify:
- Search van an/hien file/folder dung logic cu.
- Restart badge loading state van khoa click va mo lai khi loi.
- Update button loading state van dung.

### Step 3 - Theme Toggle Dedup

- Dashboard chi giu mot implementation theme toggle.
- Neu can, dung shared DMU CSS source hoac token tu `dec-ui-theme-toggle.css`.
- Khong doi kich thuoc/vi tri toggle.

Verify:
- Toggle Youth/Elegant van doi label va theme.
- Khong con duplicate `.theme-toggle-switch` block trong `Template/Dashboard.css`.

### Step 4 - CSS Token Pass

- Chuyen cac literal moi cham vao thanh token dashboard/DMU.
- Khong bulk rewrite cac selector dang on dinh neu chua co visual verification.
- Loai bo border dashed trong tree theo DEC rule bang solid token.

Verify:
- `rg` tren cac selector vua sua khong con raw color/shadow/spacing neu co token phu hop.
- Youth/Elegant van can bang.

### Step 5 - Regenerate And Smoke

- Chay test launcher route neu co san.
- Regenerate Dashboard qua engine/API hoac function generate.
- Audit generated `DukeEnglishCenter.html` de dam bao khong con inline event/style tu tree.

## Stop Conditions

- Dung lai va bao cao neu thay doi can rewrite lon CSS co nguy co thay visual.
- Dung lai neu generated Dashboard khac cau truc ngoai pham vi plan.

## Execution Status

Completed safe pass:

- Removed generated inline folder `onclick`.
- Removed generated inline folder icon `style`.
- Replaced folder click behavior with delegated JS listener.
- Replaced direct JS style mutations in search/restart state with `hidden`/class state.
- Replaced Dashboard `innerHTML` state updates with DOM APIs.
- Removed duplicate Dashboard theme toggle block.
- Tokenized theme toggle and touched folder/control state values.
- Replaced dashed tree connector with solid tokenized border.
- Regenerated `DukeEnglishCenter.html` from Dashboard source.

Verification completed:

- `rg` found no `onclick=`, `style=`, `.style.*`, `innerHTML`, `insertAdjacentHTML`, `document.write`, `dashed`, or `dotted` in Dashboard source/output.
- `node --check Template/Dashboard.js` passed.
- `dashboard.py` parsed successfully with Python AST.
- Generated tool links still use `http://localhost:6868/...`.

Deferred by stop condition:

- Full tokenization of all legacy selector literals remains high risk without a visual baseline.
- Current audit count outside root/theme token declarations: about 111 color/gradient literals, 42 shadow literals, and 299 numeric layout literals.
- Recommended next step is to capture Youth/Elegant desktop/mobile screenshots, then continue CSS tokenization section by section with screenshot diff after each section.
