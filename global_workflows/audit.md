---
description: Run static integrity audit, encoding check, and WSR compliance tests
---

# Quy trình Audit & Kiểm tra chất lượng WSR (WSR Core 1.0)

Khi chạy lệnh `/audit` hoặc thực hiện kiểm tra chất lượng, Agent thực hiện:

## Bước 1: Quick Audit (Mặc định)
- Tự động chạy wsr_audit.py cho các file thay đổi:
  `python .agents/scripts/wsr_audit.py --changed`
- Nếu muốn audit đường dẫn chỉ định:
  `python .agents/scripts/wsr_audit.py --path [đường_dẫn]`
- Nếu muốn chạy Deep Audit toàn repo (yêu cầu User duyệt trước):
  `python .agents/scripts/wsr_audit.py --mode deep`

## Bước 2: Quét Nợ Kỹ Thuật (Debt Check)
- Chạy quét nợ ở chế độ Read-Only (mặc định):
  `python .agents/scripts/wsr_debt_scanner.py --check`
- Nếu muốn quét kèm theo file tài liệu:
  `python .agents/scripts/wsr_debt_scanner.py --check --include-docs`
- **Ghi kết quả vào Ledger:** Chỉ chạy khi User yêu cầu rõ ràng và được duyệt riêng:
  `python .agents/scripts/wsr_debt_scanner.py --write --output [ledger_path]`

## Bước 3: Xem điểm chất lượng
- Đọc Scorecard từ màn hình. Yêu cầu đạt 100/100 (hoặc WARN được giải thích rõ).
