# DEC Production Release Roadmap 2026-05-15

## Mục tiêu

Đưa DEC về trạng thái đủ chuẩn production để có thể release an toàn, dựa trên release check ngày 2026-05-15.

Trạng thái mục tiêu:

- Release check đạt PASS toàn bộ P0 và P1.
- Không còn blocker ở `adaptive-lazy-loading-audit`.
- Không phát sinh hardcode UI mới theo diff-aware gate.
- Các audit report hiện có được giữ lại để commit cùng đợt khi hệ thống ổn.
- `DOCS/DEC Ads/desktop.ini` được coi là nhiễu hệ thống tự sinh và không chặn release.

## Hiện trạng đầu vào

- Branch: `main`.
- Release check gần nhất: `DOCS/Reports/DEC_PRODUCTION_EXCELLENCE_95_RELEASE_CHECK_20260515_160630.md`.
- Kết quả: FAIL, gate BLOCKED, đạt 24 trên 25 hạng mục.
- Blocker duy nhất: `adaptive-lazy-loading-audit` cấp P1.
- Audit lazy-loading ghi nhận TA load `pool_A_v3.jsonl` và `pool_B_v3.jsonl` trong cùng phiên kiểm tra.
- Unit test qua `unittest`: 13 test PASS.
- Smoke các tool chính PASS: TL, TQ, TS, TE, TA, TQI.
- Mojibake audit PASS: 380 file, 0 finding.
- QBank schema, QBank operation, security, input validation, secret hygiene đều PASS.
- UI hygiene PASS theo gate hiện tại, nhưng còn nhiều audit debt hardcode trong CSS/template.

## Nguyên tắc thực thi

- Source-first: không sửa trực tiếp `DukeEnglishCenter.html`, `index.html`, output lesson, hoặc report sinh tự động trừ khi chính script audit cần cập nhật baseline.
- Isolation-first: mỗi phase chỉ chạm đúng lớp đang xử lý, trừ khi user bật Godmode.
- Với UI, mọi thay đổi mới phải dùng DEC Master UI, token `var(--dec-*)`, class `dec-ui-*`, hoặc token bổ sung trong `Tools/assets/shared/dec-ui-tokens.css`.
- Không bulk rewrite CSS lớn nếu chưa có visual baseline và tiêu chí diff rõ.
- Sau mỗi phase phải chạy bộ kiểm tra tối thiểu của phase đó trước khi sang phase kế tiếp.
- Mọi file tiếng Việt mới hoặc sửa phải giữ UTF-8 chuẩn, không có `U+FFFD`, không có mojibake, không dùng tiếng Việt không dấu để né lỗi encoding.

## Phase 0 - Chốt baseline release

Mục tiêu: khóa lại điểm xuất phát để mọi thay đổi sau có thể so sánh được.

Phạm vi:

- Giữ các report audit đã sinh trong `DOCS/Reports` và `DOCS/QuestionBankDocs`.
- Không xử lý `DOCS/DEC Ads/desktop.ini`; ghi nhận là file hệ thống tự sinh.
- Không commit ở phase này nếu chưa bắt đầu fix blocker.

Việc cần làm:

1. Ghi lại danh sách file dirty hiện tại và phân loại:
   - Audit report giữ lại.
   - `desktop.ini` bỏ qua khi đánh giá release.
   - File source chưa sửa.
2. Nếu cần commit sau này, commit theo nhóm:
   - Nhóm 1: report baseline.
   - Nhóm 2: fix TA lazy-loading.
   - Nhóm 3: hardcode/DMU cleanup.
3. Đảm bảo không có thay đổi source ngoài ý muốn trước khi sửa TA.

Tiêu chí hoàn tất:

- Có baseline release check và lazy-loading report để đối chiếu.
- Git dirty được hiểu đúng, không nhầm `desktop.ini` thành lỗi sản phẩm.

## Phase 1 - Unblock release gate TA lazy-loading

Mục tiêu: sửa blocker P1 duy nhất để release gate không còn BLOCKED.

Failure layer: Logic, performance, QBank loading.

Nguồn cần rà:

- `Tools/DevTool/adaptive_lazy_loading_audit.py`
- `ENGINE/launcher_modules/adaptive_api.py`
- `ENGINE/launcher_modules/adaptive_service.py`
- `ENGINE/launcher_modules/adaptive_runtime_core.py`
- `ENGINE/launcher_modules/adaptive_state.py`
- `Tools/assets/adaptive/*`
- `QBank/index_exam_pool.json`
- `QBank/pool_A_v3.jsonl`, `QBank/pool_B_v3.jsonl`, `QBank/pool_C_v3.jsonl`

Giả thuyết cần kiểm chứng:

- Audit đang phát hiện đúng: một request TA đang làm load nhiều pool hơn phạm vi level cần thiết.
- Hoặc audit đang quá chặt: luồng hợp lệ có thể cần preload metadata từ nhiều level nhưng không nên đọc full pool.
- Các check nội bộ đã PASS gồm `loads_index_before_pool`, `has_level_pool_cache`, `maps_single_pool_per_level`, `load_pool_is_level_scoped`; vì vậy lỗi có thể nằm ở request test, cache dùng chung, hoặc đường khởi tạo session gọi thêm level.

Việc cần làm:

1. Đọc audit để xác định hành vi mong đợi chính xác:
   - Một phiên TA level A chỉ được load pool A.
   - Một phiên TA level B chỉ được load pool B.
   - Một phiên TA level C chỉ được load pool C.
   - Index có thể được đọc trước pool nếu không đọc full pool.
2. Trace điểm load QBank:
   - Tìm hàm mở file pool.
   - Xác định tham số level đi từ frontend vào API.
   - Xác định cache level có bị giữ giữa các request audit không.
3. Sửa root cause:
   - Nếu API đang gọi load toàn bộ pool, đổi sang load theo level.
   - Nếu cache bị nhiễm giữa request test, tách cache theo level và reset đúng điểm.
   - Nếu audit chạy nhiều request và cộng dồn loaded files không đúng kỳ vọng, sửa audit để phân biệt per-request và session-wide.
4. Thêm hoặc cập nhật test nhỏ cho contract lazy-loading:
   - Level A không đọc B/C.
   - Level B không đọc A/C.
   - Level C không đọc A/B.
   - Index drift vẫn PASS.
5. Chạy lại kiểm tra phase:
   - `python Tools/DevTool/adaptive_lazy_loading_audit.py`
   - `python Tools/DevTool/smoke_tool_adaptive_modules.py`
   - `python Tools/DevTool/smoke_launcher_routes.py`
   - `python Tools/rebuild_exam_index.py --fail-on-drift`

Must remain unchanged:

- Thuật toán chọn câu TA.
- Contract response của `/api/adaptive/start`, `/api/adaptive/answer`, `/api/adaptive/result`.
- QBank schema và `index_exam_pool.json`.
- Báo cáo Adaptive PDF.
- Student session/report đang có trong `DATA/Student`.

Tiêu chí hoàn tất:

- `adaptive-lazy-loading-audit` PASS.
- Release check không còn blocker P1 từ adaptive performance.
- Không phát sinh drift QBank.
- Không giảm coverage smoke TA.

## Phase 2 - Hardcode gate nâng cấp theo DEC Master UI

Mục tiêu: biến UI hardcode debt từ trạng thái "đã biết" thành kế hoạch xử lý có kiểm soát, không phá visual.

Failure layer: UI, CSS, template, export render.

Thứ tự ưu tiên theo rủi ro và lượng debt:

1. `Tools/assets/qbank-import/tool-qbank-import.css`
2. `Tools/assets/exam/tool-exam.css`
3. `Template/AdaptiveTemp/styles.css`
4. `Template/UltiTemp/styles.css`
5. `Template/QTemp/styles.css`
6. `Tools/assets/slide/tool-slide-runtime.js`
7. `ENGINE/launcher_modules/adaptive_report.py`

Nguyên tắc xử lý:

- Không token hóa toàn bộ bằng thay thế cơ học.
- Mỗi pass chỉ xử lý một nhóm selector hoặc một component.
- Giá trị mới phải đi qua `Tools/assets/shared/dec-ui-tokens.css` nếu là token dùng chung.
- Nếu token chỉ phục vụ một tool, ưu tiên map qua biến local có nguồn từ DMU.
- Không sửa trực tiếp generated lesson hoặc report output.
- Không làm thay đổi bố cục, copy UI, kích thước container, theme Youth/Elegant nếu chưa có visual check.

Việc cần làm:

1. Chụp baseline visual cho Youth và Elegant ở desktop, tablet, mobile cho tool đang sửa.
2. Tách debt thành nhóm:
   - Màu sắc và gradient.
   - Shadow.
   - Spacing và radius.
   - Font weight và font size.
   - Inline event/style còn tồn tại.
   - JS style mutation.
3. Chuẩn hóa token theo hướng nhỏ:
   - Bổ sung token còn thiếu.
   - Dùng token ở selector đang chạm.
   - Không thay đổi selector chưa liên quan.
4. Sau mỗi tool chạy:
   - `python Tools/DevTool/ui_hygiene_audit.py --diff-aware --no-report`
   - Smoke tool tương ứng.
   - Visual check nếu có thay đổi layout.
5. Sau mỗi cụm 2 đến 3 tool, chạy:
   - `python Tools/DevTool/ui_hygiene_audit.py --no-report`
   - `python Tools/DevTool/mojibake_audit.py --no-report`

Must remain unchanged:

- Flow nhập liệu của từng tool.
- Theme switch Youth/Elegant.
- Offline font Be Vietnam Pro.
- Export HTML/PDF hiện có.
- Keyboard shortcuts và focus mode.

Tiêu chí hoàn tất:

- Diff-aware hardcode gate PASS sau mỗi patch.
- Audit hardcode tổng giảm theo từng tool, không tăng ở tool khác.
- Không có inline style hoặc inline event mới.
- Không có dashed/dotted border mới.
- Không có icon mới ở H1, label, button, tab nếu không có `[DMU-EXCEPTION]`.

## Phase 3 - Dashboard và generated output consistency

Mục tiêu: đảm bảo Dashboard, web build và output generated không lệch source sau khi source UI được chuẩn hóa.

Nguồn cần rà:

- `Template/DashboardTemp.html`
- `Template/Dashboard.css`
- `Template/Dashboard.js`
- `ENGINE/launcher_modules/dashboard.py`
- `DukeLauncher.pyw`
- Generated output: `DukeEnglishCenter.html`, `index.html`

Việc cần làm:

1. Kiểm tra source Dashboard đã là nguồn chuẩn cho output.
2. Regenerate Dashboard nếu source thay đổi.
3. Kiểm tra output không còn inline event/style phát sinh từ engine mới.
4. Với `index.html`, chỉ regenerate từ source, không sửa trực tiếp.
5. Smoke launcher route và link tool.

Tiêu chí hoàn tất:

- Dashboard source và generated output nhất quán.
- Tool links vẫn trỏ đúng localhost route.
- Không có thay đổi visual ngoài phạm vi chuẩn hóa.

## Phase 4 - Release verification full gate

Mục tiêu: chạy lại toàn bộ gate production sau khi fix blocker và các debt chính.

Bộ kiểm tra bắt buộc:

- `python Tools/DevTool/run_release_checks.py`
- `python Tools/DevTool/mojibake_audit.py --no-report`
- `python Tools/DevTool/ui_hygiene_audit.py --diff-aware --no-report`
- `python Tools/rebuild_exam_index.py --fail-on-drift`
- `python -m unittest discover tests`

Điều kiện PASS:

- Overall release check PASS.
- P0: 100 phần trăm PASS.
- P1: 100 phần trăm PASS.
- P2 còn lại phải có owner, phase xử lý, và rollback path nếu chưa dọn hết.
- Report mới được sinh và giữ lại.

Nếu còn FAIL:

- P0/P1: dừng release, sửa ngay hoặc có decision log chấp nhận rủi ro.
- P2/P3: chỉ cho phép release khi có debt note rõ trong report và không ảnh hưởng vận hành.

## Phase 5 - Đóng gói release và commit

Mục tiêu: tạo lịch sử commit sạch, dễ rollback.

Thứ tự commit đề xuất:

1. Baseline reports:
   - Các report audit ngày 2026-05-15 đã sinh.
   - Roadmap này.
2. TA lazy-loading fix:
   - Source fix.
   - Test hoặc audit update liên quan.
   - Report PASS sau fix.
3. DMU hardcode cleanup:
   - Token bổ sung.
   - CSS/template/source cleanup theo từng tool.
   - Report audit sau cleanup.
4. Release verification:
   - Release check PASS cuối cùng.
   - Release note ngắn nếu cần.

Không commit:

- `DOCS/DEC Ads/desktop.ini` nếu chỉ là file hệ thống tự sinh bị xóa.
- File cache, `__pycache__`, temp, hoặc output thử nghiệm không thuộc report chính thức.

Tiêu chí hoàn tất:

- Git status chỉ còn các file được chủ động chọn để commit.
- Có release check PASS sau cùng.
- Có rollback path theo commit nhóm.

## Checklist release cuối

- [ ] `adaptive-lazy-loading-audit` PASS.
- [ ] `run_release_checks.py` PASS toàn bộ P0/P1.
- [ ] `unittest discover tests` PASS.
- [ ] Smoke TL, TQ, TS, TE, TA, TQI PASS.
- [ ] Launcher routes PASS.
- [ ] Launcher contract snapshot PASS.
- [ ] QBank schema PASS.
- [ ] QBank operation PASS.
- [ ] Exam index drift PASS.
- [ ] Security runtime audit PASS.
- [ ] Input validation audit PASS.
- [ ] Secret hygiene audit PASS.
- [ ] Mojibake audit PASS.
- [ ] Diff-aware UI hardcode gate PASS.
- [ ] Report audit mới được giữ lại.
- [ ] `desktop.ini` được bỏ qua như nhiễu hệ thống.
- [ ] Không có file source lạ ngoài phạm vi roadmap.

## Quyết định ưu tiên

Ưu tiên tuyệt đối là Phase 1. Khi blocker TA lazy-loading chưa PASS, không nên dành thời gian vào hardcode cleanup lớn vì release gate vẫn BLOCKED.

Sau Phase 1, nếu release check PASS toàn bộ P0/P1, có thể chọn một trong hai hướng:

- Release candidate sớm: commit fix và report PASS, hardcode debt còn lại ghi rõ là P2 audit debt.
- Hardening thêm: xử lý các surface hardcode lớn theo Phase 2 trước khi đóng release.

