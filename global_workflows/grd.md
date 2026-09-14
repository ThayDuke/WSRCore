---
description: Grill a codebase decision and prepare controlled glossary or ADR updates
---

# /grd

Làm rõ thiết kế trong codebase và chuẩn bị glossary hoặc ADR có kiểm soát.

## Trạng thái

- Luôn bắt đầu ở `DISCUSSION`.
- Nạp capability `wsr-grilling` theo profile `task`.
- Được đọc codebase và tài liệu hiện hữu.
- Không ghi file trước approval allowlist chính xác.
- Câu trả lời grilling không phải quyền sửa file.
- Approval chỉ cho phép ghi glossary và ADR đã trình bày.
- Không mở rộng sang sửa source hoặc triển khai tính năng.

## Cách chạy

- Chạy engine grilling với mode `docs`.
- Nạp reference domain chỉ khi mode này hoạt động.
- Đối chiếu thuật ngữ với code và tài liệu hiện hữu.
- Mỗi lượt hỏi đúng một câu và kèm khuyến nghị.
- Giữ glossary delta và ADR candidates trong hội thoại.
- Khi frontier rỗng, trình bày toàn bộ target và nội dung dự kiến.
- Chờ approval hiện tại trước khi ghi.
- Sau khi ghi, báo artifact và kiểm tra đã chạy.

## Đường dẫn

- Mặc định dùng `.agents/domain/CONTEXT.md`.
- Mặc định dùng `.agents/domain/adr/NNNN-ten-quyet-dinh.md`.
- Nearest project rule hoặc tài liệu dự án hiện hữu được ưu tiên.
- Mọi target phải nằm trong workspace.

## Định dạng

- Dùng tiếng Việt Caveman, tối đa 20 từ mỗi dòng.
- Dùng đúng bốn khối alert của `GEMINI.md`.
- Không in reasoning nội bộ hoặc toàn bộ cây quyết định.
- DISCUSSION chốt `> [!IMPORTANT]\n> XIN VUI LÒNG PHÊ DUYỆT`.
- Hoàn thành sau approval chốt `> [!IMPORTANT]\n> ĐÃ HOÀN THÀNH NHIỆM VỤ`.
- Dòng context luôn nằm cuối phản hồi.
