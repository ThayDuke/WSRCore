---
description: Authorize one bounded Goal execution and its task receipts
---

# /goal

Ủy quyền thực thi một Goal giới hạn và thu thập biên lai công việc.

## Khởi tạo và ghi nhận

- Nhận diện prefix `/goal`, `Goal ` hoặc `Goal:` ở đầu prompt.
- Ghi nhận mục tiêu, định danh Goal, nguồn ủy quyền và `allowedPaths`.
- Thiết lập cơ chế tự động checkpoint trong Goal ledger.

## Kiểm soát ngữ cảnh và thực thi

- Ước lượng context trước khi dispatch tác vụ.
- Nếu context dự kiến chạm 60%: chia nhỏ Goal hoặc checkpoint ngay.
- Chỉ dispatch tác vụ nằm trong phạm vi `allowedPaths`.
- Bắt buộc biên lai `goal-task-v1` cho mỗi tác vụ hoàn thành.
- Nếu thiếu Goal native, thực thi một tác vụ cục bộ trong phạm vi hẹp.
- Tuyệt đối không lưu quyền phê duyệt hoặc secret ra ngoài phạm vi.

## Định dạng

- Dùng tiếng Việt Caveman, tối đa 20 từ mỗi dòng.
- Dùng đúng bốn khối alert của `GEMINI.md`.
- `[KẾT_QUẢ]` dùng `> [!TIP]`; `[PHƯƠNG_PHÁP]` dùng `> [!NOTE]`.
- `[RỦI_RO]` dùng `> [!WARNING]`; `[DÒNG_CHỐT]` dùng `> [!IMPORTANT]`.
- Hoàn thành toàn bộ Goal chốt `> [!IMPORTANT]\n> ĐÃ HOÀN THÀNH NHIỆM VỤ`.
- Dòng context luôn nằm cuối phản hồi.
