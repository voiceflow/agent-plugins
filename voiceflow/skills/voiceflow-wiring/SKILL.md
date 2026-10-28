---
name: voiceflow-wiring
description: Connect Voiceflow function/API tool inputs, secrets, captured outputs, and project variables; diagnose empty values or incorrect tool bindings.
license: MIT
---

# Wire tools and state

For questions about input collection, defaults, captures, references, or state behavior
that this skill does not answer, follow the
[docs MCP workflow](../voiceflow/references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Include package/skill/stage context in `why` as
described there. Reuse guidance for the same issue; consult it whenever unsure.

Read the [operation contract](../voiceflow/references/operations.md). Inspect the
resource declarations and the specific attachment using them. Tool definitions,
attachments, and project variables are different resources.
Read [attachment request shapes](../voiceflow/references/request-shapes.md#attach-a-function-and-capture-its-results)
when creating a binding or diagnosing an invalid target/capture payload.

For function inputs, key inputVariables by the declared input UUID, with the same
functionInputVariableID inside. For API tool inputs use apiToolInputVariableID.
Do not key by a friendly name merely because an existing attachment does.

A defaultValue can bind a project variable or secret by name. Check
unresolvedReferences after writes. Secret values belong in the secure Voiceflow
UI/connection flow, never chat or source code. Leave collection disabled for
secret-bound inputs according to the live schema.

Agent collection and defaults are distinct. Disable collection only when a
reliable default/setter exists on every incoming path; otherwise an empty value
may silently reach the integration. A default alone does not prove a value is
available.

Capture outputs explicitly into the intended project variable IDs. Output text
visible to the model is not persistent state. Each attachment has independent
bindings; changing one does not configure every playbook using the same tool.

Order dependent tool calls. Do not assume two calls in one parallel batch see
each other's captured writes. Re-read after UI edits if captures appear lost.

An attachment update changes only the fields you send. `inputVariables`,
`captureResponse` and `captureInputVariables` merge by key: send only the
entries you change, and `null` for an entry to remove it. Any other field you
send replaces the stored one. To drop a phantom input keyed by a name, send
that key as `null`; leaving it out keeps it. A `required: false` input also
needs a `defaultValue`, or the run fails with a missing input value.

## Progress and counters

A playbook cannot set a variable. Only a tool's captured response, a
`captureInputVariables` entry, or a workflow Set step writes one, so an
instruction such as "add the answer to {evidence}" does nothing. To track
progress, use one function per event:

- The model sends only the new event as one `required: true` input, never the
  running totals.
- Each stored value comes in as its own `required: false` input with a default
  such as `{attempts}`, so the model never sees or retypes it.
- The code returns the new value, such as a count plus one or a JSON list with
  the new item, as a string or number, and `captureResponse` writes it back to
  the same variable.
- A gate, such as a routing rule or exit condition, reads the stored value,
  for example `attempts` at 3 or more, never a flag the model sets.

Treat `""`, `"0"`, and invalid JSON as empty, because an unset variable arrives
as `0`. Call the function once per turn: two calls in one batch both read the
value from the start of the turn, so one update is lost. A tool that takes the
whole stored list from the model loses everything on one blank argument.

## Check the wiring

Prefer the smallest relevant inspection over sweeping the whole project. Verify
UUIDs, WHAT + WHEN descriptions, references, captures, and route coverage before
running anything. For a full check, list each agent's and playbook's tools,
read their attachments, and list the project variables. Compare input defaults
and captures with the declared variables, and check `unresolvedReferences` in
write results. Proven designs are in [patterns](references/patterns.md); common
mistakes and their fixes are in [anti-patterns](references/anti-patterns.md).

Source: [References](https://www.voiceflow.com/docs/documentation/build/editor/references).
