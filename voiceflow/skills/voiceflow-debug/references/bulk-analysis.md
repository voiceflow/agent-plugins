# Bulk transcript analysis

How to find a pattern across many conversations, then prove it. Read this when
the user asks what goes wrong across a period, not in one conversation.

## Load the project first

Before pulling any transcript, read the agent's setup: the global prompt, the
main-agent instructions and routing, the playbooks, and their tools. Without it
you will misclassify the same failure many times over.

## Pick the read

- Find candidates with `voiceflow_transcript.search`. Narrow with the date
  range, evaluation results and transcript properties before paging. Keep pages
  small, about 20 rows, and page with `skip` while the result says there is
  more. Each row already carries the transcript's evaluation scores.
- Look for a known marker, such as an error text or "transfer to a human", with
  `voiceflow_transcript.query_logs` on each candidate: `search` for the text,
  or `levels: ["fatal", "error", "warn"]` for failures. It returns only the
  matching entries.
- Read whole conversations with `voiceflow_transcript.get`, only for the few you
  deep-read. A voice call can be tens of thousands of tokens.
- When a read is cut or too long, read the turns that matter with
  `voiceflow_transcript.query_logs` and `turns`, `levels` or `debugKinds`.

Never read 20 or more transcripts in full. Search and filter first, then
deep-read the few that matter.

## Triage before reading

Skip the marker search when the complaint is vague, such as "quality feels
off", and start here.

1. Take one page of search results for the period and sample.
2. Run evaluations only when the user asked for it, and only for transcripts
   missing a score you need. One `voiceflow_evaluation.run` call takes several
   evaluations and transcripts; batch them instead of looping.
3. Build a matrix of transcripts against evaluations:

   ```text
   Transcript | Eval A | Eval B | Eval C | Fails
   ---------- | ------ | ------ | ------ | -----
   T1         | FAIL   | FAIL   | PASS   | 2
   T2         | PASS   | PASS   | PASS   | 0
   T3         | FAIL   | PASS   | FAIL   | 2
   ```

4. Sort by failures. Read the worst first.
5. Count the pass and fail rate per evaluation, for example "Escalation: 18 of
   28 failed (64%)". This alone often shows where the problem lives.

## Deep-read three to five

Pick for variety, because the first pattern you find is usually the most
obvious one, not the most important:

- two or three of the worst performers;
- one passing transcript, to see what correct looks like;
- one edge case when there is room: unusual length, input, or mixed results.

For each one, record:

- the turn where the issue happened, by number;
- the agent's exact text, one or two sentences;
- what it should have done, citing the prompt or playbook rule;
- which evaluation failed and what it checks;
- whether it matches a pattern you already saw.

## Cross-check

Answer these before reporting:

1. Do transcripts that fail one evaluation also fail another? Then they likely
   share a cause.
2. Do low satisfaction scores overlap with one evaluation's failures? Give the
   numbers, such as "4 of 5 low scores also failed escalation".
3. Are failures concentrated in one playbook?
4. How many distinct failure modes did you find? If only one, read more.
5. Is the agent at fault, or is the cause upstream, such as user confusion or a
   knowledge gap, or downstream, such as a backend system?

## Evidence standards

- Frequency: "N of M transcripts (X%)", never "several" or "some".
- Examples: name at least three transcripts by ID for any pattern.
- Quotes: the exact agent text that shows the issue, without personal data.
- Fix: the exact text to add or change, and where, not "improve the prompt".
- Severity: why it ranks where it does, from frequency, user impact, and fix
  effort.

## Fix order

When several issues exist, fix in this order:

1. Safety and compliance, such as leaking sensitive data.
2. Made-up critical information.
3. Core function: broken tools or the main use case.
4. Experience: tone, length, flow.
5. Rare edge cases.

The causes and fix templates are in [failure patterns](failure-patterns.md).
