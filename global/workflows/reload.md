---
description: Nạp lại và ghi nhớ toàn bộ cấu hình, quy tắc (rules), kỹ năng (skills) và bài học (memory) từ thư mục .agents để cập nhật ngữ cảnh.
---

# Quy trình Reload Cấu hình, Skills và Rules V2.0

Khi người dùng yêu cầu "reload" hoặc nhập lệnh `/reload`, Agent phải thực hiện chính xác các bước sau đây để làm mới và đồng bộ lại toàn bộ ngữ cảnh vận hành:

## Bước 1: Nạp Quy tắc Toàn cục (Global Rules)
- Đọc và ghi nhớ quy tắc toàn cục `AG_GLOBAL_RULES.md` tại thư mục cấu hình toàn cục (thường là `~/.gemini/config/global_rules/` hoặc tương đương) nếu có, hoặc phiên bản local tại `.agents/global/rules/AG_GLOBAL_RULES.md`.
- Đọc và ghi nhớ file global config `GEMINI.md` tại thư mục cấu hình người dùng hoặc `.agents/global/GEMINI.md`.

## Bước 2: Xác định thư mục cấu hình cục bộ của Workspace
- Kiểm tra sự tồn tại của thư mục `.agents` ở thư mục gốc của workspace hiện tại.
- Nếu thư mục `.agents` tồn tại, chọn `.agents` làm thư mục tri thức chính của dự án.

## Bước 3: Đọc Core Rules & Workflows
- Đọc tài liệu quyết định: `.agents/rules/AG_DECISION_RULES.md`
- Đọc hướng dẫn: `AGENTS.md` tại gốc dự án (nay nằm trong `.agents/AGENTS.md`).
- Đọc workflow kiểm thử: `.agents/global/workflows/audit.md` (nếu có).

## Bước 4: Nạp Kỹ năng và Bài học theo Cấp độ (Tiered Loading)
Tùy thuộc vào lệnh của người dùng, thực hiện nạp các file tương ứng:

### 1. Cấp độ Tiêu chuẩn (Mặc định `/reload`)
Chỉ nạp các quy tắc cốt lõi và checkpoint để khôi phục nhanh ngữ cảnh mà không làm phình token:
- Các file ở Bước 1, Bước 2, Bước 3.
- Khối nén ngữ cảnh: `.agents/memory/project_checkpoint.yaml` (nếu có).
- *Không nạp* các file hỗ trợ gỡ lỗi, các file `SKILL.md` và `AG_LESSONS.jsonl`.

### 2. Cấp độ Chỉ định Kỹ năng (`/reload <tên_kỹ_năng>`)
Nạp các quy tắc cốt lõi (Cấp độ Tiêu chuẩn) + duy nhất file kỹ năng được chỉ định:
- Các skill toàn cục nếu được định nghĩa.
- Các skill cục bộ: nạp đúng file `SKILL.md` của skill tương ứng trong thư mục `.agents/skills/<tên_kỹ_năng>/` của dự án hiện tại.

### 3. Cấp độ Hỗ trợ Gỡ lỗi & Kiểm thử (`/reload debug` hoặc `/reload qa`)
Nạp các quy tắc cốt lõi (Cấp độ Tiêu chuẩn) + các tài liệu hỗ trợ gỡ lỗi và kiểm thử cục bộ:
- Các playbook gỡ lỗi cục bộ trong `.agents/rules/` (ví dụ: `local-debug-playbook.md` hoặc tương đương).
- Các checklist kiểm thử hồi quy cục bộ trong `.agents/rules/` (ví dụ: `regression-checklists.md` hoặc tương đương).
- Các mẫu prompt cục bộ (nếu có).

### 4. Cấp độ Đầy đủ (`/reload full`)
Nạp toàn bộ tài nguyên để thực hiện các phân tích hệ thống sâu:
- Tất cả quy tắc, checkpoint và tài liệu hỗ trợ (Playbook, Checklist, Mẫu prompt).
- Toàn bộ các file kỹ năng cục bộ.
- Nhật ký bài học: `.agents/memory/AG_LESSONS.jsonl`.

## Bước 5: Cơ chế nạp kỹ năng động (Dynamic Skill Selection)
- Mặc định sau khi `/reload`, Agent không nạp sẵn các file kỹ năng (skills) để tiết kiệm token.
- Khi nhận task, Agent đối chiếu yêu cầu với **Router Kỹ năng** trong [AGENTS.md](../../AGENTS.md) để tự động nạp duy nhất file kỹ năng phù hợp (chỉ nạp phần block liên quan nếu file kỹ năng có phân chia cấu trúc rõ ràng).


## Bước 6: Báo cáo kết quả và xác nhận
- Báo cáo chi tiết cho người dùng bằng tiếng Việt chuẩn có dấu, định dạng UTF-8.
- Liệt kê đầy đủ các file đã được đọc và ghi nhớ (kèm theo liên kết file dạng `[filename](file:///absolute/path)`).
- Xác nhận trạng thái sẵn sàng thực hiện các nhiệm vụ tiếp theo.
