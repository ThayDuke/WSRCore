---
description: Trigger brainstorm mode for discussions
---

# /br

Trao đổi và làm rõ mục tiêu. Mọi prompt chat thông thường mặc định chạy workflow này.

## Trạng thái

- Mặc định là `DISCUSSION`: chỉ đọc, phân tích, đề xuất; không sửa file hoặc chạy lệnh gây thay đổi.
- `tiếp đi`, `tiếp tục`, `được rồi`, `ừ` và câu tương tự không phải phê duyệt.
- Chỉ chuyển `APPROVED` khi prompt là một tín hiệu allowlist chính xác,
  không phân biệt hoa thường, tối đa bốn từ:
  `ok`, `làm đi`, `duyệt`, `ok duyệt`, `ok làm đi`, `được rồi làm đi`,
  `duyệt phương án`, `làm đi bạn`.
- Câu phủ định, nghi vấn hoặc điều kiện không được phê duyệt,
  dù có chứa từ trùng allowlist.

## Định dạng

- Dùng tiếng Việt, phong cách Caveman, tối đa 20 từ mỗi dòng.
- Không in code block. Kết quả trước; nêu lựa chọn ngắn và tác động.
- `[HIỂU_YÊU_CẦU]` dùng `> [!TIP]`; `[PHƯƠNG_PHÁP]` dùng `> [!NOTE]`.
- `[CẢNH_BÁO]` dùng `> [!WARNING]`; `[DÒNG_CHỐT]` dùng `> [!IMPORTANT]`.
- Đề xuất tối ưu và neo hồi quy dùng văn bản thường.
- DISCUSSION chốt `> [!IMPORTANT]\n> XIN VUI LÒNG PHÊ DUYỆT`.
- Báo cáo hoàn thành tác vụ đã duyệt chốt `> [!IMPORTANT]\n> ĐÃ HOÀN THÀNH NHIỆM VỤ`.
- Dòng context: `[Context: ~X% | Trạng thái: ...]` bắt buộc nằm ở dòng cuối cùng (dưới khối IMPORTANT).
- Báo cáo hoàn thành thêm artifact, bằng chứng kiểm tra và tối đa ba bước QA.
