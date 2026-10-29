---
name: voiceflow-debug
description: Diagnose broken Voiceflow behavior from configuration, traces, and transcripts. Use for wrong routing, failed tools, empty values, or unexpected answers.
license: MIT
---

# Diagnose before editing

For questions about an error, unexpected runtime behavior, or a proposed fix
that this skill does not answer, follow the
[docs MCP workflow](../voiceflow/references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Include package/skill/stage context in `why` as
described there. Reuse guidance for the same issue; consult it whenever unsure.

For widget loading, styling, duplicate launchers, or website navigation problems,
use [Widget](../voiceflow-widget/SKILL.md) before changing the agent's behavior.

Read the [operation contract](../voiceflow/references/operations.md). Establish
the expected behavior, actual behavior, project, environment, and one relevant
conversation or failing step. Do not assume the currently published version is
the same as the draft.

Inspect the smallest useful evidence: current resource settings, routing,
attachment bindings, and relevant trace sections. Classify the failure as
instructions, retrieval, routing, state/wiring, integration, or runtime/version.
The [failure patterns](references/failure-patterns.md) list common causes and
their fixes. For many conversations at once, follow
[bulk analysis](references/bulk-analysis.md).

Read only the part of a log you need. `voiceflow_transcript.query_logs` reads a
live conversation or a debug session by transcript ID, and
`voiceflow_test.query_run_logs` reads a test run by run ID. Filter by `levels`
(`["fatal", "error", "warn"]` for what went wrong), `turns`, `kinds`,
`debugKinds` (`tool`, `variables`, `llm`, `kb`), or `search`. `search` is plain
text, ignores case, and takes `|` between alternatives; it does not match the
whole prompts and knowledge chunks an entry carries. Each result also counts
entries per kind and level and reports token use per model, so a first query
with `limit: 1` shows what the log holds. CLI 0.287.0 has no command for log
queries; use `vf transcript get` there.

A `voiceflow_conversation.send` result leaves out the knowledge chunks a search
returned and a playbook's whole instructions. To see the chunks, query the log
with `debugKinds: ["kb"]` and `detail: "full"`. In a transcript every input
starts a turn, the launch included, so the user's first message is turn 2. A
test run does not log its launch: its greeting is turn 0 and the user's first
message is turn 1. Find the turn the user means with `kinds: ["user"]` or a
`search` for their words, then read it with `turns`.

For a tool failure, distinguish model selection from missing inputs, external
HTTP failure, output shape, capture mapping, and dependent-call ordering.
Use [wiring](../voiceflow-wiring/SKILL.md); prompt edits cannot repair missing
output captures or IDs.

For an unexpected answer, check the actual retrieved source and active prompt
layer before rewriting persona text. For workflow failures, read ports and
branch topology rather than infer connections from names.

For repeated replies, count final answers, tool executions, and handoffs within
one visitor turn. A single tool execution can still produce duplicate answers
from the playbook and main agent. Read both main routing and the playbook's full
completion/exit instructions. If a conversational playbook has already answered
but unconditionally returns to main, remove that conflicting exit: wait for a
new visitor message and return when that new request needs another capability.
Adding "do not repeat" only to main leaves the premature handoff intact. Give
the final answer one owner; if main must answer, the playbook should hand off
without also answering. Preserve deliberate workflow exits. See
[prompting](../voiceflow-prompting/SKILL.md) for related instruction guidance.
Test calculation/task → another capability → recall/new task in one conversation,
not only fresh sessions, to verify that the fix has not trapped routing.

Report observed evidence separately from hypotheses. Make the smallest
authorized correction and verify its stored result. A read-back proves saved
configuration, not runtime success. Ask for or run a scoped test only when it
is within the user's request; real integrations may fire.

Sources: [Transcripts](https://www.voiceflow.com/docs/documentation/measure/transcripts),
[Tests](https://www.voiceflow.com/docs/documentation/measure/tests).
