---
name: wsr-audit
description: >
  Audit toàn bộ repo để tìm over-engineering, code rác, dependency thừa.
  Đề xuất danh sách những gì có thể xóa, rút gọn hoặc thay thế bằng stdlib/native.
---

# WSR Audit (Repo-wide)

Quét toàn bộ cây thư mục để săn tìm sự phức tạp, phình to code.

<!-- START_BLOCK: MODE -->
## Chế độ quét (Modes)
- Quick mode: Quét các file thay đổi (git changed).
- Deep mode: Quét toàn diện package review.
<!-- END_BLOCK: MODE -->

<!-- START_BLOCK: HUNT_TARGETS -->
## Hướng Tấn Công (Hunt targets)
- Các dependency trùng lặp hoặc không dùng.
- Hàm/Class viết lại chức năng của thư viện chuẩn (stdlib) hoặc native.
- Các file chỉ export một giá trị đơn giản.
- Các cấu hình (config) hoặc cờ (flag) chết, không bao giờ thay đổi.
<!-- END_BLOCK: HUNT_TARGETS -->

<!-- START_BLOCK: SCORE -->
## Thang điểm Scorecard
Tính điểm dựa trên số lượng file pass và file fail. Điểm tối đa 100.
<!-- END_BLOCK: SCORE -->

<!-- START_BLOCK: OUTPUT -->
## Định Dạng Kết Quả
Đầu ra là danh sách xếp hạng theo mức độ tối giản:
`<tag> <nội dung cần cắt>. <thay thế>. [đường_dẫn]`

Kết thúc bằng tổng kết:
`net: -<N> dòng code, -<M> dependency có thể loại bỏ.`
<!-- END_BLOCK: OUTPUT -->

<!-- START_BLOCK: GUARDS -->
## Quy tắc bảo vệ (Guards)
Không quét các file nhị phân, file ZIP, desktop.ini.
<!-- END_BLOCK: GUARDS -->
