---
description: Prove root cause
---

# /diag

Điều tra lỗi, kiểm tra thất bại, lỗi build hoặc hành vi bất thường.

## Trạng thái

- Luôn bắt đầu ở `DISCUSSION` và giữ read-only.
- Nạp capability `wsr-diagnose` theo profile `task`.
- Thu thập bằng chứng trước khi kết luận nguyên nhân gốc.
- Không sửa code hoặc cấu hình khi chưa có phê duyệt.

## Cách chạy

- Tái hiện lỗi và thu thập log thực tế.
- Tách biệt rõ dữ kiện đã chứng minh và giả thuyết.
- Xác định nguyên nhân gốc và đề xuất giải pháp nhỏ nhất.
- Đề xuất chuyển tiếp:
  - Nếu sửa lỗi có test: đề xuất chuyển sang `/tdd`.
  - Nếu sửa đổi lớn hoặc nhiều file: đề xuất chuyển sang `/pl`.

## Định dạng

- Dùng tiếng Việt Caveman, tối đa 20 từ mỗi dòng.
- Dùng đúng bốn khối alert của `GEMINI.md`.
- `[KẾT_QUẢ]` dùng `> [!TIP]`; `[PHƯƠNG_PHÁP]` dùng `> [!NOTE]`.
- `[RỦI_RO]` dùng `> [!WARNING]`; `[DÒNG_CHỐT]` dùng `> [!IMPORTANT]`.
- DISCUSSION chốt `> [!IMPORTANT]\n> XIN VUI LÒNG PHÊ DUYỆT`.
- Dòng context luôn nằm cuối phản hồi.
