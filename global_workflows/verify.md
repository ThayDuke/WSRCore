---
description: Evidence gate before completion
---

# /verify

Kiểm chứng tuyên bố hoàn thành, sửa lỗi, build hoặc phát hành bằng bằng chứng tươi.

## Trạng thái

- Giữ nguyên trạng thái read-only đối với mã nguồn.
- Nạp capability `wsr-verify` theo profile `task`.
- Chạy lại các lệnh kiểm tra mới nhất, cấm đoán mò theo luật `VERIFY-01`.
- Không tự ý sửa lỗi phát hiện được khi chưa có phê duyệt mới.

## Hợp đồng bằng chứng

- Bắt buộc lập bảng đối soát bằng chứng gồm 4 cột:
  - Tiêu chí kiểm tra.
  - Lệnh thực thi thực tế.
  - Đầu ra / Bằng chứng quan sát được.
  - Trạng thái: PASS hoặc FAIL.
- Chỉ tuyên bố hoàn tất khi 100% tiêu chí bắt buộc đạt PASS.
- Chuyển tiếp: Khi pass toàn bộ, đề xuất `/commit` hoặc `/audit`.

## Định dạng

- Dùng tiếng Việt Caveman, tối đa 20 từ mỗi dòng.
- Dùng đúng bốn khối alert của `GEMINI.md`.
- `[KẾT_QUẢ]` dùng `> [!TIP]`; `[PHƯƠNG_PHÁP]` dùng `> [!NOTE]`.
- `[RỦI_RO]` dùng `> [!WARNING]`; `[DÒNG_CHỐT]` dùng `> [!IMPORTANT]`.
- DISCUSSION chốt `> [!IMPORTANT]\n> XIN VUI LÒNG PHÊ DUYỆT`.
- Nghiệm thu thành công chốt `> [!IMPORTANT]\n> ĐÃ HOÀN THÀNH NHIỆM VỤ`.
- Dòng context luôn nằm cuối phản hồi.
