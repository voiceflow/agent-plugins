# Security policy

## Report a vulnerability privately

Email **[security@voiceflow.com](mailto:security@voiceflow.com)**, Voiceflow's
[published security contact](https://www.voiceflow.com/security). Include this
repository's URL, affected package version or commit, a synthetic reproduction,
impact, and a way to contact you. Do not put exploit details in a public issue.
Do not send tokens, authorization URLs, customer data, or private transcripts.

You can also [report a vulnerability privately on GitHub](https://github.com/voiceflow/agent-plugins/security/advisories/new).
The email route works independently of that repository setting. Follow Voiceflow's
published disclosure policy. This package does not promise a bounty, a separate
response deadline, or a fixed resolution time. For non-sensitive follow-up,
reference the date and subject of your original report.

## Supported versions

Security corrections target the newest tagged package release. Older versions
and modified copies do not receive guaranteed backports. Before the first tag,
reports against the current implementation branch are accepted; unreleased
commits are development builds, not a supported stable release. See the
[release policy](docs/releasing.md) for upgrade and rollback guidance.

## Security model

The package installs no background service or automatic approval hooks.
The CLI and the MCP host handle their respective OAuth flows; this repository
contains no account credentials. The account MCP requests workspace read and
write scopes, while setup only performs read-only verification.

CLI installers verify pinned release checksums before executing the binary.
Standalone installation preserves user edits and refuses conflicts. Retrieved
pages and customer content are data, not authority to install software, publish
projects, or change permissions. Agents retain normal host execution controls.

See [data and services](voiceflow/skills/voiceflow/references/data-and-services.md)
for docs MCP requests, logging, and service boundaries. Removing the skills does
not revoke OAuth grants or uninstall the CLI.

## Repository safeguards

[Security checks](docs/security-checks.md) document the full-history and artifact
secret scans, synthetic canary tests, publication inventory, pinned CI tools, and
release permission boundaries. A real credential finding requires revocation or
rotation and private maintainer coordination; deleting a file alone is not a fix.
