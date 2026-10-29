# Reading secrets in a function

How a function receives an API key or other credential, and how the binding
fails. Read this when a function needs a secret, or a secret input misbehaves.

## Declare the secret as an input

Functions do not have `args.secrets`. Reading it returns `undefined`, the
function takes its error path, and the agent then tends to make up an answer
around the empty result.

Declare each secret as an input variable instead, beside the regular inputs, and
check that it arrived:

```javascript
export default async function main(args) {
  const { question, api_key } = args.inputVars || {};

  if (!api_key) {
    return {
      outputVars: { success: false, error: 'missing api_key' },
      trace: [{ type: 'debug', payload: { message: 'api_key not provided; check the tool attachment' } }],
      next: { path: 'error' },
    };
  }

  const response = await fetch('https://api.example.com/search', {
    headers: { Authorization: api_key },
  });
  // ...
}
```

Give the input a description that says it is secret-bound, such as "API key for
Example. Filled from the secret EXAMPLE_API_KEY; do not change."

## Bind it on the attachment

On the tool attachment, `voiceflow_tool.create` or `voiceflow_tool.update`, set
the input's `defaultValue` to the secret's name in braces, `"{EXAMPLE_API_KEY}"`,
and leave `required` out. Key each input by its variable's UUID and repeat that
UUID in `functionInputVariableID`. The full body is in
[attach a function](../../voiceflow/references/request-shapes.md#attach-a-function-and-capture-its-results).

At the start of a turn the runtime replaces the reference with the stored value.
The model never sees the value, because the input is not collected from it.

## Why the secret input must not be collected

If the model is asked to fill a secret input, it leaves it empty or invents
something that looks like a key. Both break the function.

`required` controls this. Leave it out on a secret input: a default that holds a
secret makes it `false`, so the value is filled in and the model is never asked.
An input with any other default, or none, becomes `true`. Sending
`"required": true` with a secret default is rejected, because the two settings
contradict each other. `"required": false` is always accepted.

In the Voiceflow UI, the Agent collect toggle is the same field: on means
`required: true`. Adding a default in the UI does not turn the toggle off. If a
user reports that the agent still asks for a secret input, check the toggle.
See [wiring](../../voiceflow-wiring/SKILL.md) for the other `required` rules.

## Check the secret name

`voiceflow_secret.list` takes the project only, because secrets belong to the
project. It returns each secret's `id`, `name` and `hasValue`, never the value.
Copy the `name` exactly. A mistyped name is saved as literal text, comes back in
the write result's `unresolvedReferences`, and the model is then asked for the
input. A value can differ per environment, and `voiceflow_secret.list_overrides`
reports which, but the name you bind stays the same.

To create a secret or set its value, follow the
[CLI handoff](../../voiceflow/references/cli-handoffs.md#set-a-secret-value).
Never ask for a credential in the conversation.

## Several secrets, several attachments

A function that needs three secrets needs three inputs and three secret
defaults. Each attachment is independent: a function attached to three
playbooks needs the defaults set on all three attachments.

## Check that it works

To run the function yourself with a credential input, as when the user asks
"does it work with order 123?", pass the secret's name in braces as that input,
such as `{EXAMPLE_API_KEY}` or `Bearer {EXAMPLE_API_KEY}`, never the value. The
server fills it in, and the result shows `[secret]`. Any other `{name}` is
refused, because a single run has no conversation to read a variable from; pass
that value directly. The code really runs, so say what it will do outside
Voiceflow and get the user's go-ahead.

In a conversation test, the log shows the function's inputs with the secret
masked as `[secret]`. The literal text `undefined`, or an empty string, means
the binding is wrong.
