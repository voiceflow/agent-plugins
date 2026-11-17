# Common failure patterns

Recurring agent failures, how to confirm each one, and a fix template. Read this
after you have classified a failure and before you write the fix.

Adapt each template to the agent's own wording and put it in the layer that
owns the behavior: global prompt, main-agent instructions, or one playbook. See
the `voiceflow-prompting` skill.

## 1. Made-up information

Symptoms: invented order numbers, links, or facts; answers that do not match
what a tool returned.

Check: was the tool called at all; did it return empty or an error; does the
prompt say what to do when data is missing?

```markdown
## No made-up information

Never make up information. If a tool returns nothing or fails:
1. Do not invent data.
2. Say you could not retrieve it.
3. Offer another way: try again, a transfer, or a manual lookup.
```

## 2. Tool not called when needed

Symptoms: generic or guessed answers where the agent has a tool for real data.

Check: the tool's attachment description must say both what it does and when
to call it. If the "when" lives only in one playbook's instructions, other
routes never see it. This is the most common cause of a skipped tool; see
the `voiceflow-build` skill. Then check that the active playbook's
instructions also say when to call it.

```markdown
## Required tool use

When the user asks about [topic], call [tool name] first. Do not guess.
- Order status: call [order lookup tool]
- Account balance: call [balance tool]
```

## 3. Tool error not handled

Symptoms: the agent carries on as if a failed call succeeded, or invents data
after an error.

Check: what the tool returned in the log, whether the prompt covers errors, and
whether the function reports its errors on a path or output.

```markdown
## Errors

If a tool returns an error, nothing, or unexpected data:
1. Do not continue the normal flow.
2. Do not make up replacement data.
3. Say: "I'm having trouble retrieving that information."
4. Offer a transfer or to try again later.
```

## 4. Internal details leak

Symptoms: the agent mentions a knowledge base, database, API, tool names, or
"checking our system".

```markdown
## Silent tools

Run tools without mentioning them. Never mention searches, tool names, API
calls, or routing. Present the result as your own answer.
```

## 5. Lost context

Symptoms: the agent asks again for details the user gave, or forgets the
current task.

Check: whether the details were saved to variables, whether the prompt says to
keep them, and whether a very long conversation is the cause.

```markdown
## Context

Keep everything the user told you in this conversation: name, details already
collected, and the current task. Never ask again for something already answered.
```

## 6. Wrong tone

Symptoms: too formal or too casual, inconsistent, off-brand.

```markdown
## Tone

Use a [casual / professional] tone.
- Say: [phrases to use]
- Avoid: [phrases to avoid]
- Example: [one ideal reply]
```

## 7. Wrong length

Symptoms: walls of text, or answers missing what the user needs.

```markdown
## Length

Keep replies [brief / standard / detailed], about [X to Y] words.
On voice, at most two sentences per turn.
Always include: [essentials]. Leave out: [extras].
```

## 8. Voice problems

Symptoms on voice agents: numbers read wrongly, several questions in one turn,
references to buttons or screens, poor recovery from misheard speech. See the
`voiceflow-voice` skill.

```markdown
## Voice

Ask one question per turn.
Say numbers in words: "twenty-five", "one hundred and fifty dollars".
Read phone numbers in groups: "five five five, one two three, four five six seven".
Never mention buttons, screens, or links to click.
```

## 9. Handoff problems

Symptoms: transfers that should not happen, missing transfers, or an abrupt
handoff.

```markdown
## Handoff

Transfer to a person only when:
- [trigger 1]
- [trigger 2]
- the user asks for a person.
Do not transfer for: [cases the agent handles].
Before transferring, say: "[handoff message]".
```

### Repeat contact is not a transfer loop

Many turns and many transfer calls in one user's history often look like a
loop. Verify before you call it one:

| Signal                     | Transfer loop (bug)         | Repeat contact (not a bug)    |
| -------------------------- | --------------------------- | ----------------------------- |
| Successful handoff events  | None or very few            | About one per transfer call   |
| Timing of user messages    | Seconds or minutes apart    | Hours, days, or weeks apart   |
| Session launches           | Few or none                 | Many                          |
| External ticket or chat ID | None, or the same one again | Several different ones        |

The key check: compare transfer calls with successful handoff events. If they
match about one to one, the transfer works, and the user keeps returning because
the issue is not solved on the human side. Then ask why, whether the handoff
passes enough context, and whether returning users should be treated
differently.

A real loop shows no successful handoff and rapid turns in one session. Look at
what runs after the transfer: a re-routing step that sends the user back to the
start, such as transfer, re-route, greet, triage, transfer.

## 10. Call does not end

Symptoms: the agent says goodbye but the call stays open, or the user hangs up.

Check: whether `endTool` is enabled on the agent or playbook that ends the
call, with `vf_agent_get` or `vf_playbook_get`, and whether the prompt says when
to call it.

```markdown
## Ending the call

After saying goodbye, end the call right away. Do not wait for a reply.
```

## 11. Duplicate replies after a model fallback

Symptoms: the agent now and then sends the same reply twice, or a short extra
line follows a tool call.

Check: read the full trace of a turn that doubled with
`vf_transcript_query_logs` and that turn. Look between the two copies for a
line saying the model on the fallback chain had an outage and the runtime fell
back to another model. When that line is there, the model call failed part way
and the runtime retried it on a fallback model, which sent the reply again. No
prompt change fixes it.

Fix: quote that trace line to the user, say a prompt edit will not fix it, and
stop changing the prompt. Suggest switching the agent's model if it keeps
happening. With no fallback line, treat it as a prompt or routing problem, and
run the scenario three times after the fix before calling it fixed.
