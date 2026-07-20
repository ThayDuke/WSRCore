---
description: Auto-detect latest WSR release and sync system configuration files
---

# Quy trình Tự Động Đồng Bộ `/sync` (WSR Core)

`/sync` tự động tìm kiếm phiên bản release mới nhất và thực hiện đồng bộ tệp cấu hình hệ thống không nạp lại ngữ cảnh cũ.

## Quy trình Thực thi
1. **Tự động quét bản Release mới nhất:**
   - Quét gói release hiện hành (gói phát hành chính thức hoặc các tệp zip lưu trữ trong thư mục phát hành).
   - Chọn gói release có phiên bản (semver / `buildId`) cao nhất.
2. **Kiểm tra sức khỏe gói Release:**
   - Chạy `scripts/wsr_doctor.py` trên gói release được chọn.
   - Yêu cầu bắt buộc: Trạng thái PASS 100% (24/24 gates).
3. **Thực thi đồng bộ cấu hình (Auto Apply):**
   - Tự động thực thi `sync_config.py` với tùy chọn `--apply` và `--approval-token <buildId>` tương ứng của bản release.
   - Không nạp lại ngữ cảnh cũ và không yêu cầu hỏi lại/xin phê duyệt từ người dùng.
4. **Báo cáo kết quả:**
   - Chạy `scripts/wsr_audit.py` kiểm tra tĩnh.
   - Xuất báo cáo kết quả đồng bộ thành công (build ID, số tệp đã đồng bộ, điểm audit).
