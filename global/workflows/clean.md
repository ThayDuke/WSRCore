---
description: Quét dự án và đề xuất danh sách các tệp tin tạm, rác để dọn dẹp tối ưu dung lượng (chế độ đề xuất trước, chờ duyệt sau).
---

# Quy trình Dọn dẹp Workspace (/clean)

Khi người dùng nhập lệnh `/clean`, Agent thực hiện việc dọn dẹp các tệp tạm, rác trong workspace để tối ưu hiệu năng:

## Bước 1: Quét tệp tạm, rác và file kế hoạch cũ
- Chạy script Python chuyên dụng để quét workspace:
  `python .agents/scripts/clean_dec.py`
- Script này sẽ:
  - Bỏ qua các thư mục whitelist: `.agents/`, `.git/`, `.vscode/`, `DATA/`, `ENGINE/`, `Template/`, `Tools/assets/`.
  - Quét các tệp rác: `desktop.ini`, `Thumbs.db`, `.DS_Store`, `__pycache__/`, `.pytest_cache/`, `*.log`, `*.tmp`.
  - Rà soát các file kế hoạch dạng `planning_*_v*.md` trong thư mục `DOCS/`, nhóm theo tên gốc và chỉ giữ lại file có phiên bản cao nhất, đề xuất xóa các bản thấp hơn.

## Bước 2: Báo cáo danh sách đề xuất
- Liệt kê chi tiết các tệp tin rác và file kế hoạch cũ tìm thấy, dung lượng chiếm dụng (nếu đo được).
- Tuyệt đối không tự ý xóa bất kỳ file nào khi chưa được User phê duyệt rõ ràng.

## Bước 3: Chờ phê duyệt của User và thực hiện xóa
- Yêu cầu User xác nhận danh sách tệp cần xóa.
- Khi User đồng ý (ví dụ gõ "ok", "làm đi"), chạy script xóa thực tế:
  `python .agents/scripts/clean_dec.py --delete`
