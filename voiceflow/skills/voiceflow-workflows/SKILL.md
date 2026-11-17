---
name: voiceflow-workflows
description: Read or edit Voiceflow workflow canvas blocks, steps, ports, branches, and connections. Use for deterministic flows or broken workflow routing.
license: MIT
---

# Workflows

For questions about step behavior, ports, transitions, branching, or workflow errors
that this skill does not answer, follow the
[docs MCP workflow](../voiceflow/references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Leave `why` out when it is optional; otherwise
send only the package/skill/stage tag described there. Reuse guidance for the
same issue; consult it whenever unsure.

Read the [operation contract](../voiceflow/references/operations.md), then the
workflow and relevant step schemas. A block is a canvas container; steps inside
it execute in order. A workflow ID, block ID, step ID, and port ID are distinct.
For the message/end discriminators and entry connection, read the
[verified example](../voiceflow/references/request-shapes.md#a-message-followed-by-end).

Plan the path before mutation: start, decisions, actions, success, error, and
termination. Create resources first and connect returned IDs; do not fabricate
ports from labels or assume a step's ID is its block's ID.

A listen step captures the next turn; it does not establish that the turn answers
the requested field. For conversational intake, preserve details supplied before
entering the flow, distinguish questions/corrections from answers, and validate
captured values before advancing. Prefer main-agent or playbook collection when
flexible dialogue is needed; unconditional message/listen pairs can shift answers
into the wrong fields after a repeated question or interruption.

When a mutation accepts expectedSteps, pass the current ordered step IDs.
On a conflict, re-read and reconcile once rather than retrying stale state.
Inserting, splitting, moving, and deleting steps can change ownership or ports;
read back the affected blocks and links after the edit.

Link the actual branch/exit port to the target block using the live schema.
Playbook steps must use the playbook's declared exit paths. Check every expected
branch, including default/no-match, rather than only the happy path.

Messages and prompts are separate resources in relevant step schemas. Create
or reuse them through their supported operations; don't insert a guessed text
field into a step payload.

## Reading

`vf_workflow_get` and `vf_workflow_get_step` answer most
questions. `vf_workflow_get_raw` returns the stored canvas nodes with
their coordinates; it is long and unprocessed. Use it only when the other reads
cannot answer, such as where blocks sit, send `blockIDs` for the blocks you
need, and never plan an edit from it. To find where a word, phrase, or ID is
used across the project, see [messages](../voiceflow-messages/SKILL.md#find-text-and-owners).

## Editing

- To say something and end, use a Message step with its own message, then an
  End step. Never give a new End step a message.
- When the user wants a Message step's words gone, delete the step; do not
  keep it silent. A speaking End step is the exception, because deleting it
  leaves the path with no ending: keep it and send
  `"content": {"messageID": null, "responseEnabled": false}` with
  `vf_workflow_update_step`. An update keeps every field you leave out.
- `vf_workflow_add_blocks` adds up to 20 blocks with their steps, links
  between them, and `from` ports that link existing ports to them. Create their
  messages first, in one batch. `vf_workflow_link_many` sets up to 50
  links in one write.
- To change an exit action's kind, use `vf_workflow_replace_action`. It
  keeps the action's place in one write. Deleting and re-adding leaves the path
  running without the action in between.
- Arrange blocks with `vf_workflow_arrange_blocks` only when the user asks
  to tidy the canvas. Pass `blockIDs` when they mean some blocks; without them
  every block moves, including ones the user placed by hand.
- `vf_workflow_duplicate` copies a workflow with its own messages, prompts,
  and playbooks, and maps each original ID to the copy's. Edit the copy through
  those IDs. When the main agent should route to the copy, send every workflow
  already in the agent's `workflows` list plus the copy; the copy alone
  replaces the list.
- A new workflow needs a way in. Add it to the agent's `workflows` list, with a
  routing rule, only when the main agent should route to it. Skip both when it
  runs another way: as the Initialization workflow, from a Workflow or Go to
  block step in another workflow, or as a workflow tool.

CLI 0.287.0 has no commands for the raw read, adding several blocks, several
links, replacing an action, arranging, or duplicating; use the single-item
commands there.

## Workflow tools

When the user asks for a workflow tool rather than a routing entry, attach it
with `vf_tool_create`, type `workflow`, `target: {"global": true}`, the
`workflowID`, and a `description` that says when to run it. The main agent and
every playbook can then call it, so add no routing rule. Never send a
`playbookID`: playbooks do not take a workflow tool of their own. Without a
description the tool falls back to the workflow's own, which rarely says when.
Do not name the workflow in instructions either: a workflow name there resolves
only for workflows in the agent's `workflows` list. To undo it, delete the tool
with the ID the create returned.

Verification starts with read-back topology and reference checks. A runtime
test can invoke real integrations; scope it with [evaluations](../voiceflow-evaluations/SKILL.md)
only when the user requested testing.

Source: [Workflows](https://www.voiceflow.com/docs/documentation/build/workflows).
