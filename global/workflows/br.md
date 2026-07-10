---
description: Brainstorm trực tiếp tại chat (phân tích cách hiểu, phương pháp, đề xuất tốt nhất, cảnh báo và chờ phê duyệt, TUYỆT ĐỐI không tự ý sửa code).
---

# Quy trình Brainstorm trực tiếp tại Chat V2.0 (/br)

Khi người dùng nhập lệnh `/br` hoặc yêu cầu bắt đầu bằng `/br`, Agent bắt buộc phải thực hiện quy trình sau để đảm bảo an toàn hệ thống và tối ưu hóa giải pháp:

## Bước 1: Khởi tạo Ngữ cảnh & Risk Gate (On-demand Context Loading)
- **Tự động nạp Quy tắc & Playbook cục bộ (JIT)**:
  - Nếu tác vụ liên quan tới dự án DEC: Nạp `.agents/rules/AG_DECISION_RULES.md`.
  - Nếu là gỡ lỗi (debug/fix bug): Nạp thêm `.agents/rules/dec-debug-playbook.md`.
  - Nếu sửa đổi giao diện hoặc logic (UI, Logic, Export): Nạp thêm `.agents/rules/regression-checklists.md`.
  - Để học hỏi kinh nghiệm cũ: Chỉ truy vấn bài học liên quan bằng cách chạy `grep_search` trên `.agents/memory/AG_LESSONS.jsonl` với tên file cần chạm hoặc từ khóa lỗi. Tuyệt đối không đọc toàn bộ file `AG_LESSONS.jsonl` qua `view_file`.
  - Tải trạng thái checkpoint nếu cần khôi phục ngữ cảnh: `.agents/memory/project_checkpoint.yaml`.
- Chấm rủi ro qua 5 yếu tố: file, layer, dùng chung, tiếng Việt, phê duyệt.
- Xác định Risk Level: LOW, MEDIUM, HIGH.
- Nếu HIGH: Khuyên dùng `/pl` ngay, dừng brainstorm sâu.
- Chỉ nạp các block kỹ năng liên quan trong `SKILL.md` (Router Kỹ năng).
- Ước lượng % context window.
- **Tư duy tối thiểu (Chặn từ đầu):** Xác định rõ Mục tiêu thật, Failure Layer (UI, Logic, Export, Shell, Data, Config), File nguồn đúng cần sửa (cấm sửa ngọn), Hành vi giữ nguyên, Rủi ro hồi quy và Phương án ít thay đổi nhất.

## Bước 2: Phân tích và trình bày Brainstorm (Sử dụng XML Tags ẩn)
Trình bày rõ ràng và mạch lạc trực tiếp trên giao diện chat 5 nội dung sau bằng cú pháp Markdown Alert để tô màu nổi bật (TUÂN THỦ không xuất code và bắt buộc tuân theo phong cách Caveman, tối đa 20 từ/dòng, cấm từ nối rườm rà):
* `> [!TIP]` bọc nhãn `[HIỂU_YÊU_CẦU]`: Phân tích bản chất cốt lõi của vấn đề. Đính kèm Điểm tin cậy (Confidence Score) từ 1-10. Nếu điểm số < 8, dừng lại và hỏi rõ.
* `> [!NOTE]` bọc nhãn `[PHƯƠNG_PHÁP]`: Vạch ra các bước giải thuật hoặc phương tiếp cận kỹ thuật. Ưu tiên giải pháp đơn giản nhất, ít dòng code nhất. Trình bày ngắn gọn:
  - Sửa ở đâu (file, hàm).
  - Sửa gì (mô tả cụ thể).
  - Không đổi gì (vùng neo hành vi).
  - Vì sao đây là cách tối thiểu.
* `[ĐỀ_XUẤT_TỐI_ƯU]`: Khuyến nghị giải pháp tốt nhất kèm phân tích Ưu/Nhược điểm siêu ngắn gọn (dạng văn bản thường, không dùng alert).
* `[CẢNH_BÁO]`: Nêu rõ rủi ro vỡ giao diện (jitter, layout), xung đột biến, hoặc ảnh hưởng đến hiệu năng.
* `[NEO_HỒI_QUY]`: Chỉ định chính xác hành vi hệ thống và các thành phần logic bắt buộc giữ nguyên không được phép thay đổi (dạng văn bản thường, không dùng alert). Cấm dùng tối thiểu để sửa ngọn.

## Bước 3: Dừng lại và Chờ phê duyệt (MANDATORY HALT)
- Hiển thị thông điệp: `> [!IMPORTANT]\n> VUI LÒNG XEM XÉT VÀ PHÊ DUYỆT!`
- Cuối phản hồi, hiển thị dòng trạng thái định dạng: `[Context: ~X% | Trạng thái: An toàn/Gần đầy/Nguy cơ tràn]` (Ước lượng context nếu được).
- **Tín hiệu phê duyệt ngắn gọn (<= 4 từ):** Câu đồng ý không phân biệt chữ hoa thường (ví dụ: `ok`, `làm đi`, `duyệt`, `ok duyệt`, `Ok làm đi`, `Được rồi làm đi`, `Duyệt phương án`, `Làm đi bạn`...). Khi nhận được tín hiệu này mới được phép triển khai code.
- **Vòng thảo luận liên tiếp:** Nếu người dùng gửi prompt tiếp theo không chứa tín hiệu phê duyệt hoặc slash command khác, Agent tiếp tục xử lý như vòng thảo luận brainstorm v2, v3... cho đến khi nhận được phê duyệt.
- **TUYỆT ĐỐI KHÔNG** tự ý triển khai viết code, chỉnh sửa file khi chưa được phê duyệt trực tiếp qua các câu lệnh trên.
- **Định tuyến thông minh (Escalation):** Tự động đề xuất người dùng chuyển sang lệnh `/pl` nếu tác vụ ảnh hưởng/sửa đổi từ 3 file trở lên hoặc cấu trúc logic có độ phức tạp cao.

