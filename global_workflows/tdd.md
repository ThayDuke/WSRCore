---
description: Approval-gated red-green-refactor
---

# /tdd

Triển khai tính năng hoặc vá lỗi theo kỷ luật Test-Driven Development.

## Trạng thái

- Bắt đầu ở `DISCUSSION`: chỉ xác định mục tiêu và ca kiểm thử.
- Nạp capability `wsr-tdd` theo profile `task`.
- Phê duyệt từ allowlist chỉ cấp quyền trong phạm vi bài test đã duyệt.
- Không mở rộng sửa đổi ra ngoài phạm vi đã thỏa thuận.

## Quy trình Red-Green-Refactor

- RED: Tạo bài test nhỏ nhất chứng minh thất bại trước.
- GREEN: Viết code tối thiểu để bài test vượt qua.
- REFACTOR: Dọn dẹp code trong phạm vi đã phê duyệt.
- Chạy toàn bộ regression test liên quan để tránh hồi quy.
- Chuyển tiếp bắt buộc: chuyển sang `/verify` để nghiệm thu bằng chứng.

## Định dạng

- Dùng tiếng Việt Caveman, tối đa 20 từ mỗi dòng.
- Dùng đúng bốn khối alert của `GEMINI.md`.
- `[KẾT_QUẢ]` dùng `> [!TIP]`; `[PHƯƠNG_PHÁP]` dùng `> [!NOTE]`.
- `[RỦI_RO]` dùng `> [!WARNING]`; `[DÒNG_CHỐT]` dùng `> [!IMPORTANT]`.
- DISCUSSION chốt `> [!IMPORTANT]\n> XIN VUI LÒNG PHÊ DUYỆT`.
- Hoàn thành sau approval chốt `> [!IMPORTANT]\n> ĐÃ HOÀN THÀNH NHIỆM VỤ`.
- Dòng context luôn nằm cuối phản hồi.
