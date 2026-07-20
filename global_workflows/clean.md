---
description: Scan and remove temporary files safely using WSR whitelist policy
---

# Quy trình Dọn Dẹp `/clean` (WSR Core 1.0)

Khi chạy lệnh `/clean` để tối ưu dung lượng dự án:

## Quy định thực thi
1. **Chạy ở chế độ quét (Mặc định):**
   `python .agents/scripts/wsr_clean.py`
   - Chỉ hiển thị danh sách file tạm, rác.
   - Tuyệt đối không xóa bất kỳ file nào.
2. **Thực thi xóa thực tế:** Chỉ chạy khi User duyệt riêng:
   `python .agents/scripts/wsr_clean.py --apply --approval-token [buildId]`
3. **Quy tắc bảo toàn:**
   - Whitelist động được định nghĩa trong `cleanWhitelist` tại `WSR_MANIFEST.json`.
   - Không được xóa các file kế hoạch đang chạy trong `DOCS/Planning/`.
