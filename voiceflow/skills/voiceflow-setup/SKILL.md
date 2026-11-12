---
name: voiceflow-setup
description: Connect an assistant to Voiceflow using available account tools, hosted MCP, or a persistent CLI environment. Verify access and load guidance appropriate to this host. Use for initial setup or connection failures, not for building a project.
license: MIT
---

# Connect to Voiceflow

For questions about host connection requirements, OAuth, account access, or setup errors
that this skill does not answer, follow the
[docs MCP workflow](../voiceflow/references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Put only the package/skill/stage tag in `why`,
as described there. Reuse guidance for the same issue; consult it whenever unsure.

Follow the [canonical setup guide](references/setup.md) for the connection
decision tree, browser sign-in, persistence checks, and completion criteria.
Read it before configuring a connection or running setup commands.

Setup is complete only when a real account read succeeds and product guidance
can be used now. Persist skills where supported; accurately describe session-only
guidance in chat hosts. An empty workspace list is valid; public docs access alone
does not verify an account connection.
Do not pick a project, create a demo, publish, or run a conversation during setup.

Finish with: **You're connected to Voiceflow. What would you like to build or improve?**
