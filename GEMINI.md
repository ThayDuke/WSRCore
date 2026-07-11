# AG Global Instructions (GEMINI.md - Hardened Draft)

## 1. Response Modes & Communication
- **Mặc định xử lý là /br:** Mọi prompt chat đều mặc định xử lý như lệnh `/br` (brainstorm, đề xuất, không tự ý viết code).
- **Chặn tự ý thực thi (Iron Rule):** Tuyệt đối nghiêm cấm Agent tự ý sửa đổi code hoặc chạy các tool ghi/xóa/chạy lệnh thay đổi hệ thống khi thảo luận. Chỉ sử dụng công cụ đọc.
- **Giới hạn hiển thị Code trên Chat (Tuyệt đối):**
  - Nghiêm cấm in các khối code (code block) trên màn hình chat khi thảo luận hoặc đề xuất.
  - Chỉ in code lên chat khi nhận được yêu cầu đích danh từ người dùng ("in code cho tôi xem").
- **Định dạng Alerts cho Chat & Báo cáo:**
  - `[HIỂU_YÊU_CẦU]` -> `> [!TIP]`
  - `[PHƯƠNG_PHÁP]` -> `> [!NOTE]`
  - `[CẢNH_BÁO]` -> `> [!WARNING]`
  - `[ĐỀ_XUẤT_TỐI_ƯU]` -> chữ thường.

## 2. Quy tắc dòng trạng thái cuối cùng
- **Context line:** Luôn hiển thị dung lượng context window trước dòng Important: `[Context: ~X% | Trạng thái: An toàn/Gần đầy/Nguy cơ tràn]`.
- **Dòng cuối cùng (Bắt buộc):**
  - Khi hoàn thành viết code thực tế: `> [!IMPORTANT]\n> ĐÃ HOÀN THÀNH NHIỆM VỤ`
  - Khi brainstorm hoặc đề xuất kế hoạch: `> [!IMPORTANT]\n> VUI LÒNG XEM XÉT VÀ PHÊ DUYỆT!`
  - Đây bắt buộc phải là dòng cuối cùng tuyệt đối của phản hồi, không in thêm ký tự nào khác sau đó.

## 3. Anti-Waste & Git-Aware Prohibitions
- **Cấm tự ý Commit & Git phức tạp:** Tuyệt đối cấm Agent tự động chạy lệnh `git commit` sau khi kết thúc task. 
- **Ngoại lệ `/commit`:** Khi người dùng chủ động gõ lệnh `/commit` hoặc yêu cầu "commit all changes", Agent tự động thực hiện commit tất cả các thay đổi sử dụng lệnh `git add -A`.
- **Cấm tự ý Backup:** Không tự ý chạy script backup. Sao lưu chỉ được thực hiện khi người dùng yêu cầu hoặc gõ lệnh `/backup`.
- **Cấm test tự động:** Tuyệt đối không tự ý chạy các công cụ test tự động, trình duyệt tự động.

## 4. Giao thức Lập kế hoạch (Planning Mode)
- **Ngoại lệ `/pl`:** Agent được phép tạo và ghi nội dung tài liệu kế hoạch vào thư mục `DOCS/Planning/planning_[tên_nhiệm_vụ].md` khi người dùng yêu cầu lập kế hoạch.
- Tuyệt đối cấm tạo file tên `implementation_plan.md` ở bất kỳ đâu.

## 5. Thư mục cấu hình chuẩn
- **Canonical Folder:** Thư mục `.agents/` là đường dẫn cấu hình chuẩn của hệ thống.
- **Compatibility Folder:** Thư mục `.codex/` là đường dẫn fallback dùng cho tương thích ngược.
- **Đồng bộ tài liệu:** Mọi file hướng dẫn và `README` trong dự án phải đồng bộ và không được mâu thuẫn với `GEMINI.md`.
