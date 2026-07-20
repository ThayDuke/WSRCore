---
description: Trigger WSR packaging workflow and create release distribution ZIP
---

# Quy trình Đóng Gói `/wsr` (WSR Core 1.0)

Khi thực hiện đóng gói WSR Package để kiểm tra hoặc lưu trữ:

## Quy định thực thi
1. **Chạy script đóng gói nháp:**
   `python .agents/scripts/pack_wsr.py`
2. **Không tự ý sync cấu hình:**
   - Trong quá trình phát triển/review nháp, tuyệt đối không tự ý chạy `sync_config.py --apply`.
3. **Báo cáo kết quả:**
   - Output phải in ra đầy đủ thông tin:
     - Phiên bản đóng gói (Version).
     - Thư mục nguồn (Source Folder).
     - Đường dẫn tệp zip đích.
4. **Quy định nơi lưu trữ Release ZIP:**
   - Mỗi lần đóng gói release WSRCore, file ZIP thành phẩm bắt buộc phải được đặt trong thư mục `DOCS/` của dự án.
   - Tuyệt đối nghiêm cấm tạo file ZIP release trực tiếp ngoài thư mục root của repository.

