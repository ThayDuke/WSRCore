# DEC Cleanup Report

- Th?i ?i?m t?o: 2026-05-11T10:43:08
- Ch? ??: ch? ?? xu?t, ch?a x?a file n?o
- T?ng ?ng vi?n: 35
- T?ng dung l??ng c? th? xem x?t: 579.96 MB

## C?nh b?o v?n h?nh

- B?o c?o n?y ch? l? danh s?ch ?? xu?t. Kh?ng ???c x?a b?t k? m?c n?o n?u user ch?a x?c nh?n c? th?.
- C?c m?c li?n quan `Tools/`, `Template/`, `ENGINE/`, `QBank/`, `DATA/`, launcher, rule/skill/memory, config ho?c baseline ph?i ???c xem l? c? r?i ro v?n h?nh.
- `Temp/` l? ?ng vi?n cleanup ch?nh, nh?ng v?n c?n x?c nh?n tr??c khi d?n.

## T?m t?t theo nh?m

| Nh?m | S? m?c | Dung l??ng |
| --- | ---: | ---: |
| DOCS release bundle | 3 | 73.83 MB |
| Misc cleanup candidate | 4 | 0.12 MB |
| One-off tool candidate | 17 | 0.03 MB |
| QBank backup candidate | 1 | 52.99 MB |
| Temp cleanup candidate | 10 | 453.0 MB |

## Danh s?ch ??y ?? ?ng vi?n cleanup

| # | ???ng d?n | Lo?i | File con | Dung l??ng | R?i ro | H?nh ??ng ?? xu?t | L? do |
| ---: | --- | --- | ---: | ---: | --- | --- | --- |
| 1 | `Temp/production_excellence_95_phase12_postinstall` | dir | 833 | 152.18 MB | low | `delete_after_confirmation` | N?m trong Temp; th??ng l? artifact t?m t? audit, restore drill, postinstall ho?c cache. C?n x?c nh?n tr??c khi x?a. |
| 2 | `Temp/production_excellence_95_phase07_qbank_restore_drill` | dir | 17 | 110.6 MB | low | `delete_after_confirmation` | N?m trong Temp; th??ng l? artifact t?m t? audit, restore drill, postinstall ho?c cache. C?n x?c nh?n tr??c khi x?a. |
| 3 | `Temp/production_excellence_95_phase06_temp` | dir | 18 | 107.07 MB | low | `delete_after_confirmation` | N?m trong Temp; th??ng l? artifact t?m t? audit, restore drill, postinstall ho?c cache. C?n x?c nh?n tr??c khi x?a. |
| 4 | `Temp/production_excellence_95_phase06_import_warning` | dir | 11 | 72.51 MB | low | `delete_after_confirmation` | N?m trong Temp; th??ng l? artifact t?m t? audit, restore drill, postinstall ho?c cache. C?n x?c nh?n tr??c khi x?a. |
| 5 | `QBank/_topic_migration_backups` | dir | 5 | 52.99 MB | medium | `archive_or_delete_after_confirmation` | Backup ph? c?a QBank; li?n quan d? li?u v?n h?nh n?n ch? x?a sau khi user x?c nh?n r? kh?ng c?n rollback. |
| 6 | `DOCS/Releases/DEC_PRODUCTION_EXCELLENCE_95_RELEASE_BUNDLE_20260508_174506.zip` | file | 1 | 46.48 MB | low | `archive_or_delete_after_confirmation` | Release bundle n?n c? trong DOCS/Releases; c? th? chuy?n ra backup ngo?i repo ho?c x?a n?u kh?ng c?n c?n ??i chi?u. |
| 7 | `DOCS/Releases/DEC_PRODUCTION_EXCELLENCE_95_RELEASE_BUNDLE_20260508_174105.zip` | file | 1 | 13.68 MB | low | `archive_or_delete_after_confirmation` | Release bundle n?n c? trong DOCS/Releases; c? th? chuy?n ra backup ngo?i repo ho?c x?a n?u kh?ng c?n c?n ??i chi?u. |
| 8 | `DOCS/Releases/DEC_PRODUCTION_EXCELLENCE_95_RELEASE_BUNDLE_20260508_174207.zip` | file | 1 | 13.67 MB | low | `archive_or_delete_after_confirmation` | Release bundle n?n c? trong DOCS/Releases; c? th? chuy?n ra backup ngo?i repo ho?c x?a n?u kh?ng c?n c?n ??i chi?u. |
| 9 | `Temp/production_excellence_95_phase07_student_restore_drill` | dir | 346 | 10.58 MB | low | `delete_after_confirmation` | N?m trong Temp; th??ng l? artifact t?m t? audit, restore drill, postinstall ho?c cache. C?n x?c nh?n tr??c khi x?a. |
| 10 | `__pycache__` | dir | 3 | 0.11 MB | low | `delete_after_confirmation` | Artifact ph? kh?ng thu?c lu?ng v?n h?nh ch?nh; c?n x?c nh?n tr??c khi x?a. |
| 11 | `Temp/dashboard_sentence_count_cache_v2.json` | file | 1 | 0.06 MB | low | `delete_after_confirmation` | N?m trong Temp; th??ng l? artifact t?m t? audit, restore drill, postinstall ho?c cache. C?n x?c nh?n tr??c khi x?a. |
| 12 | `scratch` | dir | 4 | 0.01 MB | low | `delete_after_confirmation` | Artifact ph? kh?ng thu?c lu?ng v?n h?nh ch?nh; c?n x?c nh?n tr??c khi x?a. |
| 13 | `Temp/production_excellence_95_phase07_student_audit` | dir | 11 | 0.0 MB | low | `delete_after_confirmation` | N?m trong Temp; th??ng l? artifact t?m t? audit, restore drill, postinstall ho?c cache. C?n x?c nh?n tr??c khi x?a. |
| 14 | `Tools/DevTool/fix_listening.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 15 | `Temp/production_excellence_95_phase10_append_log` | dir | 10 | 0.0 MB | low | `delete_after_confirmation` | N?m trong Temp; th??ng l? artifact t?m t? audit, restore drill, postinstall ho?c cache. C?n x?c nh?n tr??c khi x?a. |
| 16 | `Tools/DevTool/clean_duplicate_questions.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 17 | `Tools/DevTool/UpdateHTMLTitles.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 18 | `Temp/DEC_Exam_B_Knowledge_06052026_140359.html` | file | 1 | 0.0 MB | low | `delete_after_confirmation` | N?m trong Temp; th??ng l? artifact t?m t? audit, restore drill, postinstall ho?c cache. C?n x?c nh?n tr??c khi x?a. |
| 19 | `Tools/DevTool/fix_ocd_toggle.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 20 | `Tools/assets/slide/fix_mojibake.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 21 | `Tools/DevTool/detect_duplicate_questions.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 22 | `Tools/DevTool/clean_fonts.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 23 | `Tools/assets/slide/parse_test.js` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 24 | `Tools/DevTool/fix_global_controls.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 25 | `Tools/DevTool/clean_fonts_js.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 26 | `Tools/DevTool/list_deleted_topics.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 27 | `Tools/DevTool/fix_theme_toggle.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 28 | `Tools/DevTool/restore_helpers.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 29 | `Tools/DevTool/list_empty_topics.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 30 | `Tools/DevTool/fix_init_order.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 31 | `Tools/DevTool/reconstruct_tool.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 32 | `Tools/DevTool/fix_zoom.py` | file | 1 | 0.0 MB | medium | `review_then_delete_after_confirmation` | C?ng c?/script c? d?u hi?u d?ng m?t l?n ?? troubleshoot/fix/chu?n h?a ph?m vi nh?; Agent c? th? t?i sinh n?u c?n, nh?ng c?n x?c nh?n tr??c khi x?a. |
| 33 | `Temp/desktop.ini` | file | 1 | 0.0 MB | low | `delete_after_confirmation` | N?m trong Temp; th??ng l? artifact t?m t? audit, restore drill, postinstall ho?c cache. C?n x?c nh?n tr??c khi x?a. |
| 34 | `Backups` | dir | 1 | 0.0 MB | low | `delete_after_confirmation` | Artifact ph? kh?ng thu?c lu?ng v?n h?nh ch?nh; c?n x?c nh?n tr??c khi x?a. |
| 35 | `desktop.ini` | file | 1 | 0.0 MB | low | `delete_after_confirmation` | Artifact ph? kh?ng thu?c lu?ng v?n h?nh ch?nh; c?n x?c nh?n tr??c khi x?a. |

## Khuy?n ngh?

1. ?u ti?n x?c nh?n d?n c?c m?c trong `Temp/` ?? gi?m dung l??ng nhanh v? ?t r?i ro nh?t.
2. Chuy?n ho?c x?a c?c `.zip` c? trong `DOCS/Releases/` n?u kh?ng c?n c?n ??i chi?u release.
3. Kh?ng x?a backup QBank n?u ch?a ch?c ch?n kh?ng c?n rollback d? li?u.
4. Kh?ng x?a script trong `Tools/DevTool/` n?u n? ?ang ???c release check, smoke test ho?c audit pipeline s? d?ng.
