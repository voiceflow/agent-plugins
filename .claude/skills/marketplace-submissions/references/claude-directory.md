# Claude directory

Portal: https://claude.ai/directory/manage, **Submit new**. A **plugin bundle**
is read from the GitHub repository. An **MCP connector** is one remote server
with its own listing. Submit everything from the same Claude organization so the
listings can be paired. Escalations: `mcp-review@anthropic.com`.

## Plugin bundle

| Field | Value |
| --- | --- |
| Repository | `https://github.com/voiceflow/agent-plugins` |
| Path | `voiceflow` |
| Branch or tag | The release tag |
| Icon | Locks at the first save. Use `voiceflow/assets/icon.png`. |

Voiceflow's organization is not verified with Anthropic, so the bundle may hold
only Markdown, text, JSON, YAML, PNG, JPEG, GIF, WebP, or ICO files, plus
LICENSE, README, and .gitignore. No file may start with `#!`, and the plugin may
have no hooks, commands, agents, themes, status line, or output styles. Run
`claude plugin validate ./voiceflow` before you submit.

"Connects to voiceflow-knowledge, Unregistered" means the docs server had no
directory listing. The published docs connector at the same URL pairs with it.

Version 1.3.0 was rejected with check `DP_TAG_BOUNCE`: the skills told Claude
to add the account server, and the plugin did not declare it. From 1.3.1,
`.mcp.json` declares it as `voiceflow` at the account connector's exact URL.
Expect "Connects to voiceflow, Unregistered" until that connector is published.
Shipped text gives only declared URLs; Cursor, GitHub Copilot, Windsurf, and
Antigravity are told to add `&dynamic=true`. `scripts/validate.py` enforces
both. The same review waived "Uses a credential from the user's machine" (the
CLI path) for 1.3.0.

Data handling answers. Confirm the under-18 answer with legal before you change it.

| Question | Answer |
| --- | --- |
| Reads or stores personal data | Reads only |
| Sends data to services other than its connectors | Yes. The README's "Data and services" section lists them. |
| How long it keeps data | Longer than the session. Voiceflow keeps account data and request logs. |
| Intended for people under 18 | No |

## Docs connector: Voiceflow Docs (published)

Listed at https://claude.ai/directory/voiceflow-docs. Keep these values for edits.

| Field | Value |
| --- | --- |
| Server URL | `https://www.voiceflow.com/docs/mcp?logging=off`, exactly. The plugin uses this URL, and the match pairs the listings. |
| Name | Voiceflow Docs |
| One-liner (129 of 200) | Answers questions about Voiceflow, its API, CLI, and MCP server from the public Voiceflow docs, with source links. No sign-in needed. |
| Categories | Developer tools |
| Icon | Leave the default, which is `www.voiceflow.com/favicon.png` |
| Documentation | `https://www.voiceflow.com/docs/mcp/knowledge` |
| Support, privacy | `support@voiceflow.com`, `https://www.voiceflow.com/privacy` |
| Enterprise managed auth documentation | Empty |
| Authentication | Not required |
| Read/write | Read only |
| Prerequisites | None. The server reads public Voiceflow documentation and needs no account or sign-in. |

Description:

```text
Voiceflow Docs answers questions about Voiceflow from its published website and documentation. It covers the product, the REST API, the vf CLI, the Voiceflow MCP server, and what changed in recent releases. Every answer carries a link to its source page.

Use it to learn how a Voiceflow feature works, to troubleshoot an error, or to check what changed. It can search the docs, read a page or one section, and list changelog entries.

All four tools are read-only and need no sign-in. The connector reads only public documentation. It cannot see your Voiceflow account. To work with your own agents, connect the Voiceflow connector as well.
```

Use cases. Each prompt returned a cited answer from the live server:

| Use case | Example prompt |
| --- | --- |
| Learn how a feature works | How do I add a website to my Voiceflow agent's knowledge base? |
| Set up a channel | How do I embed the Voiceflow chat widget on my website? |
| Check recent changes | What changed in Voiceflow this month? |

Avoid an API question as an example: a Dialog API question returned the
outbound calling page.

## Account connector: Voiceflow (in review)

| Field | Value |
| --- | --- |
| Server URL | `https://mcp.voiceflow.com/mcp?version=3` |
| Name | Voiceflow |
| One-liner (140 of 200) | Build, test, and improve Voiceflow AI agents in your workspace: prompts, playbooks, workflows, knowledge bases, transcripts, and evaluations. |
| Categories | Developer tools, Productivity |
| Author | Voiceflow, `https://www.voiceflow.com` |
| Icon | `mcp.voiceflow.com` has no favicon. Use the raw icon URL from SKILL.md as a custom icon. |
| Documentation | `https://www.voiceflow.com/docs/mcp/overview` |
| Support, privacy | `support@voiceflow.com`, `https://www.voiceflow.com/privacy` |
| Enterprise managed auth documentation | Empty |
| Authentication | OAuth with Dynamic Client Registration. Leave client ID and secret empty; the auth server issues only public clients. |
| Read/write | Read and write. Read tools are read-only; every write tool is destructive, so Claude asks first. |
| Prerequisites | A Voiceflow account with access to at least one workspace and agent. Users sign in with OAuth in the browser when they connect, and sign-in asks for workspace read and write access. The user's plan limits and workspace role apply. |

Description:

```text
Voiceflow is a platform for building and running AI agents for chat and voice. This connector gives Claude access to your Voiceflow workspace after you sign in with OAuth.

Claude can read your projects, agent instructions, playbooks, workflows, functions, knowledge base, variables, transcripts, tests, and evaluations. It can also make the changes you ask for, such as editing instructions, adding knowledge base documents, creating variables, running tests, and publishing an environment. Every change is a separate write tool, so Claude asks before it runs one.

The connector does not buy phone numbers, set secret values, or connect integrations that need live credentials. Do those in the Voiceflow app.

You need a Voiceflow account. Your plan's limits and your workspace permissions apply. Sign-in asks for workspace read and write access.
```

Use cases:

| Use case | Example prompt |
| --- | --- |
| Review an agent | List my Voiceflow agents and summarize the instructions of my support agent. |
| Debug from conversations | Show my support agent's most recent conversations and point out where it gave an unhelpful answer. |
| Make a change | Add a variable named order_id to my support agent. |

Risks a reviewer may raise:

- About 271 tools, against a reported claude.ai limit of about 256. Add it as a
  custom connector and check that a late tool such as `vf_variable_list` shows.
- Every tool needs a `title`; the portal's **Tools** step flags any that lack one.
- The server instructions tell Claude to call `vf_get_started` first, which a
  reviewer may read as steering tool choice.
- If Anthropic asks for test access, use the same reviewer account as OpenAI,
  entered only in the portal.
