---
description: Hỗ trợ commit các thay đổi đã sửa đổi hoặc toàn bộ dự án vào hệ thống Git một cách chuẩn mực.
---

# Quy trình Commit Git (/commit)

Khi người dùng nhập lệnh `/commit`, Agent thực hiện việc kiểm tra và commit các file đã thay đổi:

## Bước 1: Kiểm tra trạng thái Git
- Chạy lệnh `git status` để hiển thị các file thay đổi, file mới tạo, hoặc đã xóa.

## Bước 2: Liệt kê các thay đổi và chuẩn bị commit
- Liệt kê các file chuẩn bị commit cho người dùng kiểm tra nhanh.
- Yêu cầu người dùng cung cấp thông điệp commit (commit message) hoặc Agent tự động sinh thông điệp siêu ngắn dưới 10 từ (định dạng `type(scope): description`) nếu người dùng không chỉ định.

## Bước 3: Thực hiện commit tự động (Ngoại lệ được phép)
- Do người dùng chủ động gọi lệnh `/commit`, Agent được phép tự động đề xuất và chạy chuỗi lệnh stage/commit sau (thông qua `run_command` chờ phê duyệt UI):
  `git add -A`
  `git commit -m "<thông điệp commit>"`
- Báo cáo kết quả commit thành công cho người dùng.
- Kết thúc nhiệm vụ và xuất thông điệp hoàn thành.

