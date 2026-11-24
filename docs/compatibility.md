# Compatibility and support

Current package candidate: **0.4.2**, reviewed 2026-10-16. This is a beta package.
A source version is not a published release. Support claims below distinguish
file installation, observed agent behavior, and real host onboarding.

| Surface | Current evidence | Status / limit |
| --- | --- | --- |
| Claude Code | Isolated native plugin installation, all sixteen skills, references, license notices, and docs MCP configuration | Packaging verified; full fresh-account OAuth and next-chat acceptance still required |
| Codex CLI | Codex CLI 0.170.0 on macOS, 2026-11-24: installed 1.3.0 from GitHub, all eighteen skills listed, and the docs server answered. The account server was added with `codex mcp add` and signed in through OAuth. Codex listed 276 account tools and read workspaces, projects, and agent instructions through it, and again through CLI 0.287.0 | Install, sign-in, and account reads verified with an existing account; fresh-account onboarding not run |
| GitHub Copilot CLI | None recorded | Untested; the install commands follow GitHub's plugin documentation |
| Cursor | Manifest checks. The earlier skill-folder test used the installer removed in 1.1.1 | Experimental; team marketplace install, skills.sh, and interactive discovery not verified locally |
| Chat assistants with remote MCP | Capability-based setup guide and offline routing evaluations | Experimental; no named chat application's end-to-end onboarding is certified by these simulations |
| macOS arm64, Linux x86_64, Windows x86_64 | Checksum-verified installers in `scripts/cli/`, which run the setup skill's install steps line for line, and CLI contracts in local/three-OS CI checks | Installer evidence; not a guarantee for every host or architecture |
| Other pinned CLI architectures | Release checksums available | Not exercised by the recorded platform runs |
| CLI 0.335.0 | Help for every command the skills name, and the account-read and widget request contracts, exercised with a localhost fixture on macOS arm64 on 2026-11-23 | Tested baseline; retain newer compatible installations. CLI 0.287.0 passed the earlier contracts on 2026-10-16 |
| Account tools a host hides | A generated table maps each MCP tool to its CLI command; validation and the CLI contract check cover every row | The CLI fallback in Codex and the ChatGPT desktop app is not yet verified with a live model run |
| skills.sh | Unit tests copy each skill folder alone, as `--skill` does, and check that its references resolve | The skills CLI itself is not run by these checks |
| Standalone installer | Removed in 1.1.1. Earlier tests covered install, update, conflict preservation, removal, and rollback | No longer shipped |
| Product building and debugging | Authorized live CLI/MCP tasks and independent conversation checks | Task-specific evidence with failures and retests retained, not a universal success rate |
| Widget guides across eight platforms | Documentation review, package checks, and CLI fixtures | Experimental; live website and model acceptance cases remain unrun |
| Docs MCP use | Eight focused final runs on 0.4.1 with live public docs and simulated account state | Consultation/attribution evidence; not real OAuth or customer-resolution evidence |

The latest recorded native host versions were Claude Code **2.1.124** and Codex
CLI **0.170.0**. Minimum supported client versions are not established;
older clients may need skills.sh, which needs Node.js. Python **3.10+** is
required for the repository tools, not native plugin use or the CLI.

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

## MCP servers each host loads

Each host reads one MCP file from the plugin folder:

| Host | File | Servers |
| --- | --- | --- |
| Claude Code and the Claude apps | `.mcp.json` | Account server and docs server |
| Codex 0.170.0, Cursor, and GitHub Copilot CLI | `mcp.json`, through the Agent Plugins manifest | Docs server |
| Codex versions that read only `.codex-plugin/plugin.json` | `.codex-plugin/mcp.json` | Docs server |

Anthropic's plugin directory rejects text that tells Claude or the user to add
a server the plugin does not declare. So `.mcp.json` declares the account
server. The other files leave it out for two reasons. Codex counts the tools of
every server that installed plugins bundle against one shared 64,000-byte
budget, and hides the tools past it. Cursor and GitHub Copilot add
`&dynamic=true` to the account server URL. Claude Code 2.1.330 and Codex CLI
0.170.0 loaded these servers in disposable profiles on 2026-11-23. The Cursor
and GitHub Copilot CLI rows follow their documentation and were not run.

## Known limitations

CLI 0.287.0 and 0.335.0 can return blank JSON output when the internal timeout
cancels a response between headers and body. Manual reads use typed TOON output. The
JSON check in the setup skill's CLI guide leaves out that inner timeout and
stops the whole command after 25 seconds. A malformed, truncated, or
stderr-only response does not pass. `scripts/verify_cli.py` runs the same rule,
from `scripts/cli/check_connection.py`, against localhost fixtures with split
responses and invalid bodies. This package does not patch the CLI.

The ChatGPT desktop app and Codex cap the size of a plugin's tool list, so they
can hide most account tools, including the list tools and the account server's
docs tools. The skills then run hidden operations with the CLI. A host without
a terminal cannot do that, and setup cannot verify the account there. Through
CLI 0.335.0, `vf docs search` sends questions to the docs server without
`logging=off`, so the server logs them. The skills keep the docs MCP and the
account server's docs tools ahead of it.

Chat-only guidance may be session-scoped. A saved connector, sign-in badge, or
public docs response is not proof of working account access. Setup only claims
readiness after the actual account read and guidance checks.
