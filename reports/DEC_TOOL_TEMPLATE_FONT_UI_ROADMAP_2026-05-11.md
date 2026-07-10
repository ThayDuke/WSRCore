# Roadmap rà soát font và UI cho Tools/Template DEC

## Phạm vi

- Tool authoring: `ToolListening`, `ToolQuiz`, `ToolSlide`, `ToolExam`, `ToolAdaptive`, `ToolQBankImport`.
- Template sinh bài: `UltiTemp`, `QTemp`, `AdaptiveTemp`, `DashboardTemp`.
- Shared DMU: `Tools/assets/shared/`, `Tools/assets/vendor/dec-offline-fonts.css`.

## Baseline audit

- `mojibake_audit.py --no-report`: PASS, chưa phát hiện mojibake trong source scope.
- Smoke modules: ToolSlide, ToolExam, ToolListening, ToolQuiz, ToolAdaptive, ToolQBankImport đều PASS.
- `ui_hygiene_audit.py --no-report`: font assets DMU PASS; còn nhiều hardcode CSS là audit debt hiện hữu, chưa phải release-blocking theo script.
- Rủi ro chính đã xác định: HTML standalone của ToolSlide phụ thuộc link `/tools-assets/vendor/dec-offline-fonts.css`; khi mở file ngoài launcher, font DMU có thể không tải.

## Roadmap & workflow

### Task 1 - ToolSlide standalone font

Mục tiêu: file HTML xuất từ ToolSlide tự nhúng font DMU khi chạy qua launcher, vẫn giữ fallback link khi không fetch được.

Workflow:
1. Thêm helper trong `Tools/assets/slide/tool-slide-runtime.js` để fetch `dec-offline-fonts.css` và font TTF, chuyển thành data URI.
2. Cho `buildLessonRuntimeHtml()` nhận `fontCss` tùy chọn và nhúng vào `<style>`.
3. Cập nhật `Tools/assets/slide/tool-slide.js` để `handleExport()` chờ helper font trước khi tạo Blob.
4. Test ToolSlide smoke, mojibake audit, và test sinh HTML có tiếng Việt.

Must remain unchanged: parser/schema ToolSlide, dữ liệu slide JSON, điều hướng slide, theme toggle Youth/Elegant.

### Task 2 - Contract export qua launcher

Mục tiêu: xác nhận `/generate_slide`, `/generate_quiz`, `/generate_html` vẫn trả UTF-8 sạch và không làm hỏng title/nội dung tiếng Việt.

Workflow:
1. Dùng Flask test client kiểm tra `Content-Type`, `<meta charset>`, nội dung tiếng Việt, và marker mojibake.
2. Nếu phát hiện route nào thiếu charset hoặc ghi sai UTF-8, sửa tại route/source builder tương ứng.
3. Chạy launcher contract snapshot hoặc route smoke phù hợp.

Must remain unchanged: response format, filename slug, validation chống `</script>`.

### Task 3 - Template font surface

Mục tiêu: bảo đảm `UltiTemp`, `QTemp`, `AdaptiveTemp` và shell linked/inline đều gọi font DMU đúng nguồn.

Workflow:
1. Kiểm tra shell/template có link font offline và `<meta charset="UTF-8">`.
2. Kiểm tra inline builders đọc UTF-8 và không round-trip sai encoding.
3. Nếu cần sửa, sửa ở shell/source template, không sửa output generated.
4. Chạy smoke/release checks liên quan sau mỗi sửa.

Must remain unchanged: placeholder `lessonData`, `fullQuestionBank`, `injectedAdaptiveMeta`, `injectedAdaptiveConfig`.

### Task 4 - UI DMU hygiene có rủi ro cao

Mục tiêu: chỉ fix ngay các UI vi phạm có tác động trực tiếp đến font/layout hiện tại; ghi nợ còn lại nếu là hardcode legacy diện rộng.

Workflow:
1. Ưu tiên `legacy_font`, dashed/dotted border, inline style/event, local toggle CSS blocking.
2. Với hardcode màu/px cũ số lượng lớn, không bulk rewrite nếu chưa có token mapping an toàn.
3. Nếu sửa UI, thêm token vào `dec-ui-tokens.css` trước rồi dùng `var(--*)`.
4. Test tool liên quan trước khi chuyển task.

Must remain unchanged: layout container/card DMU, theme Youth/Elegant, không thêm icon mới.

### Task 5 - Regression suite cuối

Mục tiêu: xác nhận toàn bộ Tools/Template ổn sau các fix.

Workflow:
1. Chạy `mojibake_audit.py --no-report`.
2. Chạy smoke từng tool.
3. Chạy `ui_hygiene_audit.py --diff-aware`.
4. Chạy release checks chọn lọc nếu không phát sinh lỗi môi trường.

Must remain unchanged: các file user-owned đang deleted trong `DOCS/` không bị đụng tới.
