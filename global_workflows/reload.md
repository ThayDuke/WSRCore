---
description: Reload policies, skills, and memory context
---

# Quy trình Smart Reload `/reload` (WSR Core)

`/reload` chỉ xác minh nguồn và nạp context. Lệnh này không cài đặt, đồng bộ hoặc ghi file.

## Cổng thực thi
1. Xác định nguồn theo thứ tự: path người dùng, source lock, package chứa script. Cấm fallback mơ hồ.
   Source lock bắt buộc có `sourceRoot`, `version`, `buildId`, `manifestSha256`.
2. Chạy `scripts/wsr_reload.py` read-only. Doctor strict phải đạt 16/16 và 100/100.
3. Build mới so với target phải dùng `/reload --deep`. Đây là phê duyệt Deep Audit rõ ràng.
4. Sau trạng thái VERIFIED, Agent đọc đúng `coreFiles` từ receipt vào context.
5. Agent chỉ giữ `skillIndex`; nội dung skill tiếp tục nạp JIT theo nhiệm vụ.
6. Sync chỉ chạy dry-run để phát hiện drift. Cấm thêm hoặc suy diễn tùy chọn apply.

## Trạng thái
- VERIFIED: nguồn sạch; được phép đọc lõi.
- LOADED: Agent đã đọc đủ coreFiles và xác nhận trong chat.
- DRIFTED: source khác target; vẫn được nạp, nhưng không được tuyên bố đã đồng bộ.
- BLOCKED: sai identity, checksum, Doctor hoặc Deep Audit; cấm đọc nguồn đó.

## Biên nhận bắt buộc
Chỉ báo sourceRoot, version, buildId, manifest hash, Doctor score, Deep score, drift và coreFiles đã nạp.
