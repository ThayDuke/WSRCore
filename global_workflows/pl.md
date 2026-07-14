---
description: Trigger planning workflow and create planning file
---

# Quy trình Planning `/pl` (WSR Core 1.0)

Quy trình lập kế hoạch trước khi code:

## Quy định thực thi
1. **Tuyệt đối cấm tạo file `implementation_plan.md`:** Để tránh kích hoạt cơ chế tự động duyệt.
2. **Nơi lưu trữ kế hoạch:** Tạo và ghi tại `DOCS/Planning/planning_[tên_nhiệm_vụ].md`.
3. **Nội dung kế hoạch:**
   - Metadata Header dạng YAML.
   - checklist Phạm vi thay đổi.
   - Điểm neo Hành vi cốt lõi (Behavioral Memory Anchors).
   - Kiến trúc giải thuật và mã giả (cấm viết code hoàn chỉnh).
4. **Báo cáo trên chat:**
   - Không in code block lên chat.
   - Báo đường dẫn file dưới dạng link tuyệt đối markdown: `[tên_file](file:///đường_dẫn_tuyệt_đối)`.
   - Dòng cuối tuyệt đối là:
     `> [!IMPORTANT]`
     `> VUI LÒNG XEM XÉT VÀ PHÊ DUYỆT!`
5. **Điểm dừng bắt buộc:** Dừng chờ phê duyệt thủ công (ok, làm đi, duyệt...) từ User trước khi code.
