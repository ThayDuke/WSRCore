# Quy trình Nạp Cấu Hình `/reload` (Bản nháp 2.4.6)

Khi chạy lệnh `/reload` để nạp lại rules, skill và memory:

## Quy định thực thi
1. **Chế độ nạp mặc định (Tiêu chuẩn):**
   - Chỉ nạp các rules cốt lõi (`GEMINI.md`, `AGENTS.md`) và checkpoint hiện tại.
   - Bỏ qua các file rules cục bộ đặc thù và các skill chi tiết (sẽ được nạp JIT theo giai đoạn).
2. **Nạp JIT theo nhu cầu:**
   - Chỉ nạp skill hoặc rule cục bộ khi bắt đầu thực thi tác vụ cụ thể có liên quan (ví dụ: gỡ lỗi nạp playbook, sửa UI nạp checklist).
3. **Hiển thị xác nhận:**
   - Chỉ xuất ra thông báo ngắn gọn xác nhận các file đã nạp, tuyệt đối không tóm tắt lại nội dung để tiết kiệm token.
