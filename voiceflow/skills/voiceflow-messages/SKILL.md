---
name: voiceflow-messages
description: Create or edit reusable Voiceflow messages, prompts, and text referenced by workflow steps or tool messages.
license: MIT
---

# Messages and reusable prompts

For questions about message variants, reusable prompts, variable substitution, or channel behavior
that this skill does not answer, follow the
[docs MCP workflow](../voiceflow/references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Include package/skill/stage context in `why` as
described there. Reuse guidance for the same issue; consult it whenever unsure.

Read the [operation contract](../voiceflow/references/operations.md). Distinguish
literal message content, a reusable prompt resource, an agent's instructions,
and a workflow step that references one of these.

Read the resource and its consumers before replacing it. Shared text changes can
affect multiple paths. Preserve variants, variable bindings, channel-specific
content, and unrelated fields.

Use current message/prompt operation schemas. Do not guess whether a step
expects raw text, a message ID, or a prompt ID. Create dependencies first and
attach the returned ID. For a local edit, prefer a supported targeted update.

Keep generated-answer instructions separate from exact text the agent should
say. Check variable references and behavior when values are missing. Voice text
should sound natural aloud; chat may include formatting inappropriate for speech.

Read back the referenced resource and owning step/tool after changes. Verify
the intended path uses the edited resource, rather than creating an unused
duplicate and claiming the user-facing text changed.

## Find text and owners

Use `voiceflow_environment.search_text` to check an exact word, phrase, or
pattern across the project, or to find every holder of a message or prompt ID.
Use a targeted read when one can answer. `pattern` is literal text; add
`regex: true` for a regular expression, `wholeWord: true` to skip matches inside
longer words, or `resourceTypes: ["prompt"]` to find a prompt by its words. Each
hit names the resource, field, and line, and a hit on a message or prompt lists
in `usedBy` the steps that hold its ID. Page with `offset` set to `nextOffset`.
`incomplete: true` means the search did not read everything, and `notSearched`
names what it never reads, such as knowledge documents and transcripts. CLI
0.287.0 has no command for this search.

Workflow steps hold message IDs too: Message and End steps, End actions on an
exit, and no-match and no-reply reprompts. Capture entity items and required
entities can hold one as well, and no read shows those; search for the ID.

## Delete a message or prompt

Find every owner first, and read every page of the search. If you cannot
establish every owner, or the search says `incomplete`, do not delete. Tell the
user what you found and what you could not check, and ask whether any entity
uses the message. Delete only after the user confirms that none does.

Clear or repoint each owner before deleting the message. For an End step that
speaks, keep the End and clear its message with `voiceflow_workflow.update_step`
and `"content": {"messageID": null, "responseEnabled": false}`. Deleting the End
leaves the path with no ending, so do that only when the user asks.

Deleting a prompt does not check owners: an owner keeps the ID and sends nothing
at runtime. A message variant can hold a prompt ID in a condition, and every
read, the search included, shows that condition as `null`. So no read proves a
prompt is unused. Say so, and get the user's confirmation before deleting it.

Source: [Instructions](https://www.voiceflow.com/docs/documentation/build/instructions).
