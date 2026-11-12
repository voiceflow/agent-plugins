---
name: voiceflow-optimize-playbooks
description: Condense a long Voiceflow playbook or main-agent instructions without changing behavior, or move a separate job into its own playbook. Use when asked to shorten, clean up, or split instructions.
license: MIT
---

# Condense or split long instructions

For questions about playbooks, instruction size, routing, or tests that this skill
does not answer, follow the
[docs MCP workflow](../voiceflow/references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Put only the package/skill/stage tag in `why`,
as described there. Reuse guidance for the same issue; consult it whenever unsure.

Read the [operation contract](../voiceflow/references/operations.md). Resolve the
working environment first, as
[environments](../voiceflow-environments/SKILL.md#where-to-make-a-change) describes.

This skill makes a long playbook, or the main agent's instructions, shorter
without changing what the agent does. It can also move a separate job into a
playbook of its own. Show one plan, ask once, then build every part and run the
same tests before and after.

## Condense or split

Each model call of the running agent sees the global prompt and the
instructions of the one active playbook. Other playbooks appear only as
transfer tools with a name and a description. So a split saves context only
while a conversation stays inside one job. Each move between playbooks costs
one more model call, and a turn allows at most 10.

- Condense first. Most long playbooks are one job that gathered corrections and
  rules over time. A shorter text is the fix.
- Split only when a part serves a different user job, has its own tools or its
  own way in, such as a routing entry or a workflow step, and a conversation
  usually stays inside one job.
- Split by product or topic only when each product has its own steps and tools.
  When the products share the steps and the detail comes from tools, condense.
- A rule that holds for every job may belong in the global prompt. Suggest it
  in the plan. Never move it there yourself.

When the user asks only to optimize, condense, and say in the plan whether a
split would help. When they ask to split, condense and move each separate job
that passes the split test. The main job, the one most rules serve, stays where
it is. Never leave the main agent with only routing.

## Read everything first

Change nothing until the user answers the plan.

1. Every page of the text: `vf_playbook_read_instructions`, or
   `vf_agent_read_instructions` for the main agent, from line 1. Call again with
   `offset` set to `nextOffset` until `nextOffset` is null. A page holds at most
   24,000 characters.
2. What the playbook owns: `vf_playbook_get` for its settings and system tools,
   `vf_tool_list` with its `playbookID` for its tools, and
   `vf_playbook_list_paths` for its exit paths with their `requiredVariables`
   and `messages`. For the main agent, call `vf_tool_list` with `global: true`.
3. The routing list: `vf_agent_get`. Its `playbooks` list holds each entry's
   `condition`, `description` and `requiredVariables`.
4. The links into it: `vf_environment_search_text` with `pattern` set to the
   playbook's ID. While `hasMore` is true, call again with `offset` set to
   `nextOffset`. A `workflow` hit with a `stepID` is a workflow step that runs
   or lists the playbook. A `test` hit is a routing check. A `canvas` or
   `initialization_workflow` hit is a step the workflow tools cannot change, so
   name it in the plan and condense instead of splitting. Search once more with
   the playbook's name to find plain-text mentions. If a page says
   `incomplete: true`, or the search is refused, say the list of links may be
   short, and do not split.
5. The tests: the routing checks from the `test` hits, and tests named for the
   job in `vf_test_list`. Pick at most 10, the ones that route to it first.

## The plan and the one question

Keep the plan short and concrete:

- the size now, in characters, and the size you aim for;
- for a condense: what repeats and will merge, each contradiction the user
  must decide, and what looks out of date, which stays unless the user says to
  drop it. Every rule, every reference, the `## Inputs` section and the exit
  criteria stay;
- for a split: the new playbook's name, its job and when it runs, the sections
  that move, how conversations reach it, and what changes in the original;
- each routing entry and routing line you will change;
- the tests you will run before and after, each outside system they can reach,
  such as a tool that sends or books for real, and that every run uses credits.

Then ask one question in plain text. It asks for the go-ahead, with the test
runs named. When the plan moves a job, offer "condense and move the job" or
"condense only". Never offer to move every job out of the main agent. List each
contradiction with both versions of the rule. When no test covers the
playbook, offer to create a few first, as
[evaluations](../voiceflow-evaluations/SKILL.md) describes. Change nothing
before the user answers.

## After the go-ahead

1. Start the tests with `vf_test_create_many_runs`, and read each run until it
   finishes, as [evaluations](../voiceflow-evaluations/SKILL.md) describes. Keep
   each test's passed checks. A test run builds the environment first, so do
   not compile.
2. Make the changes, as below.
3. Run the same tests again. Make no write after these runs, unless a test
   failed because of the change. Then say so, fix the agent, never the test,
   and run the same tests once more.
4. Report once: what changed, the size before and after, and the passed checks
   before and after for each test. Name any test that got worse and the likely
   cause.

Once the first run starts, never create, change or delete a test, a turn or a
check, not even to make it pass. If a check is wrong after the change, for
example one that expects the main agent to answer a job that moved, name it in
the report and leave it.

## A condense is one whole replace

1. Read every page of the text again, right before the replace.
2. Send the whole new text in one `vf_playbook_update` with `instructions`. For
   the main agent, send one `vf_agent_update` with `instructions`.
3. Check `unresolvedMentions` in the result. It must be absent or empty. Fix a
   name it lists with `vf_playbook_patch_instructions` or
   `vf_agent_patch_instructions`.

A condense keeps every distinct rule, even one stated once. It keeps every
reference exactly as written: `name` for a tool, playbook or workflow, and
`{name}` for a variable. It keeps the `## Inputs` section, the exit criteria,
and the clearest WRONG and RIGHT example for each behavior. It removes repeats
and words that add nothing, and keeps the order and headings. Sections marked
with tags such as `<rules>` become markdown headings. It drops a rule that looks
out of date only when the user says so.

## Split the main agent's instructions

Every tool on the main agent is global: every playbook can call it, workflow
tools included. So a new playbook can call the main agent's tools, and this
split moves text only. Follow [split the main agent](references/split-main-agent.md).

## Split a playbook

Splitting one playbook into two needs a copy that keeps its tools, exit paths
and messages. The operations these skills name cannot make that copy yet, and
rebuilding each tool by hand is easy to get wrong. Condense instead, and tell
the user that a split of this playbook is not available here yet.

Sources: [Playbooks](https://www.voiceflow.com/docs/documentation/build/playbooks),
[Tests](https://www.voiceflow.com/docs/documentation/measure/tests).
