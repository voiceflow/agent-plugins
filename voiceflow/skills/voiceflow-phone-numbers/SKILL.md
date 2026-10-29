---
name: voiceflow-phone-numbers
description: Give a Voiceflow voice or chat agent a phone number for calls or texts, and move, disconnect, rename, or delete numbers. Use when the user wants an agent reachable by phone.
license: MIT
---

# Phone numbers

For questions about phone providers, calls, texts, or number setup that this
skill does not answer, follow the
[docs MCP workflow](../voiceflow/references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Include package/skill/stage context in `why` as
described there. Reuse guidance for the same issue; consult it whenever unsure.

Read the [operation contract](../voiceflow/references/operations.md).

A phone number belongs to the workspace, not to one agent. It has two sides:
the `voice` side takes calls and the `sms` side takes texts. Each side reaches
one project or nothing, and assigning a side is what connects it.

## Which side the agent uses

The project read does not say whether an agent is for voice or chat, so ask
whether it takes phone calls or texts.

- A voice agent takes calls on the `voice` side.
- A chat agent takes texts on the `sms` side. Texts need a Twilio number. A
  Voiceflow number, provider `voiceflow-telnyx`, never takes texts, and a chat
  agent never takes calls.

The server refuses a side that does not fit the number or the project.

## Add a number

In the Voiceflow UI, open the agent and select Phone numbers in the sidebar,
under Deploy. For a chat agent the item is called SMS.

First look for a number the workspace already holds:
`voiceflow_phone_number.list` with the `workspaceID`. If a free one fits, assign
it. The MCP refuses to create a number, because that spends money or takes
carrier credentials. So hand the step to the user, as the
[phone number handoff](../voiceflow/references/cli-handoffs.md#add-a-phone-number)
describes: connect a number they hold with `vf phone-number create`, or add it
in the UI. Never ask for carrier credentials in the conversation.

Buying a new number charges the workspace. Offer it only when the user asks to
buy one and accepts the cost, and hand over the command with `--dry-run` first.
Ask the user to say when the number exists. Then find it with
`voiceflow_phone_number.list` and connect it with
`voiceflow_phone_number.assign`. A handed-over command is not a connected
number; confirm it with a read.

## Change a number

Each operation takes `phoneNumberID`, the number's ID rather than the digits,
and `workspaceID`. Find the ID with `voiceflow_phone_number.list`; each entry
shows the project its `voice` and `sms` sides reach.

- Connect or move a side with `voiceflow_phone_number.assign`, giving `target`
  and `projectID`. Leave out `environmentAlias` unless the user names an
  environment. With no environment, calls and texts reach the published version
  and follow the traffic split. To try a change on a real call before
  publishing, send `environmentAlias` with `version: "draft"`, and switch back
  afterwards.
- Disconnect with `voiceflow_phone_number.unassign` and `target`. Leave out
  `target` to clear both sides. Clearing a side that is not connected is
  refused.
- Rename with `voiceflow_phone_number.update` and `name`. The name is a label in
  the workspace; callers never see it.
- Delete with `voiceflow_phone_number.delete` only when the user says to delete
  the number. It stops answering at once.

Moving or disconnecting a side that answers for an agent, and deleting a number
that does, changes who gets real calls or texts. Say which agent gains or loses
them and get the user's go-ahead first. After a move, say that the old agent no
longer gets those calls or texts. When a number reaches the published version,
say that unpublished changes are not live on it yet.

Use [voice](../voiceflow-voice/SKILL.md) for how the agent speaks on a call, and
[environments](../voiceflow-environments/SKILL.md) for publishing.

Sources: [Connect a phone number](https://www.voiceflow.com/docs/documentation/deploy/phone/connect-a-phone-number),
[Inbound SMS](https://www.voiceflow.com/docs/documentation/deploy/sms/inbound).
