---
name: wsr-grilling
description: >
  Phỏng vấn một ý tưởng hoặc thiết kế theo cây quyết định.
  Dùng với /gr, /grd, grill me hoặc yêu cầu stress-test quyết định.
---

# WSR Grilling

Giúp người dùng biến giả định ngầm thành quyết định rõ ràng.

## Chọn mode

- Workflow `/gr` dùng mode `conversation`.
- Workflow `/grd` dùng mode `docs`.
- Active workflow quyết định mode và quyền.
- Không tự nâng `conversation` thành `docs`.

Mode `conversation` không đọc thêm reference.

Mode `docs` đọc:

- [Domain modeling](references/domain-modeling.md)
- [Context format](references/context-format.md)
- [ADR format](references/adr-format.md)

## Engine chung

- Xác định quyết định gốc và phạm vi hiện tại.
- Dựng cây gồm quyết định, tiền đề và nhánh phụ thuộc.
- Frontier chỉ chứa nhánh có tiền đề đã chốt.
- Hỏi đúng một câu mỗi lượt.
- Luôn kèm phương án khuyến nghị và tác động chính.
- Người dùng quyết định; agent tự tìm dữ kiện.
- Dùng công cụ read-only trước khi hỏi dữ kiện có thể kiểm chứng.
- Câu trả lời mới có thể mở hoặc đóng nhánh.
- Tóm tắt frontier, không hiển thị reasoning nội bộ.
- Dừng khi frontier rỗng hoặc người dùng kết thúc.

## Giới hạn

- Không hỏi lại dữ kiện đã có trong codebase.
- Không biến phỏng vấn thành bảng câu hỏi dài.
- Không kéo dài câu hỏi cần prototype hoặc bằng chứng thực nghiệm.
- Không hành động từ kết quả trước khi có quyền phù hợp.
- Không coi đồng thuận nội dung là approval sửa file.
- Không lưu hoặc khôi phục approval.

## Context

- Mỗi lượt ghi ngắn quyết định đã chốt và frontier còn mở.
- Từ 60%, đề nghị `/ho` hoặc checkpoint phù hợp.
- Không tạo `.grill-tree.md` trong DISCUSSION.

## Nguồn

Phỏng theo Matt Pocock Skills tại commit `3cca18b368ae95cdbdebbff572ccafa662551015`.

Xem giấy phép tại [LICENSE.upstream](LICENSE.upstream).
