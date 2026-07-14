# DEC UI Skill

## Purpose

Tai lieu nay la noi quy bat buoc cho moi AI Agent khi nhan nhiem vu `tao`, `sua`, `xoa`, `refactor`, `remaster`, `audit`, hoac `regenerate` bat ky item UI nao trong he sinh thai DEC.

Neu tac vu cham den giao dien ma agent khong tuan theo tai lieu nay, tac vu do duoc xem la `khong dat chuan`.

## Trigger

Ap dung ngay khi co mot trong cac tin hieu sau:

- Cham file HTML/CSS/JS co render UI
- Cham template export/runtime
- Cham authoring tools
- Cham launcher/dashboard/overlay/diagnostic UI
- Cham generated lesson HTML vi ly do UI
- Cham script co the tao hoac remaster UI output

## Prime Directives

1. `Shared core first`
2. `Source-of-truth before artifact`
3. `Class/token before inline style`
4. `One contract only`
5. `No silent UI drift`

## Mandatory References

Agent phai doc dung cac nguon sau truoc khi sua:

1. `DOCS/INFO/DEC_MASTER_UI_COMPONENT_SPEC.md`
2. `DOCS/INFO/DEC_UI_COMPONENT_CONTRACT.md`
3. `RefineUiReport.md`
4. Shared core trong `Tools/assets/shared/`

Neu sua runtime:

5. `Template/QTemp.html`
6. `Template/AdaptiveTemp.html`
7. `Template/UltiTemp.html` neu lien quan legacy runtime

Neu sua dashboard hoac launcher:

8. `Template/DashboardTemp.html`
9. `Template/Dashboard.js`
10. `Template/Dashboard.css`
11. `DukeEnglishCenter.html`
12. `DukeLauncher.pyw`

## Preflight Checklist

Truoc khi sua bat ky dong nao, agent phai lam du:

1. Xac dinh be mat dang sua la `authoring`, `runtime`, `dashboard`, `overlay`, hay `generated artifact`.
2. Xac dinh `source of truth` that su cua be mat do.
3. Grep nhanh cac dau hieu lech chuan trong pham vi sua.
4. Kiem tra co shared class/component nao da ton tai chua.
5. Kiem tra file dang sua co phai artifact sinh ra tu template hay khong.

## Non-Negotiable Rules

### 1. Khong copy giao dien tu mot tool bat ky

Agent khong duoc chon mot tool trong "gan giong nhat" roi copy UI cua tool do sang noi khac. Agent phai di tu shared core hoac template source chinh thuc.

### 2. Khong coi generated HTML la nguon su that

Neu mot bai hoc HTML da sinh ra tu template, agent khong duoc dung file output do lam nen chinh de phat trien lau dai. Chi duoc hotfix truc tiep artifact neu:

- user yeu cau ro
- hoac dang xu ly tinh huong khan cap

Sau do van phai quay lai sua source template that.

### 3. Khong dung `style=` cho layout tinh

Cam dung inline style cho:

- margin
- padding
- color
- font-size
- font-weight
- border
- border-radius
- display state thong thuong
- width/height tinh
- position tinh

Ngoai le chi chap nhan khi la gia tri runtime that su phai do dac dong, vi du:

- progress width theo phan tram
- transform fit-to-screen
- toa do runtime thay doi theo du lieu thuc

### 4. Khong dung `.style.display` cho visibility state thong thuong

Chuan bat buoc:

- `hidden`
- `.hidden`
- `.is-hidden`
- `.is-flex`
- `.is-grid`

Neu agent van dung `.style.display`, agent phai giai thich ro vi sao do la animation hoac runtime measurement bat kha khang.

### 5. Khong duplicate theme toggle source

Agent khong duoc:

- copy block `.theme-toggle-switch` sang authoring CSS cuc bo
- tu hardcode lai `140px`, `36px`, `102px` neu shared token da ton tai
- tao toggle moi voi geometry khac

### 6. Khong dung font legacy

Cam:

- `Tahoma`
- font fallback `sans-serif` cho UI chuan neu khong di kem `"Be Vietnam Pro"`

### 7. Khong hardcode path legacy

Cam moi tham chieu:

- `0. DUKE ENGLISH CENTER`

Neu script can path, agent phai dung path moi hoac cau hinh hoa path.

### 8. Khong tao hai he shell canh tranh trong cung mot surface

Neu surface da thuoc DEC authoring shell chuan, agent khong duoc gan them mot shell rieng voi palette/font/radius/spacing khac.

## Workflow By Operation Type

### A. Khi tao component moi

1. Kiem tra component co that su moi hay chi la bien the cua item da co.
2. Neu la bien the, bam family hien co.
3. Neu la item moi that:
4. Dat selector chuan.
5. Cam token chuan.
6. Dua vao shared core hoac template source of truth.
7. Cap nhat `DEC_MASTER_UI_COMPONENT_SPEC.md` ngay trong cung dot.
8. Ghi ro contract moi trong bao cao cuoi.

### B. Khi sua component hien co

1. Sua tu source of truth.
2. Tim moi noi dang duplicate item do.
3. Hop nhat neu co the.
4. Khong va mot cho roi bo mac cac ban copy con lai neu chung van la source dang hoat dong.
5. Neu chua xu ly het duoc, agent phai ghi no ky thuat ro trong audit/report.

### C. Khi xoa component

1. Reverse-search toan bo selector/class/id.
2. Kiem tra runtime builder va generated output lien quan.
3. Xoa CSS, JS, markup, va tai lieu lien quan.
4. Chay audit sau xoa de chac khong de orphan selector hoac flow gay.

## Surface-Specific Rules

### 1. Authoring tools

Mot authoring tool chuan phai import theo thu tu:

1. `dec-ui-tokens.css`
2. `dec-ui-shell.css`
3. `dec-ui-typography.css`
4. `dec-ui-controls.css`
5. `dec-ui-theme-toggle.css`
6. `dec-ui-state.css`
7. `dec-ui-studio.css` neu can
8. `dec-ui.js`

Agent khong duoc bo qua thu tu nay tru khi co ly do ky thuat rat ro.

### 2. Runtime templates

Agent phai uu tien sua:

- `Template/QTemp.html`
- `Template/AdaptiveTemp.html`
- `Template/UltiTemp.html`

truoc khi dung vao HTML output duoc sinh ra tu chung.

### 3. Dashboard and launcher surfaces

Day la be mat quan tri co do uu tien cao. Moi UI debt tai day phai duoc coi la `system-level debt`, khong phai loi nho le.

### 4. Diagnostic and overlay UI

Overlay loi, reconnect, popup, warning box cung la UI chinh thuc. Agent khong duoc dung ly do "day chi la screen phu" de dung ad-hoc bang inline style neu co the chuan hoa bang class.

## Required Commands

Agent phai chay cac lenh phu hop voi pham vi thay doi:

```powershell
rg -n "style=|\\.style\\.display|Tahoma|0\\. DUKE ENGLISH CENTER" <scope>
python Tools\fix_theme_toggle.py
python Tools\fix_ocd_toggle.py
python Tools\ui_hygiene_audit.py --markdown DOCS\INFO\DEC_UI_HYGIENE_AUDIT.md
```

Khi sua JS:

```powershell
node --check <changed-js-file>
```

Khi sua Python:

```powershell
python -m py_compile <changed-python-file>
```

## Documentation Duties

Neu agent thay doi UI contract, agent bat buoc:

1. Cap nhat `DOCS/INFO/DEC_MASTER_UI_COMPONENT_SPEC.md`
2. Cap nhat `DOCS/INFO/DEC_UI_COMPONENT_CONTRACT.md` neu contract ky thuat thay doi
3. Ghi thay doi vao bao cao tuong ung
4. Append tien do o cuoi roadmap neu la thay doi cap he thong

## Audit Duties

Khi duoc giao nhiem vu review/audit UI, agent phai:

1. Uu tien liet ke findings theo muc do anh huong.
2. Chi ro file va line.
3. Phan biet ro:
- cai gi da sach
- cai gi la debt con lai
- cai gi da fix ngay trong vong audit
4. Khong tuyen bo "da chuan hoa toan bo" neu van con legacy surface hoat dong.

## Definition Of Done

Mot tac vu UI chi duoc coi la xong khi:

- source of truth da dung
- khong tao drift moi
- audit/verification da chay
- tai lieu lien quan da cap nhat
- phan debt chua xu ly het da duoc ghi ro, khong che giau

## Failure Conditions

Agent duoc xem la lam sai neu xay ra mot trong cac truong hop sau:

- sua artifact thay vi source roi dung o do
- them inline style tinh moi
- them `.style.display` cho flow thong thuong
- duplicate toggle CSS
- giu font/path legacy
- khong cap nhat spec khi tao item UI moi
- bao cao "done" nhung khong chay verify

## Final Instruction

Khi co nghi ngo giua `va nhanh` va `chuan hoa dung contract`, agent phai uu tien phuong an thu hai. Neu bat buoc phai va nhanh, agent van phai ghi ro do la `temporary exception` va chi ra noi source of truth can sua tiep.
