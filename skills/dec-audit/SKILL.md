---
name: dec-audit
description: >
  Audit DEC theo immune gate: quick, debt, deep. Tim complexity,
  debt, encoding risk, dependency thua, va sai source-of-truth.
---

# DEC Audit Immune Gate

Dung skill nay cho audit chat, `/audit`, hoac audit folder nhap WSR.

## Mode
- `quick`: File thay doi hoac path chi dinh. Mac dinh.
- `debt`: Chi quet no ky thuat.
- `deep`: Repo-wide. Can phe duyet khi ton nhieu thoi gian hoac ghi file.

## Hunt Targets
- Dependency khong dung hoac co native/stdlib thay the.
- Helper viet lai logic co san.
- File chi boc mot gia tri don gian.
- Config/flag khong bao gio doi.
- Fallback dai khi root cause da ro.
- Debt thieu `ceiling:` hoac `upgrade:`.
- File doc loi UTF-8, mojibake, U+FFFD.
- Sua artifact thay vi source.

## Score
- **PASS:** Khong blocker.
- **WARN:** Co warning co the chap nhan.
- **FAIL:** Co blocker.

## Output Bat Buoc
- Status.
- Scope.
- Blockers.
- Warnings.
- Quick wins.
- Net reduction estimate.
- 3 QA thu cong toi da.

## Khong Lam
- Khong tu ghi file khi chi audit.
- Khong chay test suite lon.
- Khong quet repo-wide neu user chi can quick.
- Khong de xuat refactor lon neu fix nho du.
