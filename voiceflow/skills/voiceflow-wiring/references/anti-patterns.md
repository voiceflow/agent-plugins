# Wiring anti-patterns

Wiring mistakes that look fine in the editor and fail at runtime, with the fix
for each. Read this when a tool gets empty, wrong, or invented values.

## 1. A default from a variable nothing writes

An input defaults from `{account_id}`, but no tool or step ever writes that
variable. Every call gets an empty value and the function fails.

Fix: find the function whose response carries the value, add an output, and
capture it into the variable on that function's attachment.

## 2. Collected input for a value with a known source

An `orderId` input is `required: true` with the default `{order_id}`. The model
is asked to fill it, and sometimes invents an ID, leaves it out, or gets it
right.

Fix: set `required: false`, so the default is always used. Only do this when a
writer sets the variable on every path to the tool; otherwise see 8.

## 3. A function returns nothing a later tool needs

A refund tool takes `refundTotal`, but the tool before it does not return the
amount, so the model has to carry the value through the conversation. That is
fragile.

Fix: add the amount to the first function's outputs, capture it into a project
variable such as `refund_amount`, and default the later input to
`{refund_amount}` with `required: false`.

## 4. `functionInputVariableID` holds a name

Some older create flows left `functionInputVariableID` set to the input's name,
such as `"token"`, instead of its UUID. The editor may still show it correctly,
but the wiring is broken.

Fix: when you update the attachment, repair these IDs in the same update. Do
not carry broken state forward.

## 5. Phantom inputs keyed by name

```jsonc
"inputVariables": {
  "INPUT_UUID": { "functionInputVariableID": "INPUT_UUID" },
  "token": { "description": null }
}
```

The map key must be the declared variable's UUID. The editor looks inputs up by
key, and cloning or importing the agent fails on a name key. Remove the
name-keyed entry, which usually has `description: null`, by sending its key as
`null` in the update's `inputVariables`. Leaving it out of the update keeps it.
Never remove the UUID-keyed entry.

## 6. Prompt fixes for a wiring problem

When a function gets bad arguments, adding more examples to the prompt rarely
helps, because the cause is an empty default, not the model's reasoning.

Fix: inspect the wiring before changing the prompt. If the upstream variable is
never set, capture it. If the input has nothing to choose, change `required`.

## 7. Reading `args.secrets` in function code

```javascript
const apiKey = args.secrets?.MY_API_KEY || '';
```

`args.secrets` does not exist in functions, so `apiKey` is always empty. The
function takes its error path and the model makes up an answer.

Fix: declare `api_key` as an input, read `args.inputVars.api_key`, and on the
attachment set that input's default to `"{MY_API_KEY}"`, keyed by its UUID,
with `required` left out. See
[secrets](../../voiceflow-functions/references/sensitive-inputs.md).

## 8. `required: false` without a writer on every path

The mirror of 2, and more dangerous, because it fails silently. An input is
switched to `required: false` because the variable has a known source, but on
some path nothing writes the variable before the tool runs.

For example, a follow-up tool's name and zip inputs were set to
`required: false`. For returning callers a lookup captured those values. For
new callers only a placeholder such as "Unknown zip" was set at launch, so every
new caller's request was sent with it and rejected. The agent never asked for
the zip, because turning collection off removes the question; it adds no
fallback.

Fix: before switching an input to `required: false`, find what writes the
variable, a captured response or a workflow Set step, and check that it runs on
every path to this tool. If a path has none, keep `required: true` so the agent
asks, or add the missing writer. Treat placeholders set at launch as unset.

## 9. A secret or project variable in an API tool's URL or headers

Symptom: the editor shows a field pointing at a variable that does not exist,
often a bare ID in braces. At runtime the host is malformed or the auth header
is empty, and the call fails with 401, 403, or a DNS error. Nothing reports a
problem at build time.

Cause: an API tool's `url`, `headers`, and `body` resolve only against that
tool's own declared inputs. Project variables, entities, and secrets are not in
scope, so a reference to them becomes empty.

Fix: declare an input on the API tool, reference it from the URL or header, then
bind the secret on every attachment:

```jsonc
{
  "inputVariables": {
    "INPUT_UUID": {
      "apiToolInputVariableID": "INPUT_UUID",
      "description": "Bearer token. Filled from the secret EXAMPLE_TOKEN.",
      "defaultValue": "{EXAMPLE_TOKEN}"
    }
  }
}
```

Leave `required` out: a secret default makes it `false`, so the runtime fills
in the value and the model never sees it. Copy the secret's name exactly from
`voiceflow_secret.list`. A mistyped name is saved as literal text, appears in
`unresolvedReferences`, and the model is then asked for the input.

Never fix a failing secret reference by putting the literal value back in the
URL. The user chose to keep that credential in a secret; a failing binding is a
bug to diagnose.
