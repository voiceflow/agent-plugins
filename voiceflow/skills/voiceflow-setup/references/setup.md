# Connect your assistant to Voiceflow

Prepare Voiceflow for the user, using the capabilities actually available in
this conversation. Complete mechanical steps yourself where supported. Keep
progress short; ask the user only for an unavoidable sign-in, host setting, or
missing detail. Do not ask them to choose between CLI and MCP.

Use the guide and linked files from the supplied checkout, repository revision,
or versioned website bundle. Do not assume the default branch or an unpublished
website URL contains the requested version. Package licensing, account permissions,
and docs request handling are described in
[data and services](../../voiceflow/references/data-and-services.md).

For every new Voiceflow setup blocker or connection error, consult the
[docs MCP workflow](../../voiceflow/references/documentation.md) before proposing
or applying recovery, even if this guide suggests the fix. Follow its rule for
`why` on every docs request, including the documentation check below: leave an
optional `why` out, and fill a required one with only its package tag and
`skill=voiceflow-setup stage=setup`. Public docs need no account sign-in.
If the docs connection itself fails, use the workflow's bounded recovery and
official-docs fallback; do not loop trying to ask a broken server how to repair
itself.

## 1. Inspect capabilities and reuse connections

Inspect the host's available tools and connector inventory, including deferred
tool discovery when available. Do not infer capabilities from a model name,
brand, or a claim that the assistant is a coding agent.

Distinguish:

- Account tools that read or change the user's Voiceflow account.
- Public documentation tools, which need no account and do not prove sign-in.
- Host tools that can add/authenticate a remote connection.
- Terminal/file tools that can install in the customer's persistent environment.
  A temporary code interpreter or remote scratch sandbox does not qualify.
- Ways to read guidance: web fetch, authenticated repository access, attached
  files, MCP resources, or documentation tools.

If Voiceflow account tools already exist, inspect their schemas and make one
read-only workspace-list request, or a project-list/account read that needs no
user-selected project. Use the actual tool name and arguments, never guess them.
A valid account response, including an empty list, verifies the connection.
Skip a new connector, CLI install, and sign-in, and continue to step 3.
For a failed MCP read, use [MCP recovery](mcp.md#verification-and-recovery).

## 2. Choose the supported connection path

| Observed capability | Next step |
| --- | --- |
| A working account connection | Reuse it; go to step 3 |
| No account connection; a persistent customer terminal is available | Follow the [CLI path](cli.md), unless the user requested MCP or this host already has a configured Voiceflow MCP connection to repair |
| No usable terminal; remote MCP can be connected by a tool or host settings | Follow the [MCP path](mcp.md) |
| Only web/docs access; host connection support is unknown | Check the host's current official connection instructions if accessible; ask which app the user is using only if that is the missing fact |
| Host cannot connect account tools or run the CLI | Explain that this chat can offer guidance but cannot connect to or act on their account; give the smallest supported next step |

Follow only the chosen path. Do not download an archive or provide shell
commands to a chat-only assistant. A successful public docs request, saved
configuration, sign-in badge, or user saying "done" is not account verification.
If the user must change a host setting or sign in, wait for that action, then
rediscover tools and verify a live account read. Do not restart setup from scratch.

## 3. Make guidance available in this host

Make the **docs MCP a standard companion to either account MCP or CLI**.
Reuse an existing Voiceflow Knowledge connection; native plugins bundle its
public server. After plugin installation or discovery, verify a real docs tool
response. If absent, follow [documentation connection](mcp.md#documentation-connection)
using this host's supported connection tools/settings. No OAuth or API key is
needed. Do not skip it merely because the package Markdown is readable.
Use one useful question to verify documentation access, such as how draft and
published environments differ. Fill `why` only as the docs workflow says.
Never describe the setup state or whether the account read succeeded.
Reuse this result in step 4; do not send a second check or a success-report query.

Read the [entry skill](../../voiceflow/SKILL.md) and its
[operation contract](../../voiceflow/references/operations.md). Follow specialist
links only when a later task needs them. These are Markdown instructions; a
native skill loader is not required to read them.

**Clients with persistent skill/plugin support:** use [client installation](clients.md)
for this host only. If already installed, reuse the adjacent files. Use the same
repository revision as the guide; an accessible checkout needs no additional
GitHub sign-in. If repository access is restricted, use an existing authenticated
reader or supplied files rather than requesting a token.
For the published website bundle, download sibling `voiceflow.zip` and
`manifest.json` from the same `/agents/` location and verify the archive SHA-256
before extraction. Preserve user changes and avoid duplicate plugin/skill installs.
Confirm the entry skill and linked files exist; report any pending host reload.

**Chat assistants:** read the linked Markdown through the available fetch or
repository tool. Resolve relative links from the fetched file's location.
No clone, ZIP, filesystem, or persistent skill installation is required.
If an existing Knowledge MCP exposes `voiceflow://skill`, read it as maintained
product guidance; it is not proof that this repository's packaged skills are
installed or that the account is connected. If resource reads are unavailable,
use available documentation tools or web pages; do not require resource support.
See [chat guidance alternatives](mcp.md#guidance-without-a-filesystem) when the
linked files cannot be read. Reuse an existing docs connection rather than
adding duplicates. If the host cannot expose docs MCP, verify the public-docs
or CLI-docs fallback and accurately describe that limitation; do not block
otherwise usable account access or claim the docs MCP is connected.

Repository access can fail independently of Voiceflow sign-in. Use an
existing authenticated repository connection or ask for the guide and linked
Markdown as attachments. Never ask for a GitHub token in chat or claim the
unpublished website bundle exists. If no guidance source is accessible, report
that the account is connected but guidance setup is incomplete.

## 4. Verify and hand over

Setup is ready for this conversation when:

1. An actual read of the user's Voiceflow account succeeded in this session.
2. Guidance is readable now: load this package's entry/operation instructions
   when accessible, and verify a real docs MCP tool response (for example, how
   draft and published environments differ). If docs MCP is unsupported or
   unavailable, verify the public-docs/CLI-docs fallback and state the limitation.
   Readable packaged skills alone do not verify live documentation access.
3. Persistence is stated accurately: installed where supported, or available
   in this chat with future discovery dependent on the host. Do not promise
   future chats inherit a read page or invent a memory/skill installation tool.

If guidance is session-only, say so briefly before the completion question.
If a host needs a new chat to expose account tools, give the minimal resume
instruction and leave account verification pending. Never claim setup complete
without the live read. An empty account is valid; do not create, select, or ask
the user to choose a workspace/project, run a test, or publish during setup.

Once ready, end with exactly:

> You're connected to Voiceflow. What would you like to build or improve?

Wait for the answer. No sample project, task menu, or discovery interview should
come before that question.
