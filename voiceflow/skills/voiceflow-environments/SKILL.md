---
name: voiceflow-environments
description: Resolve Voiceflow environment aliases and drafts, clone environments, compare changes, and manage explicitly requested merges or publishing.
license: MIT
---

# Environments and release actions

For questions about draft/live behavior, cloning, shared resources, merges, or publishing
that this skill does not answer, follow the
[docs MCP workflow](../voiceflow/references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Include package/skill/stage context in `why` as
described there. Reuse guidance for the same issue; consult it whenever unsure.

Read the [operation contract](../voiceflow/references/operations.md). Resolve the
project and environment from live data. An environment alias, environment ID,
and version ID are different. Draft-editing operations use the alias required
by their schema. Never silently choose Main because it is the default.

## Where to make a change

Main is what live traffic hits. For a project with a live version, propose a
working environment for the change: a clone of Main named for the change in a
few words, such as Refund policy update. Clone only after the user agrees,
because a project has Main and up to nine more environments. Use one
environment for the whole change, not one per edit, and pass its alias on every
write. A clone copies Main's draft as it stands, unpublished edits included.

For a new project with nothing live, edit Main's draft. When the user asks to
change Main directly, for example because they test only on the live build,
edit Main's draft and say once that each publish of Main puts the change live.

With nine environments besides Main, another clone is refused. Ask which one
to retire and delete only the one the user names, because its draft goes with
it. An environment that still receives traffic needs its traffic moved first.

## Drafts, clones, and tests

Each environment has draft and live content. A user can mean unpublished draft
changes when asking to clone; inspect clone options and source version. Do not
publish merely to make a clone include recent edits.

Compile draft edits before a conversation test: use the environment's `compile`
operation, check its result, and start a fresh draft conversation. This refreshes
the runtime representation without publishing. See the
[verified compile sequence](../voiceflow/references/request-shapes.md#compile-before-a-draft-conversation-test).

Environment isolation has limits: knowledge document bodies and evaluation
resources can be project-shared; secret names are shared while values are
environment-specific. Cloning can copy secret values and does not isolate
external services.

Publishing content does not promote Draft secret values to Default values.
Discarding or reverting content does not undo credential changes. A merge may
preserve Main's secret values or override them depending on options; inspect the
actual behavior before proceeding.

## Promote a change to Main

A merge takes the source environment's published version, not its draft. So
publish the working environment, wait for the publish result, then merge it
into Main. The merge replaces Main's live version, so the change is live when
it finishes; do not publish Main afterwards. The merge can also delete the
working environment. Offer that, and keep the environment if the user wants it.

The environment reads do not say when the working environment last took Main's
changes. The merge dialog on the Environments page warns when Main published
since then, because a merge would overwrite that release. When it warns, or the
user says Main changed, offer Pull from Main first, if the workspace has it.
Only the user can run it, from the Environments page. A pull brings Main's
changes into the working environment's draft only, so the order is: pull,
publish the working environment, then merge. A merge after a pull alone still
overwrites Main's newer release.

## Authorization

Publish, merge, deletion, and traffic changes require scope from the user.
Read the current diff/state and explain the concrete effect before an approval
when authorization is missing. Protected environments may restrict these actions
to admins/owners. Do not bypass protection.

After an authorized release action, verify the resulting status/version and
report what became live. A saved draft is not a deployment.

Source: [Environment overview](https://www.voiceflow.com/docs/documentation/deploy/environments/overview).
