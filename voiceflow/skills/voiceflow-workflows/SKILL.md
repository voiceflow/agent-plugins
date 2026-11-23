---
name: voiceflow-workflows
description: Read or edit Voiceflow workflow canvas blocks, steps, ports, branches, and connections. Use for deterministic flows or broken workflow routing.
license: MIT
---

# Workflows

For questions about step behavior, ports, transitions, branching, or workflow errors
that this skill does not answer, follow the
[docs MCP workflow](references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Leave `why` out when it is optional; otherwise
send only the package/skill/stage tag described there. Reuse guidance for the
same issue; consult it whenever unsure.

Read the [operation contract](references/operations.md), then the
workflow and relevant step schemas. A block is a canvas container; steps inside
it execute in order. A workflow ID, block ID, step ID, and port ID are distinct.
For the message/end discriminators and entry connection, read the
[verified example](references/request-shapes.md#a-message-followed-by-end).

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
used across the project, see the "Find text and owners" section of the
`voiceflow-messages` skill.

## Editing

- An End step, or an End exit action, ends the whole conversation, also inside
  a workflow the agent runs, the Initialization workflow, or a workflow another
  workflow calls. Nothing after it runs, the agent does not answer, and a later
  message starts the conversation over. Use End only where the user wants the
  conversation to stop.
- To hand back to the agent, leave the last port unlinked. When a path reaches
  an unlinked port on the last step of a block, or an unlinked `else`, the
  workflow finishes there and the conversation returns to what started it: the
  agent, or the Workflow step that called it, which goes on to its next step.
  This is how greeting buttons in an Initialization workflow hand over to the
  agent. A read shows such a port or button with `to: null`; that is not an
  error. A Handoff's fail or return port can likewise stay unlinked when the
  agent should take over then.
- A step that links back to its own block repeats forever. Point it at a block
  that does what the user wants next: hand back, hand off, or end. Unlinking
  the looping port also stops the loop, but on a step that is not last, an
  unlinked button port continues to the next step: check that step, because an
  End there ends the conversation. A retry loop also needs a counter, raised in
  a Code step, and a Condition that leaves it.
- To say something and end, use a Message step with its own message, then an
  End step. Never give a new End step a message.
- When the user wants a Message step's words gone, delete the step; do not
  keep it silent. A speaking End step is the exception, because deleting it
  stops ending the conversation there: keep it and send
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
  those IDs. When the main agent should route to the copy, add the copy with
  `vf_agent_add_workflow`.
- A new workflow needs a way in. Add it to the main agent's `workflows` list
  with `vf_agent_add_workflow` when the main agent or a playbook should call
  it. Skip that when it runs another way: as the Initialization workflow or
  from a Workflow or Go to block step in another workflow.

## Workflow tools

A workflow is never a tool. To make a workflow available, add it to the main
agent's `workflows` list with `vf_agent_add_workflow`. Give the entry a
`workflowID` and a `description` that says when to run it. The main agent and
every playbook can then call the workflow, and the description tells them
when. Add a routing rule with `vf_agent_patch_instructions` only when the main
agent itself should hand off to the workflow at a set point.

Change one entry with `vf_agent_update_workflow`, and send only the fields
that change. Take a workflow off the list with `vf_agent_remove_workflow`. The
workflow itself stays. Each of these three tools changes one entry and keeps
every other. Adding a workflow that is already listed fails. Changing or
removing one that is not listed fails too. Deleting a workflow with
`vf_workflow_delete` leaves its entry in the list, so remove the entry as well.

`vf_agent_update` with `workflows` replaces the whole list. Use it only when
the user wants to replace the list. Read the list first and send every entry
you keep, because an entry you leave out is removed.

Never create a tool of type `workflow` with `vf_tool_create`. The server
refuses it and writes nothing. If the user asks for a "workflow tool", explain
that workflows are added to the main agent's `workflows` list, not as tools,
and do that instead. An older project can still show a workflow tool on the
main agent. Opening the project in Voiceflow moves it into the `workflows`
list. Do not create another workflow tool, and do not copy that one.

An older project can also carry a workflow tool on a playbook. It runs until
someone opens the project in Voiceflow, which deletes it without moving it. If
the playbook still needs that workflow, add it to the main agent's `workflows`
list with `vf_agent_add_workflow` first: every playbook can call a listed
workflow. Until the project is opened, `vf_tool_list` shows the old tool and
`vf_tool_delete` removes it. Nothing can create or update one.

Verification starts with read-back topology and reference checks. When you
report a workflow with buttons, say for each button whether its path ends the
conversation, hands off, or hands back to the agent. A runtime
test can invoke real integrations; scope it with the `voiceflow-evaluations`
skill only when the user requested testing.

Source: [Workflows](https://www.voiceflow.com/docs/documentation/build/workflows).
