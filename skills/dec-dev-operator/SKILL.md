# HỆ THỐNG KỸ NĂNG AGENT (SKILL.md)
*Tập hợp tri thức kỹ thuật và vận hành chuyên sâu của dự án DEC*

---

<!-- START_BLOCK: ARCHITECTURE -->
## CỐT LÕI KIẾN TRÚC
*   **Ngôn ngữ lập trình:** Python 3.x, HTML5, JavaScript (ES6+).
*   **Quy định thiết kế:** Code sạch, xử lý ngoại lệ toàn cục, không sử dụng thư viện ngoài nếu không có chỉ thị.
*   **Mode vận hành:** Isolation Mode (mặc định) và Godmode.
*   **Quy định UTF-8 Tiếng Việt:** 
    - Không được dùng shell pipeline (như Get-Content/Set-Content) đọc/ghi file UTF-8 có tiếng Việt diacritics.
    - Mọi file tiếng Việt mới/sửa đổi phải viết có dấu chuẩn UTF-8. Sau khi ghi phải verify không lỗi `U+FFFD`, không mojibake dạng double-encoded UTF-8.
<!-- END_BLOCK: ARCHITECTURE -->

---

<!-- START_BLOCK: MINIMAL_CODING -->
## NGUYÊN TẮC CODE TỐI THIỂU (MINIMAL CODING PROTOCOL)
*   **Quy tắc chung:** Sửa đúng gốc, ít dòng, ít file, ít rủi ro nhất.
    - *Cấm sửa ngọn:* Tuyệt đối cấm sửa ngọn (ví dụ sửa file build thay vì sửa file template). Sửa ngọn sẽ tính failed và bị rollback lập tức.
    - *Dung hòa đồng bộ:* Khi sửa UI bắt buộc đồng bộ theme Youth/Elegant và file template nguồn, được tính là 1 tác vụ đơn nhất.
    - *Dung hòa patch:* Ưu tiên patch cục bộ, cấm dùng placeholder.
    - *Dung hòa Godmode:* Cho phép sửa nhiều file nhưng phải tối giản tối đa số dòng code sửa.
*   **Chặn suy nghĩ sai từ đầu (Xác định trước khi code):**
    - Mục tiêu thật của task.
    - Failure Layer: UI, Logic, Export, Shell, Data, Config.
    - File nguồn đúng cần sửa.
    - Hành vi phải giữ nguyên (Regression Guard).
    - Rủi ro hồi quy.
    - Phương án ít thay đổi nhất.
*   **Cấm tuyệt đối:**
    - Refactor lan rộng khi chỉ yêu cầu sửa nhỏ.
    - Tạo class, service, framework nội bộ khi chưa cần.
    - Tách file mới chỉ để code trông "sạch" hơn.
    - Viết fallback phức tạp khi nguyên nhân gốc đã rõ.
    - Thêm dependency nếu có thể dùng code hiện có.
    - Chạm shared component khi task không yêu cầu.
    - Sửa giao diện bằng hardcode tạm.
    - Viết lại toàn bộ file vì muốn đồng bộ style.
*   **Nguyên lý cốt lõi:** "Code tốt nhất là code không cần viết. Code tốt thứ hai là code nhỏ, đúng chỗ, dễ xoá."
<!-- END_BLOCK: MINIMAL_CODING -->

---

<!-- START_BLOCK: AUDIO_SHELL -->
## XỬ LÝ ÂM THANH & TỰ ĐỘNG HÓA
*   **Tách câu & Lọc TTS:** Logic phân tách câu âm thanh phải loại bỏ hoàn toàn tiền tố tên người nói (ví dụ: "A:", "B:", "Speaker:") trước khi nạp vào bộ xử lý TTS.
*   **Conventional Commit:** Tự động tạo Conventional Commit Message (`type(scope): description`) khi sửa đổi xong.
*   **Dọn dẹp Cleanup:** Hỗ trợ quét rác tự động trong `Temp/` và đề xuất dọn dẹp an toàn qua workflow `clean dec`.
<!-- END_BLOCK: AUDIO_SHELL -->

---

<!-- START_BLOCK: UI_DESIGN -->
## GIAO DIỆN WEB & GAME HOÁ (DEC)
*   **Chỉ thị cốt lõi:**
    1.  `Shared core first`: Bắt đầu từ shared core trong `Tools/assets/shared/` hoặc template nguồn.
    2.  `Source-of-truth before artifact`: Sửa đổi tại file nguồn `Template/` (ví dụ `DashboardTemp.html`, `Dashboard.css`), cấm sửa ngọn tại `DukeEnglishCenter.html`.
    3.  `Class/token before inline style`: Ưu tiên dùng token/class, cấm inline style (`style=`) và `.style.display`.
    4.  `One contract only`: Đảm bảo đồng bộ hóa cả hai theme **Youth (mặc định)** và **Elegant** để triệt tiêu hiện tượng jitter, flicker.
    5.  `No silent UI drift`: Không tự ý làm chệch giao diện.
*   **Quy tắc UI nghiêm ngặt:**
    - Cấm inline style cho layout tĩnh (margin, padding, width, height, border).
    - Cấm `.style.display` cho visibility (dùng `.hidden`, `.is-hidden`, `.is-flex`, `.is-grid`).
    - Cấm duplicate theme toggle geometry (`140px`, `36px`, `102px`).
    - Cấm font legacy (`Tahoma`, `sans-serif` thiếu `Be Vietnam Pro`).
    - Cấm nét đứt/chấm (`dashed`, `dotted`), chỉ dùng nét liền (`solid`).
*   **DEC Master UI Specifications (DMU 2026):**
    - Container: `max-width: 900px`, `margin: 0 auto 20px`, `border-radius: 22px`, `padding: 22px`, `gap: 14px`, shadow `0 22px 50px rgba(28, 62, 95, 0.16)`.
    - Card: `border-radius: 18px`, `padding: 16px`, `accent-bar height: 6px`, `accent-bar color` `#e91e63 -> #00acc1` (Youth).
    - Form: Height `40px`, padding `0 12px`, textarea padding `12px`.
    - Typography: H1 `Be Vietnam Pro` zoom `0.7` margin-bottom `8px`. Main Label `font-weight: 800` margin-top `24px` margin-bottom `10px` size `1.05rem`.
    - *Banned:* Nghiêm cấm dùng font Sora hoặc font legacy khác. Cấm padding nhãn tiêu đề.
*   **Miễn trừ đặc biệt cho Game (GL, GC, GB):** Miễn trừ hoàn toàn quy tắc DMU, cho phép thiết kế free style tối ưu trải nghiệm chơi game.
<!-- END_BLOCK: UI_DESIGN -->

---

<!-- START_BLOCK: LOCAL_SERVER -->
## CẤU HÌNH SERVER LOCAL
*   **Cổng localhost:** Khởi chạy localhost luôn sử dụng cổng kết nối cố định `6868`.
*   **Ẩn Console Windows:** Khi khởi động server, bắt buộc sử dụng `ctypes.windll.user32.ShowWindow` kết hợp `kernel32.GetConsoleWindow` và tham số `0` để ẩn console hoàn toàn.
*   **Syntax verification:** Chạy `node --check <changed-js>` or `python -m py_compile <changed-python>` để xác minh cú pháp trước khi chạy server.
<!-- END_BLOCK: LOCAL_SERVER -->
