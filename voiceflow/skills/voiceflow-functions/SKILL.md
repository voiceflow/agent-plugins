---
name: voiceflow-functions
description: Create or debug Voiceflow function code, sandbox behavior, fetch parsing, outputs, and exit paths. Use when logic cannot be handled by an existing integration or one API request.
license: MIT
---

# Function code

For questions about sandbox APIs, fetch behavior, limits, traces, or function errors
that this skill does not answer, follow the
[docs MCP workflow](references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Leave `why` out when it is optional; otherwise
send only the package/skill/stage tag described there. Reuse guidance for the
same issue; consult it whenever unsure.

Read the [operation contract](references/operations.md).
Prefer an existing integration for a supported action, an API tool for one HTTP
request, and a function for transformation, branching, or composed logic.

Functions run in Voiceflow's sandbox, not Node or a browser. Use
`export default async function main(args)` and declared inputs from
`args.inputVars`. Do not assume imports, require, process, Buffer, DOM, or
browser URL utilities exist. `TextEncoder`, `TextDecoder`, `URLSearchParams`,
`FormData`, `setTimeout`, and `setInterval` are not defined either. Beyond
standard JavaScript, the sandbox has the modified `fetch`, `delay(ms)`, which
returns a promise (`await delay(500)` waits half a second), and `btoa` and
`atob` for base64, as in a browser.

For base64 in new code, call the built-in `btoa` and `atob` directly; they are
always defined, so never check for them first or hand-write an encoder.
`btoa` takes one byte per character: it throws on a character above U+00FF and
encodes `é` as Latin-1, not UTF-8. So use plain `btoa` only for ASCII, such as
a Basic auth header, and the UTF-8 form for text that may hold accents or
emoji:

```javascript
const authorization = 'Basic ' + btoa(`${user}:${pass}`);
const encoded = btoa(unescape(encodeURIComponent(text.toWellFormed())));
const decoded = decodeURIComponent(escape(atob(encoded)));
```

`toWellFormed()` turns half of a cut emoji into U+FFFD; without it,
`encodeURIComponent` throws. When editing a function with its own base64
helper, keep one that only wraps the built-in or produces non-standard output,
such as base64url. For a hand-written standard encoder, check its padding:
input of 3n+1 bytes must end in `==`, and 3n+2 bytes in `=`. If it is wrong,
replace it with the matching built-in form, and say so alongside the requested
change.

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
the `voiceflow-wiring` skill for defaults and captured results.

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
`vf_function_execute` once per case and compare `output.path` and
`output.outputVars` with them. Fix the code and check again. If cases still fail
after two rounds of fixes, stop and tell the user which ones fail and why: the
code or the expectation may be wrong.

Run these checks only for self-contained code: no `fetch` or other outside
call, and literal input values only, because a `{NAME}` input value binds a
stored secret. Code that calls an outside service runs only when the user asks
for that run; say in one line what the call will do first. Otherwise test it in
a draft conversation. When `success` is false, the result's `error` says why.

Source: [Function tool](https://www.voiceflow.com/docs/documentation/build/tools/function-tool).
