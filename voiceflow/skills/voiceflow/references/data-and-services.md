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
The skills ask assistants to send a focused question. Assistants must exclude
credentials, private code, customer transcripts, personal information, and
account or project identifiers.

Every docs connection this package creates, in native plugins and standalone
setup, uses `logging=off` in the server URL. With this option, the docs service
writes one anonymous count line per call. The line holds the tool name,
`logging: off`, a caller label, the error code, the duration, and whether the
call hit a cold start. The caller label for this package is `public`. The line
does not hold the question, search terms, `why`, `initiator`, `purpose`, client
name, session, result URLs, or answer confidence. In this mode the docs tools do
not ask for `why`, and the skills leave it out.

Vercel hosts the docs site and still records each HTTP request in its request
logs and firewall analytics. These hold the method, the path with its query,
the IP address, the user agent, the status, and the timing. The query shows
`logging=off`. They do not hold the request body, which carries the question.
The docs service's rate limiter keeps the IP address in memory for its time
window and does not log it.

A docs connection the user added by hand is reused as it is. It has no
`logging=off`, so the docs service logs its requests as before: redacted or
truncated questions and context, tool, intent, response references, confidence,
errors, latency, and client/session information supplied by the host. On such a
connection the tools require `why`. The skills then send only a short tag with
the package version, active skill, and setup/troubleshooting/usage stage, and no
task, symptom, or setup state. There are no separate progress events or fake
questions for analytics.

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
