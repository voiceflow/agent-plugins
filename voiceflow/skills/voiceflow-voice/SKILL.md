---
name: voiceflow-voice
description: Configure or improve Voiceflow agents for spoken conversations, voice settings, turn handling, and phone interactions.
license: MIT
---

# Spoken conversations

For questions about voice providers, turn handling, interruptions, telephony, or transfer behavior
that this skill does not answer, follow the
[docs MCP workflow](../voiceflow/references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Include package/skill/stage context in `why` as
described there. Reuse guidance for the same issue; consult it whenever unsure.

Read the [operation contract](../voiceflow/references/operations.md). Identify the
channel and current voice/provider settings before editing. Use supported
provider values from live schemas; never invent a voice ID.

Prefer short spoken turns, one question at a time, and explicit confirmation for
ambiguous names, dates, amounts, and identifiers. Do not read Markdown, URLs, or
long lists verbatim. Preserve already-known context instead of restarting the
conversation after routing. The voice reads the same text a chat would show, so
HTML, Markdown, or symbols meant for a screen in a reply are spoken aloud.

## Pronunciation

When the voice misreads a word, name, or code, prefer an entry in the
pronunciation dictionary over a prompt rule: the dictionary acts on the spoken
text itself. Each entry maps a written word, `from`, to how the voice says it,
`to`; an empty `to` makes the voice skip the word. It changes what the voice
says, not the text, and holds at most 500 entries. Words match ignoring case,
so `Dr.` and `dr.` are one entry.

Read the dictionary from the agent read, under `voice.pronunciationDictionary`.
Change it with `voiceflow_agent.patch_pronunciation`: `set` adds a word or
changes how it is said, and `remove` deletes words. Send only the words that
change. Never send the whole dictionary through an agent update to change a few
words: that replaces every entry and loses changes made since your read. CLI
0.287.0 has no command for the patch; the UI step is Voice output in the
agent's Behaviour settings. A change reaches calls only after the environment
is compiled.

Separate prompt problems from transcription, endpointing, interruption, silence,
and telephony configuration. Use a specific transcript/trace to identify which
layer failed. A successful text test does not establish audio quality or phone
routing correctness.

Phone-number assignment and outbound calls can affect real people and billing.
Only perform them within the user's explicit task. Inspect configuration before
placing calls. Custom traces or transfer payloads require the documented runtime
contract; do not assume a chat trace works in telephony.

Use [functions](../voiceflow-functions/SKILL.md) for custom transfer logic and
[evaluations](../voiceflow-evaluations/SKILL.md) for scoped voice testing. To
give the agent a phone number, or to move or disconnect one, use
[phone numbers](../voiceflow-phone-numbers/SKILL.md).

Source: [Voiceflow documentation](https://www.voiceflow.com/docs).
