---
name: voiceflow-build
description: Build or extend Voiceflow agents and playbooks, choose the right architecture, and connect routing and tools. Use after the user describes what they want to build.
license: MIT
---

# Build an agent

For questions about architecture, agent capabilities, routing behavior, or a requested feature
that this skill does not answer, follow the
[docs MCP workflow](../voiceflow/references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Include package/skill/stage context in `why` as
described there. Reuse guidance for the same issue; consult it whenever unsure.

Read the [operation contract](../voiceflow/references/operations.md). Resolve the
user's intended project and environment from context; clarify only missing
choices. For a project with a live version, first propose a working environment,
as [environments](../voiceflow-environments/SKILL.md#where-to-make-a-change)
describes. A build request authorizes its necessary draft work, not publishing.

Keep knowledge-only Q&A and lightweight conversational collection on the main
agent. Use a playbook for a distinct multi-step job needing its own tools or
procedures; a workflow for deterministic branching or ordered actions. A series
of questions alone does not require a workflow. Preserve valid details already
supplied, including in the request that triggers routing, and ask only for what
is missing. Avoid creating a playbook solely to wrap the KB.

Separate three instruction layers: global identity/style/guardrails, main-agent
routing, and playbook job instructions. Playbooks inherit the global prompt;
they do not see each other's private instructions.

Before building for a new business, read the actual global `prompt` and main-agent
`instructions`, not just route metadata. CLI `agent get` needs both
`--include-prompt --include-instructions`; MCP `get` needs `includePrompt: true`
and `includeInstructions: true`. See [identity and greeting fields](../voiceflow/references/request-shapes.md#identity-and-greeting).
Replace sample identity and starter instructions in those fields, preserving
unrelated settings. A business name in a playbook does not override the global
identity. For an existing agent, retain its identity unless the task changes it.

Write the job's completion language around what its tools actually do. Collecting
details or setting conversation variables is not submitting a request. A pure
lookup or calculation does not book, reserve, send, or arrange human follow-up.
Without an action that performs that effect, summarize what was collected and
explain the next available step without promising it will happen automatically.

Build in dependency order: agent context, playbook, required resources, tool
attachments, then instructions referencing those attached tools. Every attachment
and routing description must say both WHAT it does and WHEN to use it.

Define who gives the final answer. A playbook that answers should stay active
and wait for the next visitor message, returning to main only when a new message
needs another capability. Do not unconditionally return immediately after an
answer: main can repeat it or route the same request back. If main owns the
answer, the playbook should hand off its result without also answering.

Read the complete existing routing registry before updating it: a supplied
playbooks/workflows list replaces the list. Keep existing entries; do not empty
a registry during a migration when the customer still needs those routes.

A workflow runs when it is registered on the main agent, attached to a playbook
by the user in the editor, reached from another workflow, or set as the
Initialization workflow. Register it on the main agent only for routing: doing
so for a workflow that already runs another way changes routing.

The Initialization workflow runs at launch, before the user's first turn: use it
to load data, greet with fixed text, or copy launch values into variables. Read
which one is set with `voiceflow_agent.get_initialization_workflow`. Build the
workflow, then set it with `voiceflow_agent.set_initialization_workflow`. Only
one is set: a new one replaces it, and `null` clears it. CLI 0.287.0 has no
command for either; the UI step is the Initialization section of the agent's
Behaviour settings. Values the widget or API pass at launch arrive in the
`last_event` variable, not as variables of their own. To use one, add a Code
step to that workflow that copies it from `last_event.payload` into a variable.

The main agent takes a turn at launch, after the Initialization workflow, and
again each time a workflow returns to it. Put the greeting in one place: fixed
text in the Initialization workflow, or a main-agent rule such as "Greet only on
the first turn. After a workflow returns, carry on without greeting." Without
one, the agent greets at launch and again after every workflow.

Use returned IDs. Confirm write results, unresolved references, tool descriptions,
and routing before reporting the draft ready. Do not run tools that contact
external services merely to inspect configuration. Check a new or changed
function on test cases, as [functions](../voiceflow-functions/SKILL.md) describes,
before offering a conversation test.

When runtime testing is authorized, compile the draft and check a fresh greeting
and the job's completion response. Ask whether the requested action actually
happened; verify the answer against the executed tool's effect. See
[evaluations](../voiceflow-evaluations/SKILL.md). Report configuration-only checks
as such when runtime testing is outside scope.

Read [prompting](../voiceflow-prompting/SKILL.md) for instructions and
[wiring](../voiceflow-wiring/SKILL.md) before attaching functions/API tools.
Source: [Playbooks](https://www.voiceflow.com/docs/documentation/build/playbooks).
