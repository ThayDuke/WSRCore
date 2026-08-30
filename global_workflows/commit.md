---
description: Commit all repository changes and push to GitHub (current or specified branch)
---

# /commit

Cho phép commit toàn bộ thay đổi trong repo và đặt thông điệp commit phù hợp, sau đó tự động push lên GitHub theo nhánh đang làm việc. Nếu được chỉ định rõ nhánh đích, gộp nhánh hiện tại vào nhánh được chỉ định và tiến hành push theo đúng quy định.

- Không yêu cầu phê duyệt trước.
- Không tự động tạo issue.
- Nếu branch đích chưa tồn tại, tạo nhánh mới và push lần đầu.
- Sử dụng thông điệp commit tổng quát:
    - Nếu không có prompt, dùng "Repository update".
    - Có thể tùy chỉnh prompt ngắn gọn.
- Luôn xác nhận đã push thành công.
