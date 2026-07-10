---
description: "Quy trình Đóng gói WSR: tự động thu thập, nâng phiên bản WSR global, cập nhật README.html và nén thành file .zip để lưu trữ và chia sẻ."
---

# Quy trình Đóng gói WSR toàn cục (/wsr)

Khi người dùng nhập lệnh `/wsr` hoặc yêu cầu đóng gói phiên bản cấu hình Agent mới, Agent bắt buộc phải thực hiện các bước sau:

## Bước 1: Thu thập thông tin Thay đổi từ Người dùng
- Nếu người dùng cung cấp thông tin tiêu đề và chi tiết các thay đổi trong prompt (ví dụ: "Đóng gói bản mới cập nhật rules và pl"), hãy sử dụng thông tin đó.
- Nếu không, hãy tóm tắt nhanh các thay đổi chính gần nhất (ví dụ: "Cơ chế lazy load workflows và đồng bộ GEMINI.md").

## Bước 2: Thực thi Script Đóng gói tự động
- Chạy lệnh Python sau để thực hiện việc quét phiên bản, tạo thư mục mới, nâng version, cập nhật `README.html` và nén zip:
  ```powershell
  python .agents/scripts/pack_wsr.py "[Tiêu đề thay đổi]" "[Chi tiết thay đổi 1; Chi tiết thay đổi 2]"
  ```
- **Ví dụ**:
  ```powershell
  python .agents/scripts/pack_wsr.py "Cập nhật Lazy Loading và Quản lý Planning" "Chuyển sang nạp JIT quy trình tiết kiệm token;Cập nhật GEMINI.md làm rõ ranh giới file artifact"
  ```

## Bước 3: Đồng bộ hóa cấu hình hệ thống
- Tự động chạy script đồng bộ hóa để cập nhật cấu hình toàn cục trên hệ điều hành Windows:
  ```powershell
  python .agents/scripts/sync_config.py
  ```

## Bước 4: Báo cáo kết quả
- Trình bày kết quả cho người dùng theo phong cách Caveman:
  - Báo cáo phiên bản mới đã tạo (ví dụ: `2.4.3`).
  - Cung cấp liên kết markdown đến thư mục mới và file `.zip` đã tạo trong `DOCS/`.
  - Dòng cuối cùng của phản hồi bắt buộc là:
    ```markdown
    > [!IMPORTANT]
    > ĐÃ HOÀN THÀNH NHIỆM VỤ
    ```
