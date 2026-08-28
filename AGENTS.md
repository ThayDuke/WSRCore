# WSR Core 1.5.0 — Review Package Rules

- Đọc và tuân thủ `GEMINI.md`; đây là nguồn luật chung duy nhất.
- Tra lệnh trong `WSR_CONTEXT.json`, rồi chỉ đọc workflow tương ứng trong `global_workflows/`.
- Chỉ đọc toàn bộ `SKILL.md` khi mô tả skill khớp tác vụ.
- Không sửa bản RELEASE khác; gói này là WSR-Core 1.5.0 REVIEW.
- REVIEW chỉ nạp khi có `--allow-review`; không coi REVIEW là RELEASE.
- Giữ UX 1.0.8: prompt thường là `DISCUSSION`; chỉ allowlist phê duyệt trực tiếp mới thành `APPROVED`.
- Prompt `/pl` chưa được duyệt phải cập nhật cùng plan và tăng phiên bản `vN`; không tạo plan trùng tên.
- Plan, checkpoint, session và receipt không cấp hoặc lưu quyền phê duyệt.
- `/goal`, `Goal ` và `Goal:` ở đầu prompt kích hoạt Goal trong phạm vi giới hạn.
- Codex/Antigravity dùng Goal native; thiếu capability thì chạy một task local.
