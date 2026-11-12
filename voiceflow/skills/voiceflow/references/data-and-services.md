# Data and services

## What is installed

This package contains Markdown instructions and small setup utilities. Native
plugins also configure the public Voiceflow Knowledge MCP. Standalone skills
need a separate host-supported docs connection. The package has no background
service, independent analytics collector, or automatic updater.

The CLI is downloaded separately from Voiceflow's release distribution and
verified against pinned checksums. Skills are MIT-licensed, copyright
Voiceflow, Inc.; this license does not extend to the separately distributed CLI,
hosted Voiceflow services, or third-party agent clients. Their applicable terms,
licenses, permissions, and plan limits still apply.

## Account access

CLI and hosted account MCP use their respective browser OAuth flows. The account
MCP requests workspace read and write access. Setup only verifies account reads;
later tasks can change account data within the user's request and host controls.
Credentials are handled by the CLI or host, not stored in this package.

## Documentation requests and logging

The public docs MCP receives product questions without account authentication.
The skills ask assistants to send a focused question and a short tag with the
package version, active skill, and setup/troubleshooting/usage stage. The tag
carries no task, symptom, or setup state. Assistants must exclude credentials,
private code, customer transcripts, personal information, and account or project
identifiers.

Every docs connection this package creates, in native plugins and standalone
setup, uses `logging=off` in the server URL. That option turns off the docs
service's request logging for those connections. A docs connection the user
added by hand is reused as it is, and the docs service can log its requests:
redacted or truncated questions and context, tool, intent, response references,
confidence, errors, latency, and client/session information supplied by the
host. There are no separate progress events or fake questions for analytics.

This package does not set server-side retention. Public web/CLI documentation
is a fallback when docs MCP is unavailable, not a promise that those services
are unlogged. Use the
[Voiceflow Privacy Policy](https://www.voiceflow.com/privacy) for service-wide
data practices and privacy requests, and the
[Terms of Service](https://www.voiceflow.com/legal/terms) for hosted service use.
Your assistant provider has its own data handling policies.

## Removal and access revocation

[Uninstalling skills](../../voiceflow-setup/references/clients.md#updates-and-removal)
removes local guidance, not the CLI, OAuth grants, or server-side logs. Disconnect
MCP through your host's supported settings and use current Voiceflow/CLI auth
instructions for sign-out or access revocation; do not assume deleting a folder
revokes remote access. Ask [Voiceflow support](mailto:support@voiceflow.com) when
account access or a privacy request needs assistance.
