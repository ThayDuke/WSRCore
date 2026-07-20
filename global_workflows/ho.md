---
description: Trigger handoff planning workflow and create detailed architectural plan file
---

# Quy trình Handoff `/ho` (WSR Core 1.0)

Quy trình lập kế hoạch chi tiết Handoff trước khi thực thi:

## Quy định thực thi
1. **Tuyệt đối cấm tạo file `implementation_plan.md`:** Để tránh kích hoạt cơ chế tự động duyệt.
2. **Nơi lưu trữ kế hoạch:** Tạo và ghi tại `DOCS/Planning/planning_[tên_nhiệm_vụ].md`.
3. **Nội dung kế hoạch (Tiêu chuẩn Handoff chi tiết, không giới hạn dòng):**
   - Metadata Header dạng YAML (`mode: handoff`, version, description).
   - Kiến trúc đích (Target Architecture): Thiết kế chi tiết luồng xử lý/component/giao tiếp.
   - File Ownership: Phân bảng rõ ràng trách nhiệm từng file bị tác động.
   - Thuật toán (Algorithm): Mô tả logic cốt lõi bằng ngôn ngữ tự nhiên hoặc mã giả.
   - Kịch bản triển khai (Rollout Plan): Thứ tự các bước sửa đổi và deploy.
   - Tiêu chí nghiệm thu (UAT & Verification): Các kịch bản test case thủ công/tự động chi tiết.
   - Phương án Rollback: Các bước khôi phục trạng thái cũ nếu xảy ra lỗi.
4. **Báo cáo trên chat:**
   - Không in code block lên chat.
   - Báo đường dẫn file dưới dạng link tuyệt đối markdown: `[tên_file](file:///đường_dẫn_tuyệt_đối)`.
   - Dòng cuối tuyệt đối là:
     `> [!IMPORTANT]`
     `> VUI LÒNG XEM XÉT VÀ PHÊ DUYỆT!`
5. **Điểm dừng bắt buộc:** Dừng chờ phê duyệt thủ công (ok, làm đi, duyệt...) từ User trước khi code.
