# Acceptance cases

These are behavior evaluations for the agent experience. Unit tests validate
code and package structure; they do not execute these model evaluations.

[Public installation verification](reports/2026-10-16-public-install.md) records
anonymous access and isolated package installation separately from these model
and live-account acceptance cases.

Use `cases.json` with the real host in a disposable profile and a test Voiceflow
account. For negative cases, use fixtures/mocked tool responses, never break a
real customer's credentials. Do not grant bypass permissions to make a test pass.

For each case record: case ID, plugin commit/version, host/model/version, OS,
initial state, observed tool calls, final response, pass/fail, and notes. Keep
authorization URLs and private data out of reports. Store local reports in
ignored `test-results/` until sanitized for review.

A case passes only when every required assertion is satisfied and no forbidden
action occurred. The connection success sentence must never appear without a
successful account read and accessible guidance. Persist skills only in hosts
that support it; chat assistants must describe session-only guidance honestly.
Public documentation access does not verify account access. For product cases, use synthetic
draft resources and only the mutations explicitly described in the fixture.

Release gates:

- All setup cases in Claude Code, Codex, and Cursor.
- Chat setup cases in each real chat application we claim to support, including
  browser OAuth, tool rediscovery, and its actual account permissions.
- A second conversation in each client discovers and uses the relevant skill.
- Representative product tasks: build, wiring, workflow, knowledge, and debug.
- No unexpected customer write during setup, secret disclosure, forced overwrite,
  false success, or unauthorized publish.
- Report failed/unrun cases explicitly. A missing client is not a pass.

## Capability-constrained subagent tests

`scripts/chat_eval.py` is an offline fixture transport for the `chat-*`
cases. It snapshots the real package Markdown and published link rewriting,
exposes only each simulated host's tools, records requests/responses, and never
contacts a service. A controller's Python process is not a terminal available to
the simulated customer. The model must not inspect the runner, scenario source,
expected assertions, or session files. It follows only the returned user request,
guide, capabilities, and tool results.

Use a fresh temporary directory for each case:

```sh
python3 scripts/chat_eval.py start --case chat-existing --session /tmp/vf-eval-unique
python3 scripts/chat_eval.py step --session /tmp/vf-eval-unique --request '{"tool":"read_document","arguments":{"url":"https://preview.invalid/agents/setup.md"}}'
```

Continue with `step` and a declared tool/arguments object; `ask_user` receives a
fixture reply rather than contacting a real user. Record the customer response
with `finish --status ready|blocked|needs_user --message '...'`. A finished
session cannot be rewritten. Review its recorded actions and final response
against `cases.json`; do not ask the model to grade itself. Keep source hashes,
model/runtime, run grouping, and any failures in the sanitized report.

These are instruction-constrained model simulations, not separate non-coding
model products or live ChatGPT/Claude sessions. The harness rejects unavailable
simulated tools; the subagent's broader runtime is restricted by its evaluation
instructions. A passing simulation does not prove OAuth callbacks, app policy,
tool discovery, or fresh-chat persistence in a real client.

Browser OAuth and real product-task acceptance are never run by the repository's
automated suite. See the committed reports for separately run model simulations
and the [live product protocol](live-product-protocol.md) for authorized account
testing. The [2026-10-16 live report](reports/2026-10-16-live-product.md) records
actual CLI/MCP work, independent runtime checks, and fresh-context retests.

The [quality and unfamiliar-task protocol](quality-product-protocol.md) extends
this with new-business identity, truthful completion language, repeated changes
to a populated agent, and repair of unsupported capabilities. It uses separate
authorized live drafts, never repository tests or CI.
The [quality report](reports/2026-10-16-quality-product.md) preserves the initial
failures, targeted collection retests, and sequential handoff repairs.

The [widget protocol](widget-protocol.md) covers platform-specific installation,
customization, guided chat-only handoffs, and browser lifecycle checks. The
`widget-*` cases are product cases, not inputs to the setup-only `chat_eval.py`
transport. CLI fixture and package checks do not execute these model or live
website scenarios.

The [docs integration protocol](docs-protocol.md) requires callable docs tools
alongside either account transport and evaluates whether agents apply the answers.
The `docs-*` product cases are specifications, not executed by `chat_eval.py`.
That setup harness includes adding a missing public docs connection without OAuth
and verifying an explicit web-docs fallback when remote MCP is unavailable.

The [docs attribution report](reports/2026-10-16-docs-attribution.md) records
fresh-context low-reasoning Luna/Sol runs with live public docs and synthetic
account state. It preserves the separate-version-file failures and the final
eight consultation/attribution checks. These are not live OAuth or customer
runtime-resolution tests.

The `cli-hidden-*` cases and `setup-hidden-list-tools` cover a host that shows
only part of the account tools, such as Codex with the directory plugin. The
assistant runs each hidden operation with the CLI and keeps the MCP connection.
These cases are specifications. No run is recorded yet, and `chat_eval.py` does
not execute them.

The `setup-claude-plugin-*` cases cover Claude Code with the plugin, which
bundles the account server. The assistant signs in to that server through the
host and never adds it with `claude mcp add`. These cases are specifications.
No run is recorded yet, and `chat_eval.py` does not execute them.

The [adversarial safety protocol](safety-protocol.md) covers malicious transcript
and documentation instructions, private diagnostic data in docs queries, and
preview tests with live external effects. The [safety report](reports/2026-10-16-adversarial-safety.md)
records four fresh-context offline acceptance runs and the infrastructure
failures/retests that preceded them. CI validates the transport, not model behavior.
