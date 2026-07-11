---
name: wsr-debt
description: >
  Thu thập tất cả các comment đánh dấu nợ kỹ thuật `# wsr-debt:` hoặc các tag
  TODO/FIXME/HACK trong codebase vào ledger để theo dõi, tránh việc trì hoãn vô thời hạn.
---

# WSR Technical Debt Management

<!-- START_BLOCK: TAG_SCHEMA -->
## Định Dạng Tag Trong Code
Khi viết giải pháp tối giản tạm thời, Agent bắt buộc phải để lại comment theo định dạng:
`# wsr-debt: [mô tả giải pháp tạm], ceiling: [ngưỡng giới hạn], upgrade: [hướng nâng cấp khi đạt ngưỡng]`
<!-- END_BLOCK: TAG_SCHEMA -->

<!-- START_BLOCK: RULES -->
## Quy tắc nợ (Rules)
- Nợ mới thiếu `ceiling` hoặc `upgrade` là FAIL.
- Tag TODO/FIXME/HACK không có owner hoặc upgrade là WARN.
<!-- END_BLOCK: RULES -->

<!-- START_BLOCK: SCANNER -->
## Công cụ quét (Scanner)
Dùng Python script `wsr_debt_scanner.py` quét toàn bộ dự án để thu thập các dòng chứa tag.
<!-- END_BLOCK: SCANNER -->

<!-- START_BLOCK: LEDGER -->
## Sổ theo dõi (Ledger)
Ledger mặc định được lưu tại `./debt_ledger.md` trong package root hoặc resolve động từ target path.
<!-- END_BLOCK: LEDGER -->

<!-- START_BLOCK: CLOSE_RULE -->
## Quy trình đóng nợ (Close Rule)
Chỉ đóng nợ khi giải pháp nâng cấp thực tế (upgrade path) đã được triển khai đầy đủ và kiểm thử thành công.
<!-- END_BLOCK: CLOSE_RULE -->
