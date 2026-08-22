---
description: Hỗ trợ commit, push DEC-ALL, export sang DEC-Online, build index và push đồng bộ website.
---

# Quy trình Commit & Đồng Bộ Website (/commit)

Khi người dùng nhập lệnh `/commit`, Agent thực hiện quy trình tự động gồm 4 bước:

## Bước 1: Commit và Push nhánh main của repo hiện tại (DEC-ALL)
- Kiểm tra trạng thái: `git status`
- Stage và commit các file thay đổi:
  `git add -A`
  `git commit -m "<thông điệp commit>"` (dưới 10 từ theo chuẩn Conventional Commit: `type(scope): description`)
- Đẩy lên remote:
  `git push origin main`

## Bước 2: Đối chiếu và Export HTML sang DEC-Online & Build index.html
- Chạy script export chuẩn của hệ thống:
  `python APP/dev/scripts/GenerateIndexHTMLforWEB.py`
- Script thực hiện:
  - Đối chiếu và export toàn bộ các bài học HTML từ `CONTENT/levels/` sang `DEC-Online/CONTENT/levels/`.
  - Build lại file `index.html` độc lập (đã nhúng tài nguyên và lược bỏ tool offline) cho `DEC-Online`.
  - Tự động rollback an toàn nếu quá trình export gặp lỗi.

## Bước 3: Commit và Push nhánh main của repo DEC-Online
- Chuyển thư mục làm việc sang repo `DEC-Online` (`E:/0-DUKE-REPO/DEC-Online`).
- Kiểm tra trạng thái: `git status`
- Stage và commit:
  `git add -A`
  `git commit -m "sync(web): update lessons content and rebuild index.html"`
- Đẩy lên remote:
  `git push origin main`

## Bước 4: Báo cáo hoàn thành nhiệm vụ
- Tổng kết trạng thái commit và push của cả hai repo: `DEC-ALL` và `DEC-Online`.
- Xuất biên nhận hoàn tất.
