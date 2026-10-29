---
name: voiceflow-integrations
description: Connect Voiceflow integrations, API tools, MCP tools, and secret-backed credentials. Use for external services or missing tool connections.
license: MIT
---

# External services

For questions about supported integrations, authentication, API tools, or remote MCP capabilities
that this skill does not answer, follow the
[docs MCP workflow](../voiceflow/references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Include package/skill/stage context in `why` as
described there. Reuse guidance for the same issue; consult it whenever unsure.

For embedding an agent on a website, use [Widget](../voiceflow-widget/SKILL.md).
This skill connects services used by the agent, rather than installing its UI.

Read the [operation contract](../voiceflow/references/operations.md). Inspect
available integrations and their schemas before writing a custom API/function.
A connection is not an attached agent tool: verify both.

Attaching an integration tool takes two steps. First add it with
`voiceflow_integration.add_tool`, using a `toolName` that
`voiceflow_integration.get_schema` lists. It returns the tool's
`integrationToolID`; for a tool already added it returns the existing ID and
changes nothing. It refuses an integration the workspace does not have enabled;
say so and choose another kind of tool. Then attach it with
`voiceflow_tool.create`, type `integration`, and wire its inputs and outputs.
CLI 0.287.0 has no command for the first step; the user adds the tool in the
agent's Tools in the Voiceflow UI. The tool works only once the integration is
connected, so connect it first.

Use an existing integration when it supports the task; an API tool for a plain
request; a function for logic; an MCP tool for a supported remote capability.
Do not confuse the coding agent's Voiceflow MCP connection with an MCP server
that the customer is adding to their Voiceflow agent.

The user completes third-party OAuth or enters secret values in the secure
Voiceflow interface. Never request credentials in conversation. If the public
API cannot establish a connection, give the precise remaining UI step, then
resume inspection after it exists. Don't invent a private connection helper.
The MCP refuses to carry credentials. Hand a secret value or an api-key
connection to the user as a `vf` command they run in their own terminal, and
send OAuth and app integrations to the Voiceflow UI, as the
[CLI handoffs](../voiceflow/references/cli-handoffs.md) describe. The same file
covers MCP server headers. A handed-over command is not a connection: confirm
it with a read afterwards.

API-tool fields reference the tool's declared input variables. Bind project
variables or secrets through defaults on each attachment, not by assuming a
URL token can read all project state. Use [wiring](../voiceflow-wiring/SKILL.md).

Secret names may be shared while values differ by environment. Publishing
does not promote Draft credentials to Default credentials. Check whether a
value exists without retrieving or printing it.

A configured request is not proof of a successful integration. Inspect schemas
and bindings first; when authorized to test, choose a harmless read if possible.
Never send an email, payment, deletion, or other side effect solely to validate
connectivity.

Sources: [API tool](https://www.voiceflow.com/docs/documentation/build/tools/api-tool),
[Secrets](https://www.voiceflow.com/docs/documentation/build/data/secrets).
