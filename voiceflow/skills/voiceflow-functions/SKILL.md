---
name: voiceflow-functions
description: Create or debug Voiceflow function code, sandbox behavior, fetch parsing, outputs, and exit paths. Use when logic cannot be handled by an existing integration or one API request.
license: MIT
---

# Function code

For questions about sandbox APIs, fetch behavior, limits, traces, or function errors
that this skill does not answer, follow the
[docs MCP workflow](../voiceflow/references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Include package/skill/stage context in `why` as
described there. Reuse guidance for the same issue; consult it whenever unsure.

Read the [operation contract](../voiceflow/references/operations.md).
Prefer an existing integration for a supported action, an API tool for one HTTP
request, and a function for transformation, branching, or composed logic.

Functions run in Voiceflow's sandbox, not Node or a browser. Use
`export default async function main(args)` and declared inputs from
`args.inputVars`. Do not assume imports, require, process, Buffer, DOM, or
browser URL utilities exist.

Voiceflow's modified fetch exposes parsed response properties:
`const data = (await fetch(url)).json`, not `response.json()`. Inspect the
documented status and error shape; never log credentials or full customer
payloads. Check current sandbox limits before large responses or custom traces.
For functions that show cards, carousels, or buttons, or end on a user's
choice, read [custom traces](references/custom-traces.md).

Return outputVars with names matching declared outputs and supported scalar
types. Serialize structured data deliberately. Declare every path returned as
`next: { path: 'success' }`; a missing/mismatched path can stop execution.
Return a defined result on every branch.

Creating a function does not attach it to an agent. Declare inputs, outputs,
and paths, then create the attachment with a WHAT + WHEN description. Read
[wiring](../voiceflow-wiring/SKILL.md) for defaults and captured results.

Secrets arrive through declared inputs bound to secret references on the
attachment; never read `args.secrets`. For the binding and its failure modes,
read [secrets](references/sensitive-inputs.md). Tests may call real services, so use
fixtures first and only execute an integration with task authorization.

## Check a function

Check your own function after each write, once the write's result is back, and
before you say it works. Write the cases first: a normal case; each limit at one
below, at, and one above (for "at most 3 items", send 2, 3 and 4); an empty
value; a wrong type; and `"0"`, which is what an unset variable sends. Decide
the expected path and outputs for each case, then run
`voiceflow_function.execute` once per case and compare `output.path` and
`output.outputVars` with them. Fix the code and check again. If cases still fail
after two rounds of fixes, stop and tell the user which ones fail and why: the
code or the expectation may be wrong.

Run these checks only for self-contained code: no `fetch` or other outside
call, and literal input values only, because a `{NAME}` input value binds a
stored secret. Code that calls an outside service runs only when the user asks
for that run; say in one line what the call will do first. Otherwise test it in
a draft conversation. When `success` is false, the result's `error` says why.

Source: [Function tool](https://www.voiceflow.com/docs/documentation/build/tools/function-tool).
