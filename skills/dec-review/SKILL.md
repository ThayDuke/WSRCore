---
name: dec-review
description: >
  Review diff DEC de chan over-engineering, sua ngon, debt thieu trigger,
  va hoi quy hanh vi cot loi.
---

# DEC Review Immune Gate

Dung skill nay khi review diff, PR noi bo, hoac truoc khi bao hoan thanh.

## Input Can Co
- Diff hoac danh sach file da chinh.
- Muc tieu task.
- Failure Layer.
- Must remain unchanged.

## Seven-Gate Review
Kiem lan luot:
1. `goal:` Thay doi co dung muc tieu that khong?
2. `source:` Co sua dung file nguon khong?
3. `reuse:` Co viet lai helper da ton tai khong?
4. `stdlib:` Co tu viet logic ma stdlib da co khong?
5. `native:` Co dung dependency/JS/CSS thua thay vi native khong?
6. `risk:` Co cham shared/theme/export/encoding ma chua neu guard khong?
7. `shrink:` Co the xoa, gom, rut ngan khong?

## Tags
- `delete:` Code chet, fallback thua, flag chet.
- `reuse:` Logic da co trong codebase.
- `stdlib:` Tu viet lai chuc nang thu vien chuan.
- `native:` Co tinh nang nen tang thay the.
- `yagni:` Abstraction, class, file, config chua can.
- `shrink:` Logic dung nhung dai.
- `source:` Sua ngon, sai source-of-truth.
- `debt:` Debt thieu ceiling/upgrade.
- `risk:` Thieu regression guard.

## Severity
- **BLOCKER:** Co the gay fail hoac sai source.
- **WARN:** Nen sua truoc ship, nhung co the chap nhan neu co ly do.
- **NIT:** Rut gon nho, khong chan ship.

## Output
Moi dong phat hien:
`[SEVERITY] L<line>: <tag> <van de>. Thay the: <huong toi gian>. Guard: <khong doi gi>.`

Ket thuc:
- `Status: PASS/WARN/FAIL`
- `net: -<N> dong code co the cat`
- `Must remain unchanged: <danh sach ngan>`

Neu khong co van de:
`Lean already. Ship.`
