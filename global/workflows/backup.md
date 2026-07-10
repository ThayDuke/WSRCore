---
description: Thực hiện quy trình sao lưu toàn bộ dự án vào thư mục sao lưu (backup) được cấu hình trên Windows.
---

# Quy trình Sao lưu Dự án (Project Backup Shortcut)

Khi người dùng gõ phím tắt hoặc dùng lệnh `/backup`, Agent phải thực hiện chính xác quy trình sao lưu sau dựa trên thông tin cấu hình cục bộ tại `AGENTS.md` (hoặc `.codex/rules/`):

## Bước 1: Xác định Tên File Sao Lưu
1. **Kiểm tra tham số**: Xem phía sau lệnh backup của người dùng có chứa phần text mô tả bổ sung nào không.
2. **Xử lý tên file**:
   - Nếu có phần text đi kèm: Loại bỏ tất cả các ký tự không hợp lệ đối với tên file Windows (`< > : " / \ | ? *`), trim các khoảng trắng hoặc dấu chấm ở đầu/cuối, và đảm bảo kết thúc bằng đuôi `.zip`.
   - Nếu không có phần text đi kèm: Tự động đặt tên theo định dạng thời gian thực: `[Tên_Dự_Án]_ddMMyyyy_HHmmss.zip` (Ví dụ: `Project_22052026_090000.zip`).

## Bước 2: Xác định Đường dẫn Nguồn và Đích
- **Thư mục nguồn (Source)**: Thư mục gốc của workspace hiện tại.
- **Thư mục lưu trữ (Destination)**: Đọc cấu hình đường dẫn đích tại `AGENTS.md` của dự án (Đảm bảo thư mục này tồn tại, nếu chưa có thì tự động tạo).

## Bước 3: Thực hiện Nén Loại trừ (Exclusions)
Sử dụng script Python, PowerShell hoặc công cụ nén của hệ thống để nén file nhằm đảm bảo loại trừ chính xác các thư mục không cần thiết và tối ưu dung lượng:
- **Thư mục loại trừ mặc định**: `.git`, `.venv`, `__pycache__`, và các thư mục tạm/backup được cấu hình loại trừ cụ thể trong file `AGENTS.md` cục bộ.

## Bước 4: Kiểm tra và Xác nhận Kết quả
Sau khi nén thành công, Agent phải xác minh và báo cáo chi tiết cho người dùng bằng tiếng Việt các thông tin sau:
- Tên tệp tin backup và đường dẫn lưu trữ chính xác.
- Dung lượng của tệp tin `.zip` đã tạo.
- Xác nhận các thư mục trong danh sách loại trừ đã được loại bỏ thành công khỏi file sao lưu.
- Chạy trình `wsr_audit.py` (nếu có) và xuất thông điệp hoàn thành theo đúng quy tắc.


