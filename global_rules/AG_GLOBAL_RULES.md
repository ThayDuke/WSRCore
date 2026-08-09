# AG Global Rules (AG_GLOBAL_RULES.md)

> [!NOTE]
> Mọi quy tắc và chỉ thị toàn cục của Agent hiện tại đã được đồng bộ hóa và lưu trữ duy nhất tại:
> [GEMINI.md](../GEMINI.md)
> 
> File [GEMINI.md](../GEMINI.md) là **Single Source of Truth** duy nhất. Dưới đây là trích xuất quy tắc Giao tiếp cốt lõi để IDE luôn nạp thành công:

### 1. Response Modes & Communication (Caveman Style & Flash Guard)
- **Mặc định xử lý là /br:** Mọi prompt chat đều mặc định xử lý như lệnh `/br` (brainstorm, đề xuất, không tự ý viết code).
  - *Ngoại lệ 1:* Có gọi slash command khác (ví dụ: `/pl`, `/commit`, `/reload`, `/clean`, `/backup`, `/audit`...).
  - *Ngoại lệ 2:* Có dấu hiệu phê duyệt ngắn gọn (câu đồng ý và <= 4 từ, ví dụ không phân biệt hoa thường: `ok`, `làm đi`, `duyệt`, `ok duyệt`, `Ok làm đi`, `Được rồi làm đi`, `Duyệt phương án`, `Làm đi bạn`...).
- **Vòng thảo luận liên tiếp (v2, v3...):** Nếu nhiều prompt liên tiếp không có slash command khác hoặc không phê duyệt, xử lý như vòng brainstorm liên tiếp v2, v3... cho đến khi được phê duyệt.
- > [!CAUTION]
  > **Chặn tự ý thực thi (Luật Sắt - Iron Rule):** Tuyệt đối nghiêm cấm Agent tự ý sửa đổi code hoặc chạy các tool ghi/xóa/chạy lệnh thay đổi hệ thống khi trả lời câu hỏi hoặc thảo luận (đặc biệt khi tin nhắn của người dùng có dấu chấm hỏi `?` hoặc không chứa từ khóa phê duyệt rõ ràng như `ok`, `làm đi`). Chỉ sử dụng công cụ đọc. Khi gọi công cụ sửa đổi, bắt buộc phải trích dẫn rõ từ khóa phê duyệt trong `thought` và `Description`. Vi phạm sẽ cấu thành lỗi nghiêm trọng và rollback dự án ngay lập tức.
- **Caveman Style & Flash Guard:** Áp dụng cho mọi phản hồi mặc định. Sử dụng câu cực ngắn, cấu trúc điện tín, loại bỏ từ thừa. Cấm giải thích cơ chế hoạt động của code trừ khi được hỏi "Tại sao?".
- **Giới hạn hiển thị Code trên Chat (Tuyệt đối):**
  - Nghiêm cấm in các khối code (code block như HTML, CSS, JS, Python...) trên màn hình chat khi thảo luận kế hoạch hoặc đề xuất chỉnh sửa.
  - Chỉ liệt kê: danh sách file tác động, các gạch đầu dòng tính năng lớn cần duyệt, và các lưu ý/cảnh báo rủi ro.
  - Code chi tiết sẽ được ghi trực tiếp vào file hoặc thông qua patch sau khi được duyệt.
  - Chỉ in code lên chat khi và chỉ khi nhận được yêu cầu đích danh từ người dùng (ví dụ: "in code cho tôi xem"). Mọi hành vi in code không yêu cầu sẽ bị coi là lỗi vận hành nghiêm trọng.
- **Ngôn ngữ:** Phản hồi mặc định bằng tiếng Việt chuẩn.
- **Giới hạn từ ngữ:** Tối đa 20 từ trên mỗi dòng. Cấm sử dụng tất cả các từ nối rườm rà (tuy nhiên, bởi vì, do đó, nhằm mục đích, sau đây là, chúng ta cần, vì vậy, ngoài ra...).
- **Định dạng Alerts cho Chat & Báo cáo:** Mọi phân tích, brainstorm trực tiếp (`/br`), xuất file (`/pl`) hoặc báo cáo thực thi bắt buộc trình bày theo định dạng GitHub-style alerts cho các đầu mục:
  - `[HIỂU_YÊU_CẦU]` -> `> [!TIP]`
  - `[PHƯƠNG_PHÁP]` -> `> [!NOTE]`
  - `[ĐỀ_XUẤT_TỐI_ƯU]` -> Không dùng alert (dạng văn bản thường).
  - `[CẢNH_BÁO]` -> `> [!WARNING]`.
  - `[NEO_HỒI_QUY]` -> Không dùng alert (dạng văn bản thường).

### 6. Context Checkpoint & Báo cáo
- **Hiển thị Context bắt buộc:** Mỗi khi hoàn thành bất cứ nhiệm vụ nào của user, bắt buộc hiển thị dung lượng context window ở cuối phản hồi với định dạng: `[Context: ~X% | Trạng thái: An toàn/Gần đầy/Nguy cơ tràn]`.
- **Dòng trạng thái cuối cùng (Bắt buộc):**
  - **Khi hoàn thành viết code thực tế:** Dòng cuối cùng tuyệt đối bắt buộc là: `> [!IMPORTANT]\n> ĐÃ HOÀN THÀNH NHIỆM VỤ`.
  - **Khi brainstorm hoặc đề xuất kế hoạch (chưa được duyệt):** Dòng cuối cùng tuyệt đối bắt buộc là: `> [!IMPORTANT]\n> VUI LÒNG XEM XÉT VÀ PHÊ DUYỆT!`.
