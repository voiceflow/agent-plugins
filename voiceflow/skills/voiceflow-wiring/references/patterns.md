# Wiring patterns

Four proven ways to wire a function's inputs and outputs. Read this when you
design a new tool attachment or decide how a value should reach project state.

Every map is keyed by the function variable's UUID. A `defaultValue` names a
project variable in braces; `variableOrEntityID` takes the variable's ID. The
full attachment body is in
[attach a function](../../voiceflow/references/request-shapes.md#attach-a-function-and-capture-its-results).

## 1. Read-only lookup

The function reads from an API and returns data, such as `getOrderStatus`.

- Inputs: usually an ID with a known source, plus authentication.
- Make inputs `required: false` with defaults from project variables, but only
  when something writes each variable on every path to the tool.
- Capture outputs into project variables when a later tool uses them. At least
  capture the status values the agent branches on.

```jsonc
{
  "inputVariables": {
    "<orderId-uuid>": {
      "functionInputVariableID": "<orderId-uuid>",
      "defaultValue": "{order_id}",
      "required": false
    },
    "<token-uuid>": {
      "functionInputVariableID": "<token-uuid>",
      "defaultValue": "{session_token}",
      "required": false
    }
  },
  "captureResponse": {
    "<status-uuid>": {
      "functionOutputVariableID": "<status-uuid>",
      "variableOrEntityID": "<order_status variable ID>"
    }
  }
}
```

## 2. State change

The function writes somewhere else, such as a ticket or a backend record.

- Inputs: a mix of what the model supplies, such as the ticket text, and values
  filled from project variables, such as IDs and authentication.
- Outputs: return the values the function accepted, even when they came in as
  inputs, so `captureResponse` can make the effect visible in project state.

```javascript
return {
  next: { path: 'success' },
  outputVars: {
    orderId: acceptedOrderId, // echo the input so the capture stores it
    ticketId: createdTicketId, // new value from the API
  },
};
```

## 3. Side effect only

The function does something, but its result is not needed elsewhere.

- Outputs and captures are usually empty.
- Inputs are `required: false` with defaults from project state, under the same
  rule about a writer on every path.

To keep an argument the model chose, such as a category, add a
`captureInputVariables` entry on the attachment:
`{"<category-uuid>": {"variableOrEntityID": "<category variable ID>"}}`.

## 4. The model's decision is the data

The model's choice is the value, with no other source: a ticket subject, a
dispute reason, a picked time slot.

- Input: `required: true`, with no default.
- Return it as an output too, so `captureResponse` stores it for later tools.
