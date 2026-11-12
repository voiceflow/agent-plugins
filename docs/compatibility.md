# Compatibility and support

This is a beta package. The [CHANGELOG](../CHANGELOG.md) lists the current version.
This matrix was last reviewed on 2026-10-16, for 0.4.2. A source version is not a
published release. Support claims below distinguish
file installation, observed agent behavior, and real host onboarding.

| Surface | Current evidence | Status / limit |
| --- | --- | --- |
| Claude Code | Isolated native plugin installation, all sixteen skills, references, license notices, and docs MCP configuration | Packaging verified; full fresh-account OAuth and next-chat acceptance still required |
| Codex CLI | Isolated native plugin installation, all sixteen skills, references, license notices, and docs MCP configuration | Packaging verified; full fresh-account OAuth and next-chat acceptance still required |
| Cursor | Manifest checks and standalone skill installation | Experimental; interactive discovery not verified locally |
| Chat assistants with remote MCP | Capability-based setup guide and offline routing evaluations | Experimental; no named chat application's end-to-end onboarding is certified by these simulations |
| macOS arm64, Linux x86_64, Windows x86_64 | Checksum-verified installers and CLI contracts in local/three-OS CI checks | Installer evidence; not a guarantee for every host or architecture |
| Other pinned CLI architectures | Release checksums available | Not exercised by the recorded platform runs |
| CLI 0.287.0 | Account-read and widget request contracts exercised with a localhost fixture | Tested baseline; retain newer compatible installations |
| Standalone skills | Install, update, conflict preservation, removal, rollback, relative references, and license coverage | File installation verified; host-native discovery is a separate check |
| Product building and debugging | Authorized live CLI/MCP tasks and independent conversation checks | Task-specific evidence with failures and retests retained, not a universal success rate |
| Widget guides across eight platforms | Documentation review, package checks, and CLI fixtures | Experimental; live website and model acceptance cases remain unrun |
| Docs MCP use | Eight focused final runs on 0.4.1 with live public docs and simulated account state | Consultation/attribution evidence; not real OAuth or customer-resolution evidence |

The latest recorded native host versions were Claude Code **2.1.124** and Codex
CLI **0.162.0-alpha.2**. Minimum supported client versions are not established;
older clients may need the standalone path. Python **3.10+** is required for the
repository tools and standalone installer, not native plugin use or the CLI.

## Evidence and remaining acceptance

[Public installation verification](../evals/reports/2026-10-16-public-install.md)
records an anonymous clone and raw-reference retrieval, standalone installs for
all three clients, and isolated native Claude/Codex installation of 0.4.2.

[Historical verification](verification-history.md) retains previous package
results and limitations. The [acceptance protocols and reports](../evals/README.md)
record baseline failures separately from post-fix retests. Historical model
results are not relabeled as evaluations of the newest package.

Before promoting any path from experimental to supported, run fresh OAuth when
needed, live account verification, guidance discovery in a second conversation,
and representative tasks in that actual client. Unit tests and subagent
simulations cannot replace these checks. Public beta distribution may expose
experimental paths only with these limits stated.

Run local checks as described in [contributing](../CONTRIBUTING.md). Native host
verification uses disposable profiles. CLI contract tests use a local HTTP
fixture and fake credentials; repository tests do not sign in or change accounts.

## Known limitations

CLI 0.287.0 can return blank JSON output when its internal timeout cancels a
response between headers and body. Manual reads use typed TOON output. The
Python connection checker instead parses complete JSON on stdout without that
inner timeout and bounds the whole subprocess to 25 seconds. It rejects malformed,
truncated, and stderr-only responses. Localhost fixtures exercise split responses
and invalid bodies; this package does not patch the CLI.

Chat-only guidance may be session-scoped. A saved connector, sign-in badge, or
public docs response is not proof of working account access. Setup only claims
readiness after the actual account read and guidance checks.
