# CHANGELOG

## v2.4.1 - 2026-07-09
- **Tích hợp Giao thức Code tối thiểu (Minimal Coding Protocol - WSR-Duke-All-2.4.1)**:
  - Bắt buộc xác định Failure Layer, file nguồn đúng và các yếu tố hồi quy trước khi code.
  - Cấm tuyệt đối sửa ngọn (sửa ngọn sẽ bị rollback lập tức).
  - Ưu tiên localized patch, chỉ chạm tối thiểu số file và dòng code.
  - Dung hòa giữa sửa tối thiểu với đồng bộ theme và full code trong localized patch.
  - Cập nhật đồng bộ GEMINI.md, AG_DECISION_RULES.md, SKILL.md và các file workflow (br, pl, audit).

## v2.4.0 - 2026-07-09
- **Cải tiến Quy trình Phê duyệt & Vòng thảo luận (WSR-Duke-All-2.4.0)**:
  - Mọi prompt chat mặc định là `/br` để ngăn tự ý sửa code ngoài ý muốn.
  - Hỗ trợ tín hiệu phê duyệt ngắn gọn (<= 4 từ, không phân biệt hoa thường như: `ok`, `làm đi`, `duyệt`, `Ok làm đi`...).
  - Triển khai cơ chế vòng thảo luận liên tiếp (v2, v3...) đối với `/br`.
  - Tích hợp vòng thảo luận cho `/pl`, tự động tăng số hiệu phiên bản file kế hoạch `planning_[tên]_v2.md`, `v3.md`... nếu chưa nhận được tín hiệu phê duyệt.
  - Cập nhật đồng bộ các file cấu hình toàn cục `GEMINI.md`, `workflows/br.md`, `workflows/pl.md` và file cục bộ `AG_DECISION_RULES.md`.

## v2.1.0 - 2026-04-13
- **Bổ sung Giao thức Phục hồi Ngữ cảnh (Context Recovery Protocol)**:
  - Thêm quy tắc **Self-Audit**: Tự động rà soát Regression Guard khi task kéo dài hoặc sửa nhiều file.
  - Thêm cơ chế **Context Refresh**: Chống hiện tượng "forgetting" trong session dài.
  - Thiết lập lệnh **Audit/Rules?** từ phía User để ép Agent tái nạp tri thức ngay lập tức.

## v2.0.0 - 2026-04-13
- **Tái cấu trúc toàn diện (Major Architecture Refactor)**:
  - Hợp nhất toàn bộ quy tắc hành vi và logic ra quyết định vào `AG_DECISION_RULES.md`.
  - Giảm quy mô `SKILL.md` từ ~450 dòng xuống ~40 dòng (Tiết kiệm >90% context nạp mặc định).
  - Tinh gọn `dec-debug-playbook.md` tập trung hoàn toàn vào Heuristics chẩn đoán.
  - Nén `ag-prompt-patterns.md` thành các template mật độ cao (High-density templates).
- **Tối ưu Quota & Token**:
  - Triển khai **Micro-mode** cho các tác vụ đơn giản.
  - Chuẩn hóa Header báo cáo mới, ngắn gọn hơn.
  - Áp dụng nguyên tắc "Patch-only" triệt để.
- **Hệ thống hóa**: Đảm bảo tính nhất quán giữa các tài liệu rules bằng cách thiết lập Single Source of Truth.

## v1.5.0 - 2026-04-07
- Bổ sung **Hệ thống Thuật ngữ & Quy ước (Terminology)** vào `SKILL.md` và `AG_DECISION_RULES.md`:
  - Định nghĩa **Dashboard**: `DukeEnglishCenter.html` / `DukeLauncher.pyw`.
  - Định nghĩa **Tool/Các tool**: Các tiện ích của DEC (`ToolExam`, `ToolAdaptive`...).
  - Định nghĩa **Theme E/Y**: Giao diện Elegant và Youth.
- Bổ sung **Quy tắc Remaster**: Luôn ưu tiên nâng cấp công cụ cũ thay vì tạo mới để tránh trùng lặp tính năng.

## v1.4.0 - 2026-04-03
- Bổ sung các **Heuristic Xử lý Zoom và Focus Mode** vào `dec-debug-playbook.md`:
  - Kỹ thuật **Non-scaling border**: Sử dụng `calc(1px / zoom)` để giữ viền 1px không bị dày lên khi phóng to.
  - Kỹ thuật **Zoom-pending visibility toggle**: Ẩn phần tử trong lúc tính toán Zoom để loại bỏ hiện tượng "nháy" (flicker).
  - Kỹ thuật **Layout Settlement Timing**: Sử dụng `setTimeout(100ms)` hoặc `double-rAF` để đảm bảo trình duyệt đã tính toán xong khung nhìn (viewport) trước khi đo đạc kích thước Zoom.
  - Kỹ thuật **Transition Interference**: Vô hiệu hóa CSS transitions trong lúc đo đạc để tránh lấy sai giá trị `getBoundingClientRect()`.
 
+## v1.3.0 - 2026-04-03
- Triển khai **Chế độ vận hành mặc định: Isolation First**:
  - Tuyệt đối chỉ sửa file được yêu cầu, không tự ý sửa lan sang các sibling tools/shared files.
  - Quy trình 3 bước: Sửa -> Xác nhận -> Gợi ý file tiếp theo.
  - Thêm mục `Operational Mode` và `Next Potential Steps` vào form báo cáo chuẩn.
- Bổ sung quy tắc **Sửa Gốc, Không Sửa Ngọn (Source-fix Only)**: Luôn fix lỗi từ file nguồn/template (như `UltiTemp.html`, `ToolListening`) để đảm bảo không tái diễn lỗi ở các file output sau này, tuyệt đối không sửa trực tiếp file kết quả (như `result.html`).
- Bổ sung cơ chế **Godmode**: Cho phép sửa hàng loạt và đồng bộ hệ thống khi có từ khóa trigger.
- Cập nhật quy trình Housekeeping: Tách biệt việc tự động cập nhật nhật ký (logs) khỏi giới hạn Isolation của file chức năng.

## v1.2.0 - 2026-04-02
 
+## v1.1.3 - 2026-04-02
+- đồng bộ triệt để `AG_DECISION_RULES.md` với `SKILL.md` (luật lõi)
+- sửa các rule gây hiểu lầm về việc "đọc mọi tài liệu" (no full read/scan bypass)
+- thống nhất form báo cáo ở mọi vị trí trong file rules
+
 
+## v1.1.2 - 2026-04-02
+- chuẩn hóa form báo cáo bắt buộc trên tất cả các file (`SKILL.md`, `dec-debug-playbook.md`, `AG_DECISION_RULES.md`)
+- bổ sung trường `Matching lessons:` vào mẫu tóm tắt và mẫu báo cáo để đảm bảo kết nối memory
+

## v1.1.1 - 2026-04-02
- sửa "hiểu nhầm quan trọng" về cơ chế nạp ngữ cảnh:
  - xác định `SKILL.md` là luật lõi duy nhất (Single Source of Truth)
  - playbook và decision rules chỉ mở khi thật sự cần heuristic
  - lessons chỉ truy xuất có chọn lọc, không quét toàn bộ (no full scan)
- loại bỏ mọi wording gây hiểu lầm là "đọc toàn bộ file" (read full) trong playbook và rules

## v1.1.0 - 2026-04-02
- chính thức xác định skill theo mode `executor-debugger`
- bổ sung lifecycle tư duy: create -> test -> deploy -> learn -> promote -> refactor
- thêm quy tắc lesson promotion: promote khi lặp lại >= 3 lần hoặc đủ giá trị khái quát
- chuẩn hóa cấu trúc skill thành các lớp:
  - SKILL.md
  - dec-debug-playbook.md
  - AG_DECISION_RULES.md
  - AG_LESSONS.jsonl
  - metadata.json
  - CHANGELOG.md
- định hướng tối ưu context (vẫn còn wording cũ cần clean up ở v1.1.1)

## v1.0.1 - 2026-04-02
- thêm AG_DECISION_RULES.md mẫu
- thêm AG_LESSONS.jsonl seed ban đầu
- thêm learning loop sau task:
  - append lesson nếu reusable
  - update playbook nếu phát hiện pattern khái quát

## v1.0.0 - 2026-04-02
- khởi tạo skill `dec-dev-operator`
- xác định vai trò:
  - thực thi
  - debug
  - QA
  - chống regression
- thêm quy tắc vận hành cốt lõi:
  - không regression
  - không hardcode mong manh
  - không sửa lan ngoài phạm vi
  - nếu liên quan PDF/export phải bám UI thật
- thêm form báo cáo chuẩn:
  - Quick diagnosis
  - Likely layer
  - Likely scope
  - Fix direction
  - Must remain unchanged
  - Regression checks
  - Lesson to append? yes/no
