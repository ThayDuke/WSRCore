# Kế hoạch rà soát và chuẩn hóa UltiTemp

Ngày lập: 2026-05-05

## Phạm vi

- Source template hợp lệ: `Template/UltiTemp.html`.
- Đường dẫn `Templates/UltiTemp` không tồn tại trong repo.
- Không sửa `.py`, `Tools/`, hoặc template khác trong lượt này.
- Phần Godmode chỉ áp dụng cho rà soát/sửa `.md` và `Docs`.

## Chẩn đoán

- `UltiTemp.html` là runtime template standalone, đang chứa 1 block CSS và 1 block JS lớn để phục vụ remaster/export bài học.
- Không phát hiện `style=` hoặc handler inline như `onclick=` trong HTML.
- CSS còn nhiều literal màu, shadow, gradient và một số nét `dashed`, chưa sạch theo DEC Master UI.
- JS có `.style.*` chủ yếu cho runtime measurement/animation: tạo bubble, clone kéo thả, fit-to-screen. Nhóm này được giữ nếu giá trị phụ thuộc kích thước thật của DOM.
- Theme toggle và Elegant override còn nhiều giá trị copy cục bộ; chưa nên tách file ngoài vì pipeline remaster hiện đọc `Template/UltiTemp.html` làm HTML standalone.

## Must Remain Unchanged

- Bố cục tổng thể, kích thước khung 900px, card, control bar, IPA mode, focus mode và theme Youth/Elegant.
- Marker data `// [DUKE PREVIEW DATA START]` và `// [DUKE PREVIEW DATA END]`.
- Tất cả `id`, class và API DOM đang được `DukeLauncher.pyw`/remaster script dùng.
- Runtime measurement trong JS được phép dùng style động khi lấy từ DOM rect hoặc random animation.
- Không đổi template khác và không đổi tool/script Python.

## Kế hoạch sửa tuần tự

1. Sửa mojibake/document encoding trong `.md` và `Docs`:
   - Quét UTF-8 bằng script đọc rõ encoding.
   - Sửa hai tài liệu có dấu `?` do mất dấu: `DOCS/INFO/DEC_UI_COMPONENT_CONTRACT.md`, `DOCS/remaster_all_tools.md`.
   - Giữ nguyên các chuỗi ví dụ mojibake có chủ ý trong rule/skill.

2. Chuẩn hóa token CSS trong `Template/UltiTemp.html`:
   - Bổ sung token cục bộ theo lớp `--ulti-*` tại `:root` và Elegant override.
   - Thay literal màu/gradient/shadow/border lặp lại trong selector bằng token.
   - Giữ nguyên giá trị thị giác hiện tại, chỉ đổi nguồn tiêu thụ sang token.

3. Sửa lỗi DMU rõ ràng:
   - Đổi toàn bộ `border-style: dashed` / shorthand dashed trong template sang solid.
   - Giữ độ dày, màu và spacing hiện tại để không làm lệch layout.

4. Dọn JS không đổi hành vi:
   - Xóa duplicate `btnSub.classList.remove('off')`.
   - Giữ `.style.*` phục vụ DOM measurement/drag clone/random bubble; không chuyển thành class giả gây sai runtime.

5. Kiểm tra hồi quy:
   - Quét lại `style=`, event inline, `dashed`, literal màu/shadow chính trong selector.
   - Extract JS từ template và chạy `node --check` nếu Node khả dụng.
   - Kiểm tra marker preview data còn nguyên.
   - Rà soát `git diff` để bảo đảm chỉ sửa đúng phạm vi.
