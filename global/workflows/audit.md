---
description: Quy trình chạy lệnh /audit chấm điểm chất lượng mã nguồn tĩnh.
---

# Quy trình chạy Audit WSR V1.0 (/audit)

Khi nhận lệnh `/audit`, thực hiện:

## Bước 1: Gọi công cụ wsr_audit.py
- Chạy wsr_audit.py (ưu tiên ENGINE/, fallback global_tools/).
- Cấm tự sửa đổi các file mã nguồn.

## Bước 2: Đánh giá Điểm số (Scorecard)
- Kiểm tra các tiêu chuẩn mã hóa, an toàn và **Minimal Coding Protocol** (đáp ứng tiêu chí sửa đúng gốc, không sửa ngọn, số lượng file/dòng code thay đổi tối thiểu, không refactor lan rộng).
- Output: Điểm 0-100, PASS/WARN/FAIL, 3 bước QA thủ công.

## Bước 3: Báo cáo
- Báo cáo kết quả trực quan dạng bảng hoặc checklist ngắn.
- Dừng tiến trình và chờ phản hồi của người dùng.
