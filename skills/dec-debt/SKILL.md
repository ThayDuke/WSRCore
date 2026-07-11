---
name: dec-debt
description: >
  Quan ly no ky thuat DEC bang tag co trigger, ledger co score,
  va scanner co check/write mode an toan.
---

# DEC Technical Debt Immune Gate

Debt duoc chap nhan khi co gioi han va duong nang cap ro.

## Tag Schema
Dung cho code (Khuyen nghi chuyen sang wsr-debt):
`# wsr-debt: <mo ta>, ceiling: <nguong>, upgrade: <huong nang cap>`
(Migration note: legacy `dec-debt:` duoc coi la alias cua `wsr-debt:` nhung bi phan doi)

Khuyen nghi them:
- `owner: <nguoi/nhom>`
- `created: YYYY-MM-DD`
- `status: open|closed`

## Rule
- Thieu `ceiling:` hoac `upgrade:` = `[no-trigger]`.
- Debt moi co `[no-trigger]` = FAIL.
- Debt cu co `[no-trigger]` = WARN den khi duoc bo sung.
- TODO/FIXME/HACK trong code = WARN neu khong co owner/huong xu ly.

## Scanner
- `--check`: chi doc, in ket qua, khong ghi ledger.
- `--write`: ghi ledger mặc định tại `./debt_ledger.md` trong package root.
- `--root`: chi dinh project root.
- `--output`: chi dinh ledger path.
- `--include-planning`: cho phep quet markdown planning.

## Ledger Columns
- File
- Line
- Type
- Severity
- Owner
- Ceiling
- Upgrade
- Status
- Note

## Close Rule
Khi debt da xu ly:
- Xoa comment debt neu khong can.
- Hoac doi `status: closed` neu can lich su trong code.
- Ledger sinh lai tu scanner, khong sua tay neu co the.
