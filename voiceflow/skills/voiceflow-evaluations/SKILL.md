---
name: voiceflow-evaluations
description: Create or run Voiceflow saved tests and evaluations, define quality criteria, and interpret test results without overstating coverage.
license: MIT
---

# Tests and evaluations

For questions about test assertions, evaluation criteria, run behavior, or interpreting results
that this skill does not answer, follow the
[docs MCP workflow](../voiceflow/references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Include package/skill/stage context in `why` as
described there. Reuse guidance for the same issue; consult it whenever unsure.

Read the [operation contract](../voiceflow/references/operations.md). Distinguish
a saved conversational test, its individual run, and an evaluation criterion.
Inspect current schemas for test turns, response/routing/tool checks, and
evaluation definitions.

Choose a small representative set: happy path, missing information, recovery,
and a known regression. Define observable success before running. Check the
intended project/environment and credentials used by the run.

For a new or revised agent, include its fresh greeting and a completed task, not
only individual function outputs. Check the business identity and whether the
closing response claims an effect the trace does not support. Follow up with
questions such as whether anything was submitted or someone will contact the
customer. For an extension, also exercise an existing route and compare its
configuration with the pre-edit state.

For collection flows, test a request that already supplies some information and
a question or correction during collection. Check the retained values and final
summary, not merely whether the happy-path topology is reachable.

Inspect same-turn handoffs and tool counts as well as response values. A correct
answer repeated by a routing loop is still a defect; repeated tool execution can
have additional effects even when a pure fixture makes the result look harmless.

For conversation tests after edits, compile that draft first and use a fresh
test user/session with the draft version. Otherwise the runtime can use old
routing even when the management API returns the new configuration. See the
[compile sequence](../voiceflow/references/request-shapes.md#compile-before-a-draft-conversation-test).

To check a short exchange without saving a test, use
`voiceflow_conversation.run_script` with up to 10 user messages in order. It
starts a fresh conversation and returns each turn's replies, tool calls,
changed variables, and errors; pass `variables` to start as a known caller. It
does not compile: compile first after an edit, and when the result says
`needsRecompile: true`, compile and run it again. Use `voiceflow_conversation.send`
only when the next message depends on the reply. CLI 0.287.0 has no command for
the script run. A reply is not proof a tool worked; read the turn's tool calls.

Before you save a test:

- Fit the scenario in its turn limit: count the turns the happy path needs,
  then add two.
- Do not script a goodbye before the turn you check, or the agent ends the
  conversation and the check never runs.
- Check outcomes, such as the booking tool called with the right date, not the
  route the agent took.
- Test a limit with real attempts, such as three wrong answers, not a message
  saying "I failed three times".
- Seed a variable by its ID from `voiceflow_variable.list`; a name in its place
  sets nothing. Check once in the run's log that the value reached the agent.
- When a test you wrote fails, check the test before the agent, and say so when
  the mistake was yours.

Tests can invoke real tools and external services. Prefer fixtures or a safe
environment when available, but do not claim an environment clone isolates
external systems or shared KB documents. Explain any material side effect
outside the user's requested testing scope before running it.

Poll run status with a bounded deadline; pending is not passed. Separate
infrastructure errors from agent failures. Inspect traces to identify why an
assertion failed instead of weakening the assertion until it passes.

Read a run with `voiceflow_test.get_run` about every 15 seconds, at most 20
times. A run goes from idle through pending and running to passed,
failed, or canceled. If it is still running at the deadline, say so and offer
to stop it with `voiceflow_test.cancel_runs`: a run that has not started never
starts, and a finished run keeps its result. CLI 0.287.0 has no cancel command.

When the agent under test can reach a tool that writes to an outside system,
list each finished run's tool calls with `voiceflow_test.query_run_logs` and
`debugKinds: ["tool"]`, and report every write-shaped call before pass or fail.
A page holds at most 50 entries or about 30,000 tokens; while `hasMore` is true,
call again with `offset` set to `nextOffset`. Then report passed checks of total
checks, the fail reason, and the failed checks with their reasons, and mention
the model credit cost of a large suite. For a failure's trace, query the failing
entries with `levels` or `turns`. A test run does not log its launch: the
greeting is turn 0 and the first user message is turn 1.

Report the cases executed, their outcomes, and remaining gaps. A test passing
does not authorize publishing or merging. Evaluation resources can be shared
across environments; inspect scope before changing a shared criterion.

Sources: [Tests](https://www.voiceflow.com/docs/documentation/measure/tests),
[Evaluations](https://www.voiceflow.com/docs/documentation/measure/evaluations).
