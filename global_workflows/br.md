---
description: Trigger brainstorm mode for discussions and minimal proposal review
---

# Quy trình Brainstorm `/br` (WSR Core 1.0)

Khi người dùng thảo luận hoặc hỏi đáp chung (mặc định chat xử lý như `/br`):

## Quy định thực thi
1. **Tuyệt đối cấm tự ý sửa đổi code:** Chỉ được sử dụng các công cụ đọc.
2. **Tuyệt đối cấm in code block:** Chỉ được liệt kê danh sách file tác động và gạch đầu dòng tính năng.
3. **Giới hạn hiển thị:**
   - Sử dụng ngôn ngữ tiếng Việt, phong cách Caveman (cực ngắn, dưới 20 từ/dòng, không từ nối).
   - Alert format:
     - `[HIỂU_YÊU_CẦU]` -> `> [!TIP]`
     - `[PHƯƠNG_PHÁP]` -> `> [!NOTE]`
     - `[CẢNH_BÁO]` -> `> [!WARNING]`
     - `[ĐỀ_XUẤT_TỐI_ƯU]` -> chữ thường.
4. **Dòng trạng thái cuối cùng:**
   - Luôn đặt dòng Context trước Important.
   - Dòng cuối tuyệt đối là:
     `> [!IMPORTANT]`
     `> VUI LÒNG XEM XÉT VÀ PHÊ DUYỆT!`
