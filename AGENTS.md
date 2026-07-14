# WSR Core Global Instructions

> [!WARNING]
> **ĐÂY LÀ NGUỒN PHÁT HÀNH CHÍNH THỨC WSR CORE 1.0.0.**
> Mọi triển khai từ package này phải đi qua Doctor, checksum và quy trình sync có phê duyệt.

## 1. Cấu trúc Package WSR Core
- **Manifest:** [WSR_MANIFEST.json](./WSR_MANIFEST.json)
- **Workflows:**
  - `/audit` -> [audit.md](./global_workflows/audit.md)
  - `/br` -> [br.md](./global_workflows/br.md)
  - `/pl` -> [pl.md](./global_workflows/pl.md)
  - `/clean` -> [clean.md](./global_workflows/clean.md)
  - `/reload` -> [reload.md](./global_workflows/reload.md)
  - `/wsr` -> [wsr.md](./global_workflows/wsr.md)

## 2. Scripts Utility mới
- **Quét nợ:** [wsr_debt_scanner.py](./scripts/wsr_debt_scanner.py) (Chống false positive trong file `.md`).
- **Audit:** [wsr_audit.py](./scripts/wsr_audit.py) (Hỗ trợ quét theo path, kiểm tra moji-bake).
- **Dọn dẹp:** [wsr_clean.py](./scripts/wsr_clean.py) (Quét file rác an toàn theo whitelist).
- **Đóng gói:** [pack_wsr.py](./scripts/pack_wsr.py) (Tạo file nén đóng gói bản review).
- **Đồng bộ:** [sync_config.py](./scripts/sync_config.py) (Dry-run mặc định, sync khi có `--apply`).

## 3. Minimal Coding Protocol (Quy tắc YAGNI tích hợp)
- **Bậc 2 (Codebase reuse):** Tái sử dụng helper/util sẵn có của dự án trước khi viết mới.
- **Bậc 3 (Stdlib first):** Dùng thư viện tiêu chuẩn ngôn ngữ thay vì tự viết.
- **Bậc 4 (Native platform):** Tận dụng tính năng HTML5/CSS gốc, tránh cài dependency mới.
- **Sửa tận gốc:** Tìm và vá lỗi ở hàm dùng chung, không sửa triệu chứng ở từng caller riêng lẻ.
- **Nợ kỹ thuật:** Mọi giải pháp tạm thời phải đánh tag `# wsr-debt:` ghi rõ `ceiling` và `upgrade`.
