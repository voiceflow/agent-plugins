# Custom trace functions

How a function sends a custom trace, such as a form or a voice transfer, and
waits for the user's answer. Read this before writing a function that a widget
extension or the voice runtime renders.

## How they differ from a standard function

A custom trace function returns a trace of its own type, which a chat widget
extension or the Twilio voice runtime renders. With
`next: { listen: true, to: [...] }` it pauses the conversation until the
extension sends an event back with `interact()`. The function does not run again
when the event arrives: the runtime follows the matching path on the canvas.

- `next.listen: true` replaces `next.path`.
- `next.to` maps incoming events to canvas paths with match queries.
- `next.defaultTo` is the fallback path.
- Path names are your own, such as `submitted` or `cancelled`.
- The function only sends the trace and pauses. It does not process the answer.
- Every path needs steps on the canvas. A path with nothing after it ends the
  conversation, and the runtime does not pause.

## Example: a form that waits

```javascript
export default async function main(args) {
  const { form_title, fields } = args.inputVars || {};

  let formFields;
  try {
    let parsed = fields;
    if (typeof parsed === 'string' && parsed.trim()) parsed = JSON.parse(parsed);
    if (parsed && !Array.isArray(parsed)) parsed = [parsed];
    formFields = parsed && parsed.length
      ? parsed
      : [
          { name: 'full_name', label: 'Full name', type: 'string', required: true },
          { name: 'email', label: 'Email address', type: 'email', required: true },
        ];
  } catch (err) {
    return {
      trace: [{ type: 'debug', payload: { message: 'Invalid fields JSON: ' + String(err?.message || err) } }],
      next: { path: 'error' },
    };
  }

  return {
    trace: [{
      type: 'form',
      payload: {
        formSlug: 'dynamic-form',
        title: form_title || 'Contact information',
        fields: formFields,
        submitButtonText: 'Submit',
        cancelButtonText: 'Cancel',
      },
    }],
    next: {
      listen: true,
      to: [
        { on: { 'event.payload.event.name': 'form_submitted' }, dest: 'submitted' },
        { on: { 'event.payload.event.name': 'form_cancelled' }, dest: 'cancelled' },
      ],
      defaultTo: 'cancelled',
    },
  };
}
```

The input handling accepts a JSON string, a parsed array, or a single object,
because the same input can arrive in any of these shapes.

`listen: true` pauses until an `interact()` event arrives. `listen: false`
carries on, but the events stay available for the session, which suits a
carousel the user might click later.

## Fire-and-forget traces

For a one-shot trace, such as a TwiML SIP transfer, leave out `next`: no paths,
no listening, no outputs. The trace is sent, and the conversation ends or the
voice runtime takes over.

```javascript
export default async function main(args) {
  return {
    trace: [{
      type: 'twiml',
      payload: `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial>
    <Sip>sip:agent@example.sip.twilio.com;transport=UDP</Sip>
  </Dial>
</Response>`,
    }],
  };
}
```

## Match the event to a path

The widget extension sends an event like this:

```javascript
window.voiceflow.chat.interact({
  type: 'event',
  payload: {
    event: { name: 'form_submitted' },
    payload: JSON.stringify({ full_name: 'Ada Example' }),
  },
});
```

The runtime wraps that payload in its own event, so a `to` query matches the
full path `event.payload.event.name`. Querying `event.type` or `event.name`
never matches. Each `dest` must equal a canvas path name exactly.

## Register the extension

A chat widget extension goes inside `assistant: { extensions: [...] }` in
`chat.load()`. A top-level `extensions` is ignored without an error.

```javascript
window.voiceflow.chat.load({
  verify: { projectID: 'PROJECT_ID' },
  url: 'https://general-runtime.voiceflow.com',
  versionID: 'production',
  assistant: { extensions: [FormExtension] },
});
```

For the extension itself, see the
[widget extension guide](https://www.voiceflow.com/docs/documentation/deploy/widget/web-chat-extensions).
