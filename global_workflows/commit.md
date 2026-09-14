---
description: Commit all repository changes and push origin/main
---

# /commit

Cho phép commit toàn bộ thay đổi trong repo và tự động push lên `origin/main`.

- Không yêu cầu phê duyệt trước.
- Đây là ngoại lệ có chủ đích theo yêu cầu người dùng.
- Ngoại lệ này không được suy rộng sang workflow khác.
- Không tự động tạo issue.
- Chỉ chấp nhận branch hiện tại là `main`.
- Không tự tạo branch, merge, rebase, pull, hoặc force-push.
- Dừng nếu remote không phải `origin` hoặc push thất bại.
- Sử dụng thông điệp commit tổng quát:
    - Nếu không có prompt, dùng "Repository update".
    - Có thể tùy chỉnh prompt ngắn gọn.
- Luôn xác nhận đã push thành công.
