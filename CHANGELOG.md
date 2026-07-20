# WSR Core Changelog

## [1.0.7] - 2026-07-20
- Fixed `wsr_doctor.py` to support Git submodule metadata by skipping root `.git` files.

## [1.0.6] - 2026-07-20
- Released the v2 cross-IDE loader contract for supported adapters.
- Scoped release gates to Codex, Gemini, Antigravity global, and Generic workspace.
- Classified Cursor and Claude as disabled, unsupported, and non-blocking.
- Accepted sandbox conformance plus official contract review as release UAT evidence.
- Fixed the packer to place the deterministic release ZIP in repository `DOCS/`.

## [1.0.5-review] - 2026-07-20
- Migrated every adapter to the exact v2 logical-root contract.
- Added workspace-safe generic support for IDE agents outside native adapters.
- Added absolute router rendering and schema-valid transactional active markers.
- Added source/runtime Doctor modes with D17-D32 conformance gates.
- Bound context, capability and release identities to SHA-256 content hashes.
- Added sandbox transaction, rollback and cross-IDE conformance evidence.
- Added SOURCE_VERIFIED and LOADED transitions to selective reload receipts.

## [1.0.3] - 2026-07-17
- Cập nhật quy trình /pl theo tiêu chuẩn handoff chi tiết.
- Phân biệt rõ tài liệu planning thủ công (không giới hạn dòng) và walkthrough.md (dưới 20 dòng).
- Cập nhật pack_wsr.py và wsr.md để luôn lưu zip release vào thư mục DOCS/ thay vì root.

## [1.0.2] - 2026-07-17
- Cập nhật Giao thức Tự vấn Bắt buộc (Cognitive Guardrail) chỉ thực hiện 1 lần ở thought đầu tiên.
- Bổ sung quy tắc Thought Caveman để giảm tiêu hao token.

## [1.0.1] - 2026-07-13
- Bổ sung Giao thức Tự vấn Bắt buộc (Cognitive Guardrail) vào GEMINI.md.
- Buộc Agent tự vấn kiểm tra quyền sửa đổi trước khi gọi tool hệ thống.

## [1.0.0] - 2026-07-13
- Established WSR Core as an independent Agent governance platform.
- Reset product identity, package naming, release paths, documentation, and runtime metadata.
- Preserved Smart Reload, strict Doctor, Deep Audit, drift detection, and JIT skills.

## [pre-1.0-v6] - 2026-07-13
- Remastered `/reload` as a read-only Smart Reload Gate.
- Added source locks, strict Doctor, adaptive Deep Audit, drift dry-run, and session receipts.
- Kept configuration deployment separate and skills JIT-loaded.

## [pre-1.0-v5] - 2026-07-12
- Final production hardening release.
- Upgraded checksum extra validation to reject self-checksum entries (WSR_CHECKSUMS.json hashing itself).
- Unified expected sources resolution excluding the checksums artifact itself.
- Passed 100% Doctor strict gates and Deep Audits.
- Enabled deterministic release packaging and transaction safety validations.

## [pre-1.0-v4] - 2026-07-12
- Remediation release superseding v3.
- Completed checksum coverage by including debt_ledger.md (47 entries in total).
- Added extra checksum entries check in Doctor utility.
- Strengthened sync mappings to raise ValueError on safety containment breaches and exit with code 4.
- Synced manifest CLI options to remove deprecated path mode and add --changed option.
- Added strict Draft-07 subset schema semantics verification (lowercase type assertions, recursive items, nested objects and type distinction).

## [pre-1.0-v3] - 2026-07-12
- Remediation release superseding v2.
- Fixed JSON Schema v2 Draft-07 types (lowercase conversion).
- Strict path containment check via os.path.realpath and os.path.commonpath.
- Upgraded doctor to validate manifest using physical schema and verify checksum coverage.
- Upgraded sync utility with unique transactional staging, backup naming, and reverse rollbacks.
- Improved clean utility JSON output mode and CLI contract arguments.
- Standardized packaging with deterministic ZIP metadata (timestamps and permissions).
- Removed hardcoded DOCS/WSR-Core paths from workflows and documentation.

## [pre-1.0-v2] - 2026-07-11
- Initial pre-1.0 foundation.
- Replaced manifest with Schema v2.
- Created platform adapter subsystem.
- Added path validation and common resolver.
- Upgraded doctor, clean, sync, audit, and packaging tools.
