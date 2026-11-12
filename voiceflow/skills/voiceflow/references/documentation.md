---
package: voiceflow
version: 1.0.0
---

# Answer product questions with the docs MCP

Skills supply the workflow; Voiceflow's website documentation supplies current
product knowledge. For **every new Voiceflow troubleshooting issue** (an error,
unexpected behavior, or blocked setup), consult the docs MCP before recommending
or applying a fix, even when a skill already suggests one. Inspect the relevant
local evidence first when needed to ask a useful question. For other how-to,
capability, setting, or API/CLI questions, consult it when the skill does not
answer them, before answering or choosing an implementation.
Do this for your own implementation questions as well as the user's questions.
Also consult it when a skill appears stale, evidence conflicts, or you are unsure.
A source link at the end of a skill is a starting point, not a substitute for
retrieving the answer. Reuse relevant retrieved guidance within the same task;
there is no need to repeat a lookup for every command or fetch an entire manual.

## Choose the documentation tool

Discover the host's actual tool names and input schemas, including deferred
tools. The server is the public **Voiceflow Knowledge MCP** at
`https://www.voiceflow.com/docs/mcp?logging=off`, with Streamable HTTP and no
authentication. The `logging=off` parameter turns off docs request logging for
connections this package creates. Host prefixes vary. Prefer this server over
general web search or remembered product behavior whenever it is available.

| Question | First tool |
| --- | --- |
| How do I do this? What does this setting mean? How does this API/CLI behavior work? Why this error? | `ask_voiceflow` |
| Find candidate pages, compare approaches, or refine a weak answer | `search_voiceflow` |
| Need the exact example, configuration fields, table, or a cited section | `read_voiceflow_page` |
| What's new, deprecated, removed, or replaced? | `get_voiceflow_changelog` |

Fill required arguments from the live schema. Current tools require `initiator`
(`human` for the user's question, `agent` for your own implementation question),
`purpose` (`answers` for a specific question, `research` for broader exploration),
and `why`. While the schema requires `why`, fill it with the package tag below
and nothing else. Ask a focused question in English, then answer the user in
their language. Include relevant product terms and channel/version context; omit
credentials, personal details, customer transcripts, and private source. These
public tools do not need account IDs or tokens.

## Send only the package tag in `why`

On each docs call made while using these skills, set `why` to exactly this tag:
`vf-agent-plugin/<version> skill=<active-skill> stage=<stage>`.
Add no task, symptom, setup state, or other sentence, even though the tool
schema describes `why` as the task. The question already says what you need.
Use `version` from this document's package metadata at the top, which is part of
the installed skill files. It travels with standalone skills and native plugins;
reading this workflow also reads the version. Use the skill
actually guiding the work, not every skill read. The stages are:

- `setup`: establishing or verifying the assistant's Voiceflow connection.
- `troubleshooting`: diagnosing an error or unexpected product behavior after setup.
- `usage`: other product questions and implementation guidance.

For example, after reading the installed version, replace `<version>` here:
`vf-agent-plugin/<version> skill=voiceflow-setup stage=setup`.
For an error question use `intent: error` where the live tool schema supports it;
`purpose` remains `answers`. Preserve the actual human/agent initiator.
Do not add unsupported arguments or put the tag in the search question.

If this document's package metadata is missing or invalid, use `unknown` for the
version; never substitute a CLI version, remembered release, or latest remote
manifest. Use the supplied metadata when it is present.
If the skill is genuinely unknown, use `skill=unknown`. Missing metadata must
not block help. This is self-reported context in the existing docs request, not
a new tracking request. Put no user/account IDs, site URLs, transcript text,
credentials, or private code in any docs argument. Do not send extra queries
merely to record progress or success, or upload a conversation afterward. Test
controllers should label their MCP client as an evaluation client so test
traffic can be separated.

## Apply the answer and verify the result

If the answer is weak, reports `answerable: false`, or points to a better
term/page, refine the question or read that section. A successful tool response
does not necessarily answer the question. Inspect the evidence and apply it;
a token search followed by an unsupported answer does not resolve the question.
Cite the returned documentation URL when explaining product behavior. For an
implementation, use the documented approach and verify the result separately.
For troubleshooting, say whether the fix is proposed, saved, or verified by an
actual runtime/browser check. A docs response never establishes task completion.

## Keep the three sources distinct

- **Skills:** task workflow, preserved state, verification, and scope.
- **Docs MCP:** current product behavior and how-to guidance, including the
  widget, API, CLI, and account MCP. Resources such as `voiceflow://skill` can
  supplement guidance if advertised; resource access is not required.
- **Account MCP / CLI:** the user's actual state and exact operation schemas.
  Inspect live schemas or installed CLI help for arguments before executing.

The account's knowledge-base query tools search the customer's agent content;
they are not the Voiceflow docs MCP. Do not use customer KB queries to learn
Voiceflow. A docs answer cannot verify account access, saved changes, or runtime
behavior. If docs conflict with a skill or tool schema, investigate the specific
discrepancy; do not guess fields or use failed writes to discover a contract.

## If docs MCP is unavailable

Check discovery first. Reuse or connect it through the host-supported
[docs connection path](../../voiceflow-setup/references/mcp.md#documentation-connection)
when available; never require OAuth for this public server. If the host cannot
expose it, or the service fails, use the public Voiceflow website docs or
`vf docs search "<question>" -o json` / `vf docs get <page>` through an available
CLI. Inspect that CLI's help; do not install it solely to answer a docs question.
For temporary failure, allow one bounded retry, respecting retry hints, then
use the fallback. Avoid repeated reconnection or searching unchanged terms.

State the fallback briefly when relevant. If no authoritative source answers the
question, say what is unresolved, complete independent work, and ask only for
missing customer context; do not turn an assumption into a product guarantee.
For another platform's own editor, plans, or deploy behavior, use that platform's
official docs in addition to Voiceflow guidance.

Source: [Knowledge MCP](https://www.voiceflow.com/docs/mcp/knowledge).
