---
name: wsr-review
description: >
  Review các thay đổi code (diff) tập trung phát hiện over-engineering, code thừa,
  thiết kế quá đà, và đề xuất tối giản cho các dự án chuẩn WSR.
---

# WSR Review (Chống Over-engineering)

<!-- START_BLOCK: INPUT -->
Review các thay đổi trong diff và phát hiện các đoạn code phức tạp không cần thiết.
<!-- END_BLOCK: INPUT -->

<!-- START_BLOCK: SEVEN_GATE -->
## Quy trình Đánh giá 7 Bậc
1. Có cần làm không? (YAGNI)
2. Có sẵn trong codebase chưa?
3. Stdlib có hỗ trợ không?
4. Native platform có hỗ trợ không?
5. Dependency có sẵn chưa?
6. Viết trong 1 dòng được không?
7. Code tối thiểu nhất.
<!-- END_BLOCK: SEVEN_GATE -->

<!-- START_BLOCK: TAGS -->
## Các Tag Đánh Dấu Báo Cáo
Đầu ra của review phải là danh sách ngắn gọn, định dạng:
`L<line>: <tag> <mô tả>. <phương án thay thế>.`

- `delete:` Code chết, code dự phòng, logic không dùng. Thay thế: không có gì (xóa bỏ).
- `stdlib:` Tự viết logic khi thư viện chuẩn đã có. Thay thế: Tên hàm chuẩn có sẵn.
- `native:` Cài dependency hoặc viết JS/CSS phức tạp khi nền tảng gốc đã có. Thay thế: Tên tính năng native.
- `yagni:` Trừu tượng hóa thừa. Thay thế: Inline hoặc gộp lại.
- `shrink:` Logic đúng nhưng quá dài dòng. Thay thế: Cú pháp ngắn hơn (one-liner).
<!-- END_BLOCK: TAGS -->

<!-- START_BLOCK: OUTPUT -->
## Báo Cáo Kết Quả
Kết thúc báo cáo bằng tổng lượng dòng tối giản được:
`net: -<N> dòng code có thể cắt giảm.`

Nếu không có gì cần cắt giảm:
`Lean already. Ship.`
<!-- END_BLOCK: OUTPUT -->
