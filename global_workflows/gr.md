---
description: Grill one idea or decision without writing workspace files
---

# /gr

Làm rõ một ý tưởng, quyết định hoặc thiết kế bằng phỏng vấn có cấu trúc.

## Trạng thái

- Luôn bắt đầu ở `DISCUSSION` và giữ read-only.
- Nạp capability `wsr-grilling` theo profile `task`.
- Câu trả lời của người dùng không cấp quyền sửa file.
- Không tạo glossary, ADR, plan hoặc session descriptor.

## Cách chạy

- Tự tra cứu dữ kiện có thể lấy từ môi trường.
- Dựng cây quyết định và giải quyết tiền đề trước.
- Mỗi lượt hỏi đúng một câu duy nhất.
- Trình bày các lựa chọn chuẩn hóa theo mẫu:
  1. Lựa chọn A... (khuyến nghị).
  2. Lựa chọn B...
  3. Lựa chọn C...
  Nếu chọn B thì...
  Nếu chọn C thì...
- Báo ngắn quyết định đã chốt và frontier còn mở.
- Kết thúc khi frontier rỗng và hai bên đã hiểu thống nhất.
- Đề nghị `/pl` nếu người dùng muốn chuyển kết quả thành kế hoạch.

## Định dạng

- Dùng tiếng Việt Caveman, tối đa 20 từ mỗi dòng.
- Dùng đúng bốn khối alert của `GEMINI.md`.
- Không in reasoning nội bộ hoặc toàn bộ cây quyết định.
- DISCUSSION chốt `> [!IMPORTANT]\n> XIN VUI LÒNG PHÊ DUYỆT`.
- Dòng context luôn nằm cuối phản hồi.
