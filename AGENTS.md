# WSR Core 1.6 — Release Package Rules

- Đọc và tuân thủ `GEMINI.md`; đây là nguồn luật chung duy nhất cho mọi IDE (Codex, Antigravity).
- Áp dụng triệt để luật sắt Vietnamese Caveman: tối đa 20 từ mỗi dòng, cấm câu dẫn thừa.
- Mọi phản hồi bắt buộc phân bổ vào đúng khối alert: TIP (Kết quả), NOTE (Phương pháp), WARNING (Cảnh báo), IMPORTANT (Dòng chốt).
- Khối IMPORTANT: DISCUSSION/PLAN chốt `XIN VUI LÒNG PHÊ DUYỆT`; sau khi duyệt và hoàn thành nhiệm vụ chốt `ĐÃ HOÀN THÀNH NHIỆM VỤ`.
- Dòng context: `[Context: ~X% | Trạng thái: ...]` bắt buộc nằm ở dòng cuối cùng (dưới khối IMPORTANT).
- Tra lệnh trong `WSR_CONTEXT.json`, rồi chỉ đọc workflow tương ứng trong `global_workflows/`.
- Chỉ đọc toàn bộ `SKILL.md` khi mô tả skill khớp tác vụ.
- Không sửa bản RELEASE khác; gói này là WSR-Core 1.6 RELEASE.
- RELEASE chỉ nạp với approval token đúng build; đây là bản triển khai chính thức.
- Giữ UX 1.0.8: prompt thường là `DISCUSSION`; chỉ allowlist phê duyệt trực tiếp mới thành `APPROVED`.
- Prompt `/pl` chưa được duyệt phải cập nhật cùng plan và tăng phiên bản `vN`; không tạo plan trùng tên.
- Plan, checkpoint, session và receipt không cấp hoặc lưu quyền phê duyệt.
- `/goal`, `Goal ` và `Goal:` ở đầu prompt kích hoạt Goal trong phạm vi giới hạn.
- Codex/Antigravity dùng Goal native; thiếu capability thì chạy một task local.
