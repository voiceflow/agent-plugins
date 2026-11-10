# Request shapes for common product work

These small examples were verified against hosted Voiceflow MCP and CLI 0.287.0
on 2026-10-16. The MCP then took each operation inside one grouped tool. The v3
tools take the same fields without that wrapper, as the next section shows. Use
current schemas when they differ. Substitute IDs from live reads; the
capitalized values below are placeholders, not customer resources.
Read only the section relevant to the task. These are examples, not a full API
catalog or authorization to run them.

## Identity and greeting

The global persona lives in the agent's `prompt`; the opening message and routing
guidance live in its `instructions`. These are separate from a playbook's
instructions. Reading only route metadata can hide the sample-company text that
still controls the greeting.

CLI: `agent get --include-prompt --include-instructions` with project/environment
flags. MCP: `vf_agent_get` with `includePrompt: true` and
`includeInstructions: true` beside `projectID` and `environmentAlias`.

Update these fields with `vf_agent_update` and
`body: {"prompt":"<global instructions>","instructions":"<main-agent instructions>"}`,
or CLI `agent update --prompt '<global instructions>' --instructions '<main-agent instructions>'`.
Read the full text first and preserve unrelated instructions; these fields
replace their text. Omit settings and route arrays that do not need to change.
Read back both fields explicitly, then compile before testing a fresh greeting.
Changing the playbook name or project name alone does not change this identity.

## MCP input and function declarations

Each MCP v3 tool runs one operation and is named `vf_<group>_<operation>`.
Path and query fields, such as `projectID` and `environmentAlias`, sit at the
top level of the tool's input. Write and execution parameters generally belong
in `body`. Many tools list a short schema; read the full one with
`vf_describe_operations` before a tool's first call. A function's
`vf_function_get_schema` describes its execution inputs and outputs, not the
request schema for creating or attaching it.

For `vf_function_execute`, execute a declared input by its name:

```json
{
  "projectID": "PROJECT_ID",
  "environmentAlias": "ENVIRONMENT_ALIAS",
  "functionID": "FUNCTION_ID",
  "body": {"inputs": {"email": "  ADA@EXAMPLE.TEST  "}}
}
```

Send `inputs` inside `body`; `inputVars` is not an execution field. CLI
equivalents use `function execute --inputs '<JSON>'`.

For `vf_function_create_variable`, the body is
`{"functionID":"FUNCTION_ID","name":"email","type":"input"}`.
Use `type: "output"` for output declarations. This type selects the declaration
direction, not a JSON scalar type. For `vf_function_create_path`, the body is
`{"functionID":"FUNCTION_ID","name":"success"}`. Both tools also need
`projectID` and `environmentAlias`. Read `vf_function_list_variables` to obtain
declaration IDs; names alone are insufficient for attachment bindings.

## Attach a function and capture its results

Read the function declarations, playbook, existing attachment, and intended
project variables first. `vf_tool_list` needs either `playbookID` or
`global: true`; omitting both can return `Tool target does not exist` even when
the project is valid.

For `vf_tool_create`, use this body, with `projectID` and `environmentAlias`
beside it. `target.playbookID` is the target selector; `target.id` is not.

```json
{
  "type": "function",
  "functionID": "FUNCTION_ID",
  "target": {"playbookID": "PLAYBOOK_ID"},
  "description": "Look up an order's status when the customer supplies an order ID.",
  "inputVariables": {
    "INPUT_UUID": {
      "functionInputVariableID": "INPUT_UUID",
      "required": true,
      "defaultValue": null
    }
  },
  "captureResponse": {
    "OUTPUT_UUID": {
      "functionOutputVariableID": "OUTPUT_UUID",
      "variableOrEntityID": "PROJECT_VARIABLE_ID"
    }
  }
}
```

Repeat capture entries for each output. Use a declared function input UUID for
the input map key and its inner ID. For outputs, verify the inner output ID and
destination project variable ID. The live checks accepted output map keys that
were names as well as UUIDs; use UUID keys consistently for new attachments.

CLI 0.287.0 accepts the function-specific JSON flag
`tool create --body-param.function '<body JSON above>'` with project/environment
flags. Its general help can abbreviate the nested schema. An accepted attachment
does not prove its inputs/captures are correct: inspect them and, when testing is
authorized, inspect conversation variables after two distinct tool inputs.

## Register routes

For `vf_agent_update`, the routing body uses `playbookID` and
`workflowID`, not generic `id` keys:

```json
{
  "playbooks": [{"playbookID": "PLAYBOOK_ID", "description": "Collect an appointment request when the customer asks for one."}],
  "workflows": [{"workflowID": "WORKFLOW_ID", "description": "Give the final request confirmation and end when the customer asks to finalize it."}]
}
```

These arrays replace the existing arrays. Merge with their complete current
contents rather than copying this example over existing routes. CLI accepts
the corresponding arrays through `agent update --playbooks` and `--workflows`.

## A message followed by End

First create a message resource with `variants: [{"text":"Your request is ready for review."}]`
using `vf_message_create` (`body.variants`) or CLI `message create
--variants`. Use its returned message ID in the workflow step.

For `vf_workflow_create_block`, send `projectID`, `environmentAlias`, and
`workflowID` beside this body:

```json
{
  "name": "Confirm request",
  "steps": [
    {"kind": "message", "content": {"responseType": "message", "messageID": "MESSAGE_ID"}},
    {"kind": "end"}
  ]
}
```

The discriminators are `kind` for the step and `responseType` for its message
content. A bare `content.messageID` is insufficient. CLI uses `workflow
create-block --name 'Confirm request' --steps '<steps array>'` plus scope flags.
Steps in this block execute sequentially; the message does not wait for a reply.

Read the workflow's entry step and new block ID. Connect them using the actual
returned port. For the entry's `next` port, `vf_workflow_link` takes `stepID`
and `portKey: "next"` at the top level and `toBlockID` inside `body`. CLI uses
`workflow link --step-id ENTRY_STEP_ID --port-key next --to-block-id BLOCK_ID`
with workflow/project/environment flags. Read back entry, links, and warnings.

An End step can also deliver a message with
`content: {"responseType":"message","messageID":"MESSAGE_ID","responseEnabled":true}`.
Both arrangements were verified at runtime; choose the simpler one for the task.

## Import a text document over MCP

The hosted `vf_document_create_text` tool accepts a file object in its body.
It handles the multipart upload; a chat agent does not need a terminal or a
public URL for short text it is authorized to import.

```json
{
  "projectID": "PROJECT_ID",
  "environmentAlias": "ENVIRONMENT_ALIAS",
  "body": {
    "file": {
      "filename": "returns-policy.txt",
      "mimeType": "text/plain",
      "content": "Unused items can be returned within 17 days."
    }
  }
}
```

Use `filename`, not `name`, and `mimeType`, not `type`. A malformed file can be
accepted with the name `undefined`; inspect the returned document before any
retry. CLI uses `document create-text --file <path>` and takes the filename from
that path. Do not create a duplicate merely to rename an accepted document;
report a naming limitation if the current update schema cannot rename it.

Wait for ingestion to succeed, then query the intended draft. MCP
`vf_knowledge_base_query` uses
`body: {"version":"draft","question":"What is the return window?","synthesis":false,"chunkLimit":3}`.
Verify the returned source and content. A successful upload response or an empty
retrieval does not establish that the knowledge is usable.

## Compile before a draft conversation test

After editing routing, instructions, tools, or workflows, compile the intended
draft before testing it. MCP: `vf_environment_compile` with `projectID` and
`environmentAlias`. CLI: `environment compile` with those scope flags. Check the result, then start a fresh conversation with version
`draft`. Compilation is distinct from publishing; do not publish to refresh a
test. In the live checks, an uncompiled draft still executed the old routing.

Pure function executions and direct KB queries can succeed before compilation;
they do not prove that a conversation is using the new agent configuration.

For MCP `vf_conversation_send`, put `projectID`, `environmentAlias`, and a
fresh synthetic `userID` at the top level, and use
`body: {"version":"draft","action":{"type":"launch"}}`.
Subsequent turns use `action: {"type":"text","payload":"<visitor message>"}`
with the same user and version. Unlike `send`, `vf_conversation_get_state`
takes `version: "draft"` at the top level with those scope fields. Putting the
send version outside its body causes a validation error even when the action
is correct.

CLI uses `conversation send --user-id '<fresh user>' --version-param draft
--action '{"type":"launch"}'` with project/environment flags. Supply an explicit
action; invoking send without one does not start the conversation. Read captures
with `conversation state get` and the same scope, user, and draft version.

The current runtime was also observed executing a main-agent-only conversation
with empty route registries. CLI 0.287.0 help warns otherwise. Verify actual
responses instead of treating the debug line `no workflows or playbooks defined`
as a failed conversation by itself; preserve existing routes when extending an
agent regardless.
