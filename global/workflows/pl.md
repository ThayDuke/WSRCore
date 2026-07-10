---
description: "Quy trình Planning: lập kế hoạch và xuất ra file tài liệu MD trong thư mục DOCS (phân tích sâu, lưu file và chờ phê duyệt, TUYỆT ĐỐI không tự ý sửa code)."
---

# Quy trình Planning xuất file tài liệu V2.0 (/pl)

Khi người dùng nhập lệnh `/pl` hoặc yêu cầu bắt đầu bằng `/pl`, Agent bắt buộc phải thực hiện quy trình sau để xây dựng tài liệu thiết kế và gỡ lỗi chuyên sâu:

## Bước 1: Risk Gate & Kiểm tra Ngữ cảnh
- Kiểm tra load rules toàn cục và cục bộ.
- Chấm rủi ro 5 yếu tố, xác định Risk Level.
- Ước lượng % context window.
- **Tư duy tối thiểu (Chặn từ đầu):** Xác định rõ Mục tiêu thật, Failure Layer (UI, Logic, Export, Shell, Data, Config), File nguồn đúng cần sửa (cấm sửa ngọn), Hành vi giữ nguyên, Rủi ro hồi quy và Phương án ít thay đổi nhất.

## Bước 2: Xây dựng File Tài Liệu Markdown Chuyên Sâu
Tạo và ghi nội dung vào file tài liệu theo đường dẫn: `DOCS/Planning/planning_[tên_nhiệm_vụ]_v[X].md`. Nội dung file bắt buộc tuân thủ cấu trúc dữ liệu nghiêm ngặt sau:

1. **Metadata Header (Cấu trúc YAML Frontmatter):**
   ```yaml
   ---
   task_name: "[Tên nhiệm vụ]"
   date: "YYYY-MM-DD"
   version: "v[X]"
   status: "Draft / Approved"
   risk_level: "LOW / MEDIUM / HIGH"
   failure_layer: "UI / Logic / Export / Shell / Docs"
   audit_required: true / false
   target_files:
     - "đường_dẫn_tuyệt_đối_file_1"
     - "đường_dẫn_tuyệt_đối_file_2"
   ---
   ```
2. **Phạm vi Thay đổi (Impact Scope - Định dạng Checklist):**
   * Sử dụng các tag trạng thái rõ ràng kết hợp hộp kiểm (`[ ]`):
     - `- [ ] [MODIFY] path/to/file`
     - `- [ ] [NEW] path/to/file`
     - `- [ ] [DELETE] path/to/file`
3. **Điểm neo Hành vi cốt lõi (Behavioral Memory Anchors):**
   - Liệt kê danh sách các hàm, biến và mô tả chi tiết hành vi bắt buộc giữ nguyên.
4. **Kiến trúc Giải thuật & Mã giả (Architecture & Pseudocode):**
   - Chỉ viết mã giả (pseudocode), skeleton cấu trúc class/hàm hoặc mô tả luồng thay đổi. CẤM viết mã nguồn hoàn chỉnh để tránh xung đột với luật cấm in code và tiết kiệm dung lượng context.
5. **Quy chuẩn hiển thị Alerts cho các đề mục phân tích:**
   - Sử dụng cú pháp Markdown Alert để bọc các nhãn tiêu đề:
     - `> [!TIP]` bọc nhãn `[HIỂU_YÊU_CẦU]`
     - `> [!NOTE]` bọc nhãn `[PHƯƠNG_PHÁP]`
     - `> [!WARNING]` bọc nhãn `[CẢNH_BÁO]`
     - Các nhãn `[ĐỀ_XUẤT_TỐI_ƯU]` và `[NEO_HỒI_QUY]` hiển thị dạng văn bản thường (không dùng alert).

## Bước 3: Xuất File và Báo cáo Trạng thái
- Lưu file với mã hóa UTF-8 chuẩn tiếng Việt có dấu.
- Trở lại cửa sổ chat, báo cáo đường dẫn file dưới dạng liên kết markdown: `[filename](file:///đường_dẫn_tuyệt_đối)`.
- Sử dụng phong cách Caveman để tóm tắt nhanh: `[Tạo File]: [Thành công]. [Đường dẫn]: [Link file] | VUI LÒNG XEM XÉT VÀ PHÊ DUYỆT!`

## Bước 4: Điểm dừng Bắt buộc (Mandatory Halt)
- Dừng toàn bộ tiến trình. Không tự ý can thiệp vào mã nguồn của dự án.
- **Tín hiệu phê duyệt ngắn gọn (<= 4 từ):** Câu đồng ý không phân biệt chữ hoa thường (ví dụ: `ok`, `làm đi`, `duyệt`, `ok duyệt`, `Ok làm đi`, `Được rồi làm đi`, `Duyệt phương án`, `Làm đi bạn`...). Khi nhận được tín hiệu này mới được phép tiến hành code thực tế.
- **Vòng thảo luận và Tăng phiên bản kế hoạch:** Nếu prompt tiếp theo không có dấu hiệu phê duyệt hoặc slash command khác, Agent coi như tiếp tục vòng thảo luận `/pl` và bắt buộc tạo ra phiên bản file kế hoạch tiếp theo: `planning_[tên]_v2.md`, `planning_[tên]_v3.md`... cho đến khi nhận được phê duyệt cuối cùng.
- **Lưu ý khi thực thi**: Sau khi viết code, chạy wsr_audit.py (ưu tiên ENGINE/wsr_audit.py, fallback global) để chấm điểm và sinh QA.


