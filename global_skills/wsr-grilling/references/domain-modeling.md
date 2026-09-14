# Domain Modeling

Chỉ đọc tài liệu này trong mode `docs`.

## Mục tiêu

- Chuẩn hóa thuật ngữ đặc thù của dự án.
- Phát hiện từ mơ hồ, quá tải hoặc mâu thuẫn.
- Kiểm chứng phát biểu của người dùng với codebase.
- Ghi nhớ quyết định khó đảo ngược bằng ADR.

## Trong DISCUSSION

- Đọc glossary và ADR hiện hữu.
- Đề xuất thuật ngữ chuẩn ngay khi làm rõ.
- Dùng tình huống cụ thể để kiểm tra ranh giới.
- Giữ glossary delta trong hội thoại.
- Giữ ADR candidates trong hội thoại.
- Không tạo hoặc sửa file.

## Trước khi ghi

- Frontier phải rỗng hoặc người dùng chủ động kết thúc.
- Trình bày target và nội dung dự kiến.
- Chờ approval allowlist chính xác trong prompt hiện tại.
- Approval chỉ bao phủ glossary và ADR đã trình bày.

## Chọn vị trí

- Ưu tiên chuẩn được nearest project rule khai báo.
- Nếu glossary hiện hữu, cập nhật đúng glossary đó.
- Nếu chưa có, dùng `.agents/domain/CONTEXT.md`.
- Nếu chưa có ADR convention, dùng `.agents/domain/adr/`.
- Không ghi ngoài workspace.

## ADR gate

Chỉ đề xuất ADR khi đủ ba điều kiện:

1. Quyết định khó hoặc tốn kém để đảo ngược.
2. Người đọc tương lai khó hiểu nếu thiếu bối cảnh.
3. Quyết định phát sinh từ một đánh đổi thực sự.
