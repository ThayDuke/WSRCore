# AG DEC Decision Rules (AG_DECISION_RULES.md)
*Single Source of Truth for AG's behavior in the Duke English Center (DEC) project*

> [!NOTE]
> File này kế thừa các nguyên tắc hoạt động toàn cục trong `AG_GLOBAL_RULES.md` và `GEMINI.md` (bao gồm: Caveman Style, Anti-Waste Prohibitions, Plan Approval Protocol và Operational Modes).

## 1. Pre-task Protocol (DEC-specific)
Before EVERY DEC task:
1. Load the active DEC skill (`SKILL.md`) and `AG_DECISION_RULES.md`.
2. Load `dec-debug-playbook.md` (Diagnostic Heuristics) ONLY if diagnosing a bug.
3. Access `AG_LESSONS.jsonl` (Memory) ONLY if pattern match is found.
4. Define **Failure Layer** (UI/Export/Shell/Logic).
5. For UTF-8 files containing Vietnamese, never round-trip the whole file through shell pipelines. Use localized patches, or an explicit UTF-8 script with before/after mojibake checks.
6. For new or updated Vietnamese-facing files, use standard Vietnamese with diacritics encoded as UTF-8. Do not use unaccented Vietnamese.

## 2. Core Principles (DEC-specific)
- **Sửa Gốc (Source First):** Fix the template/source, NOT the generated output. 
  - `DukeEnglishCenter.html` -> Source: `Template/Dashboard.css`, `Template/DashboardTemp.html`.
  - Tools (e.g. `ToolQuiz.html`) -> Check if it's a standalone tool or uses shared templates.
  - Final lessons (in level folders) -> Source: `Template/UltiTemp.html`, `Template/QTemp.html`, etc.
  - No-Tool Web build (`index.html`) -> Never fix directly. Fix the dashboard source and regenerate.
- **Micro-fix Prevention:** Do NOT "visually patch" without identifying the root cause layer.
- **Regression Guard:** Every fix must state "Must remain unchanged".
- **Vietnamese UTF-8 Standard:** Documentation, rules, skills, UI copy, business logs, checklists, and reports created for DEC must be written in proper accented Vietnamese. After writing a Vietnamese file, verify it decodes as UTF-8, contains no replacement character `U+FFFD`, contains no suspicious ASCII question mark `U+003F` replacing Vietnamese diacritics, and introduces no mojibake patterns (e.g. double-encoded UTF-8 strings). Valid Vietnamese words with characters like 'ã', 'Ã', 'â', 'Â' (e.g. "đã", "Đã", "ĐÃ HOÀN THÀNH NHIỆM VỤ") are fully allowed and should not trigger false positives.
- **Cấm tự động kiểm thử bằng Chrome (Anti-Waste & Browser Prohibition):** Tuyệt đối cấm sử dụng Chrome, `browser_subagent`, `open_browser_url`, hoặc `chrome-devtools-plugin` để tự động hóa hoặc chạy kiểm thử giao diện. Mọi xác nhận UI/logic phải do người dùng tự thực hiện thủ công qua 3 bước QA ngắn gọn.


## 2.5. Minimal Coding Protocol (Giao thức Code tối thiểu - DEC)
> [!WARNING]
> **CẢNH BÁO:** Agent bắt buộc tuân thủ giao thức code tối thiểu để bảo vệ hệ thống trước khi triển khai bất kỳ thay đổi nào.
> 
> 1. **Mục tiêu tối giản:** Sửa đúng gốc, ít dòng, ít file, ít rủi ro nhất.
>    - *Cấm tuyệt đối sửa ngọn:* Cấm dùng "sửa tối thiểu" làm lý do sửa ngọn (ví dụ sửa file build thay vì sửa file template). Sửa ngọn sẽ bị tính FAILED và rollback lập tức.
>    - *Cơ chế dung hòa đồng bộ:* Khi sửa UI bắt buộc đồng bộ theme Youth/Elegant và file template nguồn, được tính là 1 tác vụ đơn nhất.
>    - *Cơ chế dung hòa patch:* Ưu tiên localized patch (chỉ thay đổi khối cần thiết), nhưng code chèn bên trong patch bắt buộc hoàn chỉnh (không dùng placeholder).
>    - *Cơ chế dung hòa Godmode:* Khi kích hoạt Godmode cho phép sửa nhiều file nhưng vẫn phải tối giản tối đa số dòng code thay đổi.
> 2. **Xác định bắt buộc trước khi code (Chặn suy nghĩ từ đầu):**
>    - Mục tiêu thật của task.
>    - Failure Layer: UI, Logic, Export, Shell, Data, Config.
>    - File nguồn đúng cần sửa.
>    - Hành vi bắt buộc phải giữ nguyên (Regression Guard).
>    - Rủi ro hồi quy tiềm ẩn.
>    - Phương án ít thay đổi nhất.
> 3. **Cấm tuyệt đối:**
>    - Refactor lan rộng khi chỉ yêu cầu sửa nhỏ.
>    - Tạo class, service, framework nội bộ khi chưa cần thiết.
>    - Tách file mới chỉ để code trông "sạch" hơn.
>    - Viết logic fallback phức tạp khi nguyên nhân gốc đã rõ ràng.
>    - Thêm dependency ngoài nếu có thể dùng code hiện có.
>    - Chạm shared component khi task không yêu cầu.
>    - Sửa giao diện bằng cách hardcode giá trị tạm.
>    - Rewrite toàn bộ file để đồng bộ style.
> 4. **Trình bày phương án:** Phải ghi rõ: Sửa ở đâu, sửa gì, không đổi gì, vì sao tối thiểu.
> 5. **Quy tắc thực thi:** Tuân thủ localized patch, không đổi format hàng loạt, không đổi tên biến/API, không tối ưu giả định.
> 6. **Nguyên lý cốt lõi:** "Code tốt nhất là code không cần viết. Code tốt thứ hai là code nhỏ, đúng chỗ, dễ xoá."





## 3. DEC Master UI (DMU 2026) - TUYỆT ĐỐI KHÔNG HARDCODE
> [!IMPORTANT]
> - Mọi thay đổi UI dù là nhỏ nhất BẮT BUỘC phải sử dụng DEC Master UI làm nguồn chuẩn.
> - Ưu tiên dùng shared DMU tokens (`var(--dec-*)`), classes (`dec-ui-*`), và controls.
> - *Miễn trừ đặc biệt cho TG (ToolGame):* Được miễn trừ hoàn toàn mọi quy tắc DMU, cho phép thiết kế free style và tự do đề xuất các giải pháp sáng tạo về giao diện/phương pháp xử lý để game vận hành mượt mà.
> 
> [!WARNING]
> **NGHIÊM CẤM** việc hardcode màu sắc, shadow, spacing, typography (font-weight, font-size), border, gradient hoặc inline style trực tiếp. Nếu Token chưa có, Agent phải tự bổ sung vào `dec-ui-tokens.css` trước khi sử dụng. Việc dùng giá trị số trực tiếp thay vì Token sẽ bị coi là vi phạm nguyên tắc vận hành.

## 4. Icon-free UI Standard (DMU 2026)
> [!IMPORTANT]
> - Tuyệt đối không sử dụng icon cho Tiêu đề (H1, H2...), Nhãn (Label), Nút bấm (Button), hay các Tab.
> - Chỉ sử dụng icon khi có yêu cầu cụ thể. Khi đó, phải đánh dấu bằng comment `[DMU-EXCEPTION]` trong code để nhận diện.
> - Áp dụng cho thay đổi MỚI; không cần quét fix các icon cũ trừ khi được yêu cầu.

## 5. Quy chuẩn Thiết kế UI Giao diện (Youth & Elegant)
Khi thực hiện các thay đổi liên quan đến giao diện người dùng, Agent phải tuân thủ triệt để:

> [!IMPORTANT]
> **Đồng bộ Theme (Youth & Elegant):** Tuyệt đối không chỉ sửa trên một theme. Khi thay đổi bất kỳ thuộc tính nào ảnh hưởng đến kích thước hoặc vị trí (padding, line-height, margin...), phải cập nhật đồng thời cho cả theme **Youth (mặc định)** và **Elegant**. Điều này nhằm triệt tiêu hoàn toàn hiện tượng lệch UI, jitter (nhảy layout), hoặc flicker (nháy hình) khi người dùng chuyển đổi qua lại giữa các giao diện.

1. **Tính chuyên nghiệp:** Không sửa hardcode trung gian, không sử dụng "ép" vị trí (ví dụ dùng `top: 13px`), không overlay đè lên nhau. Mọi thay đổi phải dựa trên hệ thống class, tokens và tuân thủ quy tắc trình bày chuyên nghiệp, không chắp vá tạm bợ.
2. **Tính nhất quán toàn hệ thống:** Khi bổ sung item mới (nút bấm, nhãn, dropdown...), phải rà soát các công cụ khác (ToolListening, ToolSlide, ToolExam...) để tái sử dụng thiết kế đã có. Nếu item chưa từng tồn tại, hãy dựa trên quy chuẩn thiết kế của các item sẵn có về tone màu, kích thước và hành vi để tạo ra item mới đồng nhất.
3. **DEC Master UI (DMU) chỉ số:**
   - **Chỉ số Khung (Container):** `max-width: 900px`, `margin: 0 auto 20px`, `border-radius: 22px`, `padding: 22px`, `gap: 14px`, `box-shadow: 0 22px 50px rgba(28, 62, 95, 0.16)`.
   - **Chỉ số Thẻ (Card/Section):** `border-radius: 18px`, `padding: 16px`, `accent-bar height: 6px`, `accent-bar color: #e91e63 -> #00acc1` (Youth).
   - **Thành phần Form (Form Elements):** `Input/Select height: 40px`, `padding: 0 12px`, `Textarea padding: 12px`.
   - **Typography (H1 & Labels):** 
     - `H1`: `Be Vietnam Pro`, `text-transform: none`, `margin-bottom: 8px`, `zoom: 0.7`.
     - `Main Label`: `font-weight: 800`, `text-transform: uppercase`, `margin-top: 24px`, `margin-bottom: 10px`.
     - `First Label`: `margin-top: 8px !important` (để khớp khoảng cách với accent bar).
     
> [!WARNING]
> - **NGHIÊM CẤM:** Không sử dụng font Sora hoặc bất kỳ font legacy nào khác.
> - **TUYỆT ĐỐI** không dùng `padding` cho các nhãn (label) tiêu đề nếu không cần thiết, tránh lệch vertical alignment.

## 6. Neo Hồi quy Kỹ thuật (Behavioral Memory Anchors)
Bắt buộc bảo toàn các hành vi logic ngầm định sau đây của hệ thống DEC:
- **Cấu hình Server Local:** Khởi chạy localhost luôn sử dụng cổng kết nối cố định `6868`.
- **Cấu hình Ẩn Console Windows:** Khi khởi động server, bắt buộc sử dụng `ctypes.windll.user32.ShowWindow` kết hợp `kernel32.GetConsoleWindow` và tham số `0` để ẩn console hoàn toàn.
- **Xử lý Tách câu Âm thanh:** Logic phân tách câu âm thanh phải loại bỏ hoàn toàn tiền tố tên người nói (ví dụ: "A:", "B:") trước khi nạp vào TTS.

## 7. Quy trình Backup DEC
### 7.1. Full Backup (Khi sửa hệ thống lớn)
1. **Script chuẩn:** Sử dụng Python script [backup_dec.py](file:///h:/My%20Drive/1.%20DEC-Good/.agents/scripts/backup_dec.py) để nén toàn bộ thư mục gốc dự án.
2. **Vị trí lưu:** Luôn lưu vào thư mục `h:/My Drive/1. DEC-Good/Backups/`.
3. **Đặt tên:** Định dạng `DEC_FULL_BACKUP_YYYYMMDD_HHMMSS.zip`.
4. **Loại trừ (Exclusions):** Bắt buộc loại trừ `.venv`, `.git`, `__pycache__` và chính thư mục `Backups`.
5. **Xác nhận:** Báo cáo chính xác tên file và vị trí lưu sau khi hoàn thành.

### 7.2. DEC Backup Shortcut (bak dec* / backup dec*)
- Save the `.zip` file to `E:\BACKUP DukeEnglishCenter`.
- Exclude `.git`, `.venv`, `__pycache__` từ zip file.
- Định dạng tên file: Sử dụng văn bản đi kèm sau phím tắt, hoặc mặc định `DEC_ddMMyyyy_HHmmss.zip`.

### 7.3. Cấm tự ý Backup
- Tuyệt đối cấm Agent tự động chạy script backup (ví dụ: `backup_dec.py`) hoặc đưa tác vụ backup vào `task.md` khi sửa đổi hệ thống.
- Việc sao lưu và phục hồi code do Git đảm nhiệm.
- Backup (Bak) chỉ được thực hiện khi người dùng gọi lệnh thủ công hoặc yêu cầu trực tiếp.

## 8. DEC Abbreviations
- `TL`: ToolListening | `TQ`: ToolQuiz | `TS`: ToolSlide | `TE`: ToolExam | `TA`: ToolAdaptive | `TQI`: ToolQbankImport | `GL`: Game Lobby | `GC`: Game Castle | `GB`: Game Battle | `DMU`: DEC Master UI | `Theme Y`: Youth theme | `Theme E`: Elegant theme | `wsr` / `wrs`: Bộ ba 'Workflow, Skill, Rule' / 'Workflow, Rule, Skill'

## 9. Context Integrity & Recovery (DEC-specific)
> [!IMPORTANT]
> **Self-Audit Trigger:** Nếu một Task kéo dài quá 3 lượt phản hồi hoặc sửa đổi trên > 3 file, Agent **BẮT BUỘC** phải rà soát lại `Regression Guard` (Mục "Stay Unchanged") trước khi thực hiện bước tiếp theo.
- **Context Refresh:** Khi bắt đầu một session mới, Agent tự nhắc bản thân về **Failure Layer** và tự động nạp file `.agents/memory/project_checkpoint.yaml` để khôi phục nhanh ngữ cảnh.
- **Header Persistence:** Tuyệt đối không bỏ qua Header báo cáo (trừ Micro-mode).
  ```text
  Mode: [Isolation/Godmode] | Layer: [UI/Export/Shell/Logic]
  Target: [Target file] -> [Brief symptom & fix]
  ```
- **User Signal & Tiered Reload:**
  - Lệnh `/reload` (không phân biệt chữ hoa/thường):
    - **Chế độ Tiêu chuẩn (Mặc định `/reload`):** Nạp `AG_GLOBAL_RULES.md`, `GEMINI.md`, `AGENTS.md`, `AG_DECISION_RULES.md`, `dec-debug-playbook.md`, `regression-checklists.md` và `project_checkpoint.yaml`. Không nạp kỹ năng hay bài học.
    - **Chế độ Chỉ định Kỹ năng (`/reload <tên_kỹ_năng>`):** Nạp các quy tắc chế độ Tiêu chuẩn + duy nhất 1 file kỹ năng được chỉ định (operator, stitch, output, redesign, soft).
    - **Chế độ Đầy đủ (`/reload full`):** Nạp toàn bộ quy tắc, tất cả 5 file kỹ năng, `AG_LESSONS.jsonl` và `ag-prompt-patterns.md`.
  - Sau khi nạp, chỉ hiển thị xác nhận ngắn gọn "Đã đọc và ghi nhớ skill & rules" kèm danh sách file, không tóm tắt nội dung để tiết kiệm tối đa quota và context.

## 10. Resolving Rule Conflicts & Overlaps (Quy tắc xử lý giao thoa)
> [!IMPORTANT]
> Khi xảy ra mâu thuẫn giữa luật hiển thị code của GEMINI.md và quy định Full-Output của output-skill.md:
> 1. **Thảo luận & Lập kế hoạch:** Tuyệt đối không in các block code lên chat. Chỉ liệt kê file tác động và tính năng chính (tuân thủ GEMINI.md).
> 2. **Ghi/Sửa file thực tế:** Viết code hoàn chỉnh, đầy đủ vào file, không sử dụng placeholder hoặc comment rút gọn (tuân thủ output-skill.md).
> 3. **In code lên chat:** Chỉ thực hiện khi người dùng yêu cầu rõ ràng bằng từ khóa ("in code cho tôi xem").
> 4. **Quy trình lập kế hoạch:** Không tạo file `implementation_plan.md` vật lý (Quy trình Cách 3). Trình bày trực tiếp trên chat và chờ duyệt. Khi đã duyệt, tạo/cập nhật file `task.md` vật lý để theo dõi tiến độ.
> 5. **Mặc định xử lý prompt là /br:** Tất cả prompt đều mặc định brainstorm trừ khi có slash command khác hoặc nhận được tín hiệu phê duyệt ngắn gọn (<= 4 từ, ví dụ: `ok`, `làm đi`, `duyệt`, `ok duyệt`, `Ok làm đi`...).
> 6. **Vòng thảo luận liên tiếp (v2, v3...):** Nếu nhiều prompt liên tiếp không phê duyệt hoặc không gọi slash command khác, xử lý như vòng thảo luận v2, v3... cho đến khi phê duyệt. Với `/pl`, tạo và tăng phiên bản file kế hoạch `planning_[tên]_v2.md`, `planning_[tên]_v3.md`...
> 
> [!NOTE]
> **Quy chuẩn hiển thị Alerts cho /br và /pl:**
> - `[HIỂU_YÊU_CẦU]` -> `> [!TIP]`
> - `[PHƯƠNG_PHÁP]` -> `> [!NOTE]`
> - `[ĐỀ_XUẤT_TỐI_ƯU]` -> Không dùng alert (dạng văn bản thường).
> - `[CẢNH_BÁO]` -> `> [!WARNING]`
> - `[NEO_HỒI_QUY]` -> Không dùng alert (dạng văn bản thường).

## 11. Quy chuẩn Layer Địa hình (GB)
- Cơ chế quản lý ảnh xếp chồng theo từng lớp (layer):
  - `layer0`: Lớp dưới cùng (terrain nền mặc định, gạch nền...). Không thể thực hiện hạ cấp (`layer-`).
  - `layer1`, `layer2`...: Các lớp đè lên trên tiếp theo (crater, oasis, units...).
  - `layertop`: Lớp trên cùng hiện tại của ô. Không thể thực hiện tăng cấp (`layer+`).
- Khi thao tác thay đổi:
  - `layer-1`: Hạ ảnh xuống 1 cấp layer (ví dụ: layer2 xuống layer1).
  - `layer+1`: Tăng ảnh lên 1 cấp layer.

