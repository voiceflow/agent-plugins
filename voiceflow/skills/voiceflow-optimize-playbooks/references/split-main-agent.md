# Split the main agent's instructions

Read this after the user agrees to move a job out of the main agent's
instructions into a playbook of its own.

Every tool on the main agent is global: every playbook can call it, workflow
tools included. So the new playbook can call the main agent's tools, and the
split moves text only. Move one job's section at a time. The main job stays,
with the greeting, the routing rules and the rules every job shares.

1. Create the playbook with `vf_playbook_create`: its name, a `description` that
   says what it does and when, and no `instructions`. Leave `settings` out, so
   it runs on the same default model. Turn on the system tools the section
   needs, set as `vf_agent_get` shows them on the main agent. For each message
   they hold, read it with `vf_message_get`, create a copy with
   `vf_message_create`, and send the copy's ID. A message has one owner.
2. Write its text. Read the new playbook with `vf_playbook_get` and
   `includeInstructions: true`, then send `instructions` with
   `vf_playbook_update`: the moved section, plus a copy of each shared rule the
   moved job needs, such as a verification or tone rule. A playbook never sees
   the main agent's instructions. Name the main agent's tools in plain words, not
   in backticks: a backticked name in a playbook resolves only to its own tools.
   Check `unresolvedMentions`.
3. Read every page of the main agent's text again. Then send one
   `vf_agent_update` with `playbooks`, every entry exactly as read plus the new
   one, and `instructions`, the whole text with the moved section replaced by
   one routing line. For example: "Route to the `Billing` playbook when the user
   asks about an invoice or a refund." The routing list is saved first, so the
   new name resolves. Check `unresolvedMentions`.

The `playbooks` list replaces the whole routing list, so an entry you leave out
is a route you delete. No check can name the new playbook before it exists, so
leave the tests as they are.
