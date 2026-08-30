---
description: Auto-detect latest release and execute configuration sync without prompt re-approval
---

# /sync

Dry-run trước bằng `scripts/sync_config.py`. Chỉ `--apply` khi user cho phép trong tác vụ hiện tại và approval token khớp build. REVIEW cần thêm `--allow-review`. Không có force-sync; sau khi đổi router phải khởi động phiên IDE mới.
