---
name: marketplace-submissions
description: Submit, resubmit, or update this repository's Voiceflow plugin and its two MCP servers in marketplaces and directories - the Claude directory (plugin bundle and MCP connectors), the OpenAI plugin directory for ChatGPT and Codex, the Cursor Marketplace, the MCP Registry, awesome-copilot, and skills.sh. Use it when a maintainer asks how to publish or list the plugin, pastes a screenshot of a submission or review form (claude.ai/directory/manage, platform.openai.com/plugins, cursor.com/marketplace/publish), asks what to answer in a listing, data-handling, use-case, or review-details field, reports a rejection or reviewer feedback, asks to rebuild or bump the OpenAI ZIP, or asks for a status update on the listings. Do not use it to change the plugin's skills or code, or to cut a release; docs/releasing.md covers releases.
---

# Marketplace submissions

The repository owner submits; you prepare. Give exact field values to paste,
check every fact you can against the live system, and keep the submission kit
current. Never press submit or publish, and never change DNS.

## Ground rules

- **Submit from a release tag.** Every listing reads a tagged release. Check
  the latest first: `git fetch --tags origin && git tag --sort=-creatordate | head -3`.
- **Credentials go only into a portal's private field.** Reviewer emails,
  passwords, and invite links never go into this repository, a ZIP,
  `scripts/openai/review.json`, or a chat message. This repository is public.
- **Generated and private files live in `.submissions/`** at the repository
  root, which git ignores. Keep values that must not be public there, such as
  the team's status channel, the review workspace name, and where the registry
  key is kept, in `.submissions/private.md`. Read it when it exists.
- **Pin downloaded tools** to a version at least two weeks old and verify its
  checksum, for example `skills@1.8.1` and `mcp-publisher` 1.8.7.
- **Answer form questions per screenshot.** Give a table of field and value,
  paste blocks for long text, and the character count when the form shows a
  limit. Verify URLs and tool lists live before you give them.

## Shared facts

| Item | Value |
| --- | --- |
| Account MCP server | `https://mcp.voiceflow.com/mcp?version=3`. About 271 tools, OAuth with Dynamic Client Registration. |
| Account MCP, OpenAI package | `...?version=3&toolsets=project,agent,knowledge_base,transcript,variable,workspace`, in `scripts/openai/mcp.json`. 49 real tools once creator-app#24868 deploys, including the three workflow list tools. With the short instructions a `toolsets` connection gets, they measure 49,448 bytes against a 50,000-byte margin under Codex's 64,000-byte budget. That budget is shared by every installed plugin's MCP servers, so the margin is headroom, not a guarantee. Adding any other group goes over the margin. |
| Account MCP, dynamic mode | `...?version=3&dynamic=true`, about 12 tools plus search and call tools. Only for Cursor, GitHub Copilot, Windsurf, and Antigravity, which cap or trim long tool lists. Never for Codex or OpenAI: Codex does not list the call tools, and OpenAI forbids a generic executor. |
| Docs MCP server | `https://www.voiceflow.com/docs/mcp?logging=off`. Server name "Voiceflow Knowledge", four read-only tools, no sign-in. Keep `?logging=off`; without it the server logs questions. |
| Account MCP logging | No switch exists and none is needed. It logs the tool name, client, error flag, and duration, never arguments or results. |
| Docs pages | Account server `https://www.voiceflow.com/docs/mcp/overview`, docs server `https://www.voiceflow.com/docs/mcp/knowledge` |
| Support, privacy | `support@voiceflow.com`, `https://www.voiceflow.com/privacy` |
| Author | Voiceflow, `https://www.voiceflow.com` |
| Icon | `voiceflow/assets/icon.png`, 2000 by 2000 PNG. Raw URL: `https://raw.githubusercontent.com/voiceflow/agent-plugins/<tag>/voiceflow/assets/icon.png` |
| Short description | Connect to Voiceflow, then build and improve agents with shared product guidance. |
| Long description | `longDescription` in `voiceflow/plugin.json` at the tag. Copy it; do not retype it. |

## Where each listing stands

Status on 2026-11-24. Check the live state before acting on it.

| Listing | Status | Reference |
| --- | --- | --- |
| Claude: docs connector | Published at https://claude.ai/directory/voiceflow-docs | [claude-directory.md](references/claude-directory.md) |
| Claude: account connector | In Anthropic review | [claude-directory.md](references/claude-directory.md) |
| Claude: plugin bundle | 1.3.0 rejected because the plugin did not declare the account server. 1.3.1 declares it; resubmit from its tag. | [claude-directory.md](references/claude-directory.md) |
| OpenAI: plugin for ChatGPT and Codex | 1.2.1 rejected for its testing instructions. 1.2.2 was uploaded as a draft with the plain URL and showed only 32 tools in the desktop app. 1.3.1 uses the `toolsets` URL. Build it from the `v1.3.1` tag once the account server's short-instructions change is deployed, then upload it with the reviewer account's details. | [openai.md](references/openai.md) |
| Cursor Marketplace | Local test, then submit | [cursor.md](references/cursor.md) |
| MCP Registry | Waits on a DNS record and the owner's approval of the server names | [mcp-registry.md](references/mcp-registry.md) |
| awesome-copilot | Issue github/awesome-copilot#6477 passed intake and waits for a maintainer | [other-listings.md](references/other-listings.md) |
| skills.sh | No submission step | [other-listings.md](references/other-listings.md) |

## Known limits that cause rejections

- **Tool count.** The ChatGPT desktop app and Codex share one 64,000-byte
  budget across the MCP servers of every installed plugin. They count the
  server instructions once per tool and hide the tools that do not fit. With the plain URL only the `vf_agent_*`
  and `vf_analytics_*` tools show. The OpenAI package therefore lists six groups
  with `toolsets`, and the plugin works only in the desktop app, not on
  chatgpt.com. Users report that claude.ai loads about 256 tools.
- **Reviewer access.** OpenAI requires a dedicated account that works "without
  MFA approval, email or SMS codes, magic links". A workspace invite link was
  rejected for this.
- **Claude, unverified organization.** The plugin bundle may hold only
  Markdown, text, JSON, YAML, and images, no file that starts with `#!`, and no
  hooks, commands, agents, or other mods. `scripts/validate.py` enforces this.
  The icon locks at the first save.
- **Claude, undeclared servers.** Plugin text may tell Claude or the user to
  add only MCP servers that `.mcp.json` declares. 1.3.0 failed this check.
- **OpenAI packages** connect one MCP server, and each upload needs a higher
  version than the last.
