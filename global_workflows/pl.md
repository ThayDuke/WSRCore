# /pl

Tạo hoặc cập nhật kế hoạch tại `DOCS/Planning/planning_<task>.md`.

## Trạng thái và continuation

- Lần gọi đầu là `PLAN_DRAFT`: ghi mục tiêu, phạm vi, rủi ro, bước, gate và tiêu chí hoàn tất.
- Không có tín hiệu phê duyệt thì không sửa source, không triển khai, không coi plan là quyền sửa.
- Prompt tiếp theo chưa được duyệt là `PLAN_CONTINUATION`.
- Cập nhật đúng file plan hiện tại; giữ lịch sử quyết định và bổ sung delta mới.
- Tăng YAML `version` từ `vN` lên `vN+1`, đồng thời tăng tiêu đề tương ứng.
- Không tạo file plan trùng tên, không đổi tên file để tạo vòng mới.
- Chỉ tín hiệu allowlist chính xác, không phân biệt hoa thường, tối đa bốn từ,
  mới chuyển `APPROVED`: `ok`, `làm đi`, `duyệt`, `ok duyệt`, `ok làm đi`,
  `được rồi làm đi`, `duyệt phương án`, `làm đi bạn`.
- Câu phủ định, nghi vấn, điều kiện hoặc phê duyệt mơ hồ không được thực thi.

## Định dạng

- Không tạo `implementation_plan.md`; báo plan bằng link tuyệt đối khi cần.
- Dùng tiếng Việt Caveman, không in code block; dùng đúng mapping alert của `GEMINI.md`.
- Trước khi lập plan, ước lượng context hiện tại và usage dự kiến của plan.
- Nếu dự kiến từ 60%, cảnh báo sớm và gợi ý chia nhỏ, `/ho` hoặc `/reload`.
- Kết thúc bản plan bằng yêu cầu phê duyệt và dòng `[Context: ~X% | Trạng thái: ...]`.

Mode `handoff`: thêm session descriptor tại `.agents/memory/wsr-session.json`.
Chỉ lưu con trỏ workspace-relative, workflow/capability và timestamp.
Cấm trường approval, secret hoặc nội dung lịch sử dài.
