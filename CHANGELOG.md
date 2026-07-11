# WSR 2.4.6 Hardened Changelog

## [2.4.6-v5] - 2026-07-12
- Final production hardening release.
- Upgraded checksum extra validation to reject self-checksum entries (WSR_CHECKSUMS.json hashing itself).
- Unified expected sources resolution excluding the checksums artifact itself.
- Passed 100% Doctor strict gates and Deep Audits.
- Enabled deterministic release packaging and transaction safety validations.

## [2.4.6-v4] - 2026-07-12
- Remediation release superseding v3.
- Completed checksum coverage by including debt_ledger.md (47 entries in total).
- Added extra checksum entries check in Doctor utility.
- Hardened sync mappings to raise ValueError on safety containment breaches and exit with code 4.
- Synced manifest CLI options to remove deprecated path mode and add --changed option.
- Added strict Draft-07 subset schema semantics verification (lowercase type assertions, recursive items, nested objects and type distinction).

## [2.4.6-v3] - 2026-07-12
- Remediation release superseding v2.
- Fixed JSON Schema v2 Draft-07 types (lowercase conversion).
- Hardened path containment check via os.path.realpath and os.path.commonpath.
- Upgraded doctor to validate manifest using physical schema and verify checksum coverage.
- Upgraded sync utility with unique transactional staging, backup naming, and reverse rollbacks.
- Improved clean utility JSON output mode and CLI contract arguments.
- Standardized packaging with deterministic ZIP metadata (timestamps and permissions).
- Removed hardcoded DOCS/WSR2.4.6 paths from workflows and documentation.

## [2.4.6-v2] - 2026-07-11
- Initial hardened version.
- Replaced manifest with Schema v2.
- Created platform adapter subsystem.
- Added path validation and common resolver.
- Upgraded doctor, clean, sync, audit, and packaging tools.
