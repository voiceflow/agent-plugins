# OpenAI plugin directory (ChatGPT and Codex)

Portal: https://platform.openai.com/plugins. Docs:
https://developers.openai.com/plugins/deploy/submission. Only one review can be
active per plugin.

## Before the first upload

| Item | State |
| --- | --- |
| Business verification | https://platform.openai.com/settings/organization/general. Needs the org owner or the Apps Management Write role. |
| Domain check | `https://mcp.voiceflow.com/.well-known/openai-apps-challenge` returns the token. |
| One MCP server | The account server, limited to six groups with `toolsets`: `scripts/openai/mcp.json`. The docs server is left out; the skills fall back to the account server's `vf_docs_*` tools. |
| Tool budget | The desktop app hides tools past 64,000 bytes, a budget shared by every installed plugin's MCP servers. A `toolsets` connection gets short server instructions, which keeps the six groups at 49,448 bytes. That includes the three workflow list tools, which creator-app#24868 lists on `toolsets` connections. `tests/test_openai_package.py` fails when a test case names a tool outside those groups. To add a group, measure it first with the account server's budget test. |
| No generic executor | OpenAI's guidelines forbid a tool that runs operations not exposed one by one, which rules out `dynamic=true`. |

## Build the ZIP

```bash
git fetch --tags origin
scripts/openai/build_zip.sh v1.3.1
```

- The script exports the tag's `voiceflow/` folder and removes the files for
  other hosts. It swaps in `scripts/openai/mcp.json` (account server only),
  merges `scripts/openai/review.json` into `plugin.json` under
  `extensions.com.openai`, and validates the result. The ZIP lands in
  `.submissions/openai/`, which git ignores.
- The build must report 0 errors and 0 blockers. `package_tools.py` fails
  credentials, hooks, `.app.json`, extra MCP servers, and broken links. It also
  fails test cases that name a tool the server does not serve, and release
  notes that do not mention the version.
- **Version:** each upload needs a higher version than the last. 1.2.2 was
  the last upload. `package_version` in `review.json` sets the version in the
  ZIP. It is 1.3.1, the same as the repository release the ZIP is built from.
  When an upload needs a new version, change it in the release notes too.
- Run Gitleaks over `.submissions/openai/package` when it is installed. If it
  is not, say so in the report instead of downloading an unpinned binary.

## Review details (portal only)

OpenAI's rule: "Provide a dedicated test account, login URL, workspace or tenant
details, and sign-in instructions. Use sample data, not a real user's account.
The account ... should work immediately without MFA approval, email or SMS
codes, magic links, or private-network access." Run every case with that
account before you submit.

1.2.1 was rejected because its instructions asked reviewers to join a workspace
through an invite link with their own email. Use a ready account instead:

1. The owner creates a Voiceflow account with an email and a password, on a
   mailbox the team controls, and finishes email verification first.
2. The account joins the review workspace, which holds the sample data below.
   `.submissions/private.md` names the workspace.
3. Sign-in in a private browser window must ask only for the email and password.
4. Disable any invite link that went to OpenAI if it can be reused.

Sample data the test cases need:

| Item | Content |
| --- | --- |
| Agent 1 | `Acme Support Demo` |
| Main instructions | "You help Acme customers with orders and returns. Be brief. Use the knowledge base for policy questions." |
| Knowledge base | Document `Returns policy`: "Customers can return unused items within 30 days of delivery for a full refund. Refunds go to the original payment method within 5 business days." |
| Transcript | A customer asks "Can I get a refund for order 1042?" and the agent says "Sorry, I don't know the refund policy." |
| Variables | No `order_id`. Delete it after each test run. |
| Agent 2 | `Acme Sales Demo`, any simple agent |

If the workspace uses other names, change `review.json` to match and rebuild.

Test instructions to paste. Fill the placeholders in the portal, never in a file:

```text
Please test in the ChatGPT desktop app.

Test account (dedicated to this review, with sample data only)
- Email: <reviewer email>
- Password: <reviewer password>
- Workspace: <review workspace>
- The account has no MFA and needs no email code or invite. Sign in with the email and password fields on the Voiceflow sign-in page.

How to connect
1. Install the Voiceflow plugin and select Connect.
2. A Voiceflow sign-in page opens. Enter the email and password above.
3. On the consent screen, allow workspace read and write access. You return to ChatGPT.

Sample data in the workspace
- Agent "Acme Support Demo": main instructions about Acme orders and returns, a knowledge base document named "Returns policy", and a transcript where a customer asks "Can I get a refund for order 1042?" and the agent fails to answer.
- Agent "Acme Sales Demo": a second agent, so the agent list has two entries.

Running the test cases
- Run the eight test cases from the package in order. Each prompt names the agent it uses.
- The assistant may call vf_get_started first. That is expected.
- Positive case 5 is the only write. ChatGPT asks for confirmation first. If order_id already exists, the assistant says so and creates nothing, which is also a pass.
- Negative case 3 asks to delete all projects. Please do not confirm a deletion; later reviews use the same workspace.

Contact: support@voiceflow.com
```

## Test cases

`scripts/openai/review.json` holds five positive and three negative cases. A
positive case has `description`, `prompt`, `tools_triggered`, and
`expected_behavior`. A negative case has `description`, `prompt`, and
`expected_behavior`. Name only tools the plain URL serves, such as
`vf_project_list`, `vf_agent_read_instructions`, `vf_knowledge_base_query`,
`vf_transcript_search`, `vf_transcript_get`, `vf_variable_list`, and
`vf_variable_create`. Never name the dynamic-mode `vf_call_*` tools.
`tests/test_openai_package.py` checks the cases against the surface snapshot.

## Demo video

The video is a GitHub release asset, so its URL stays fixed:
`https://github.com/voiceflow/agent-plugins/releases/download/openai-review-demo-2026-11-18/voiceflow-openai-review-demo.mp4`.
The 2026-11-18 recording shows the older dynamic tools; record it again with the
reviewer account. To replace it at the same URL:

```bash
avconvert -s "<recording.mov>" -p Preset1920x1080 -o voiceflow-openai-review-demo.mp4 --replace
gh release upload openai-review-demo-2026-11-18 voiceflow-openai-review-demo.mp4 --clobber -R voiceflow/agent-plugins
```

## Recording

Record in the ChatGPT desktop app with the draft package installed, the same
way reviewers test. Before recording, ask "Which Voiceflow tools do you have?"
and check that every tool the cases name is listed. If one is missing, the
package does not fit the budget: fix the toolsets list, not the local
configuration.

The desktop app rewrites `~/.codex/config.toml` and drops per-plugin tool
allow-lists, so an `enabled_tools` workaround does not last there. Reviewers
would not have it either.
