# WSR Core Changelog

## [1.6] - 2026-08-31
- Standardized version specification to two-segment `x.y` format (discontinued `x.y.z`).
- Remastered `README.html` using the enhanced Liquid Glass optical framework (directional Fresnel borders, layered chromatic dispersion shadows, 20px squircles).
- Integrated comprehensive interactive version changelog and multi-generation comparison table into `README.html`.
- Streamlined Slash Command catalog from 11 to 9 workflows (pruned legacy `/wsr` and `/backup`).
- Updated schemas (`wsr-manifest-v2`, `wsr-context-v2`, `wsr-active-v1`, `wsr-session-v1`) and Doctor `D02_SEMANTIC_IDENTITY` check for `x.y` version format.
- Released official WSR-Core 1.6 package (`WSR-CORE-1.6-RELEASE`).

## [1.5.0] - 2026-08-28
- Released WSR-Core 1.5.0 with mandatory context telemetry and preflight guidance.
- Added mandatory context percentage reporting after every response.
- Added projected task preflight and early handoff guidance.
- Preserved 60% warning, 75% handoff, and 85% critical thresholds.

## [1.4.1-review] - 2026-08-28
- Refactored oversized clean, doctor and reload entrypoints.

## [1.4.0-review] - 2026-08-27
- Restored 1.0.8 Caveman UX, approval allowlist, alert mapping and plan continuation semantics.
- Added bounded `/goal`, Goal ledger/schema, scope guard, task receipts and Codex/Antigravity native handshakes.
- Added context thresholds, approval parser, conformance fixtures, strict Goal Doctor gate and evidence-bound packaging.

## [1.2.0-review] - 2026-08-27
- Rebuilt `wsr-audit` as a deterministic, read-only six-category audit.
- Added stable findings, severity scoring, report schema, dependency checks, and fixtures.
- Preserved the existing CLI and separated Audit from Doctor, Debt, and Review.

## [1.1.0-review] - 2026-08-27
- Replaced bulk startup loading with five enforced layers and per-profile token budgets.
- Made `WSR_CONTEXT.json` the only command registry and reduced the kernel to seven rule IDs.
- Added session descriptor v1 with workspace containment and no persisted authority.
- Added adapter v3 multi-root bindings for native Codex and Antigravity discovery.
- Removed false `LOADED` receipts; added `VERIFIED`, `RESUME_READY` and `RESTART_REQUIRED`.
- Added native-path, collision, orphan, semantic-version and duplicate-rule gates.

## [1.0.8] - 2026-08-20
- Added Section 10: Autonomous Task Ledger & Subagent Protocol to GEMINI.md and AG_GLOBAL_RULES.md.
- Standardized Orchestrator - Subagent Worker pattern for large-scale tasks (>= 20 items / batch processing).
- Defined safe context threshold gate (>= 60%) and seamless session handoff via persistent disk ledger.

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
