# Understand headless onboarding through docs questions

The docs server keeps only anonymous counts for this package's docs requests.
Measure the package with controlled evaluations, and use the Voiceflow
Knowledge MCP logs for traffic that the package does not configure.

## Who is logged

Every docs connection this package creates adds `logging=off` to the server URL.
That covers the native plugins and the standalone-skill setup. With this option
the docs server writes one anonymous count line per call. The line holds the
tool name, `logging: off`, the caller label, the error code, the duration, and a
cold-start flag. It never holds the question, search terms, `why`, `initiator`,
`purpose`, client name, session, result URLs, or confidence.

Package traffic therefore shows only as anonymous counts with caller `public`.
Any other client that sends `logging=off` lands in the same counts, so the
package tag no longer separates package traffic.

Outside the docs server code, Vercel request logs and firewall analytics still
record each request's method, path with query, IP address, user agent, status,
and timing. The query shows `logging=off`. They do not record the POST body,
where the question travels. The in-memory rate limiter holds the IP address for
its time window and never logs it.

The docs server logs connections without the option exactly as before. These
include people who add the docs MCP by hand from the Voiceflow docs, and
Voiceflow's own products that call the docs server. A host can hold both a
package connection and a hand-added one; requests through the hand-added one
are logged.

`logging=off` requires voiceflow/voiceflow-website#617 to be deployed. Until it
is, the docs server ignores the parameter and logs package requests as before.
`scripts/validate.py` holds the exact URL, so a change to it touches one value
and the check then lists every file to update.

## Package tag

On a connection with `logging=off`, `why` is optional and the server drops it,
so the shared
[documentation workflow](../voiceflow/skills/voiceflow/references/documentation.md)
leaves it out. On a connection without the option, the tools still require
`why`, at 3 to 200 characters. There the workflow fills it with this tag and
nothing else:

`vf-agent-plugin/<installed-version> skill=<active-skill> stage=<stage>`

The tag carries no task, symptom, or setup state. Anthropic's directory policy
does not allow collecting extra conversation data, even for logging. The
question already says what the assistant needs.

`stage` is `setup`, `troubleshooting`, or `usage`. A setup error stays `setup`;
`intent=error`, where supported by the tool, distinguishes it from a normal
documentation check. The installed documentation workflow carries package
metadata at its top, so reading the guidance also supplies the version in
standalone skill installs. Unavailable metadata is `unknown`, never guessed.
The tag belongs in `why`, not in the retrieval question. Keep `initiator`
and `purpose` truthful; an autonomous troubleshooting call is still an answer
request, not automatically research.

The tag is self-reported. A host name is not a model name, a connection is not
a person, and a version label does not prove the installation is unedited.

## What the existing pipeline can show

For a connection without `logging=off`, the website's Knowledge MCP handler
records redacted/truncated question and context, tool, intent, response URLs,
confidence/label where available, errors, latency, and client/session
information when the host supplies it. Its existing log collection and
docs-gap reporting are owned by the website repository. This plugin change does
not deploy changes to that pipeline or its dashboard.

These full log lines come only from connections without `logging=off`. They
show where people with hand-added connections need help. A package skill that
reuses a hand-added connection still sends the tag in `why`, so filtering `why`
by the tag finds those requests. Package connections add only anonymous counts
with caller `public`. Those counts show calls, errors, and duration by tool, but
not the question, so the signals below need the full lines:

| Signal | Useful interpretation | Limit |
| --- | --- | --- |
| Setup questions by version/client | Observed setup activity and common connection blockers | Not total installs or unique customers |
| Normal setup documentation checks | The assistant attempted to verify current guidance | A docs answer alone does not prove account access or completed onboarding |
| Troubleshooting topics by skill | Repeated product friction and candidate regression cases | Volume also reflects adoption and consultation behavior |
| Weak answers and tool errors | Candidate documentation, retrieval, or schema gaps | Confidence is not correctness or customer resolution |
| Rephrased questions and follow-up reads | Possible difficulty finding enough evidence | Follow-up reads can be appropriate; session grouping is approximate |

Evaluation runs that use the package URL add only anonymous counts. For a run
on a connection without `logging=off`, keep its traffic separate using the test
client's declared name and a recorded run window. Keep
unattributed/missing-session traffic visible. Missing events can mean a host did
not use MCP, a connection failed, or collection was unavailable; they cannot
establish a successful or abandoned journey.

## Close the loop with verified outcomes

Review recurring or weakly answered questions, sanitize the symptom, and add a
case to [the evaluations](../evals/docs-protocol.md). Improve the authoritative
docs for missing product knowledge; improve a skill for a missing workflow or
verification step. Test the changed package against the original failure and
an unfamiliar variation.

Record consultation, use of evidence, and verified outcome separately. Use
`proposed`, `saved`, `runtime_verified`, `blocked`, or `unverified` as outcome
labels, with the actual evidence and number of user interventions. An advisory
answer may pass its task while its proposed fix remains unverified. Live setup
success requires an account read, usable guidance, and the final build/improve
question; simulation results must remain labeled simulations.

The denominator for a consultation rate comes from controlled test tasks where
we know which issues occurred and whether docs were callable. Server logs alone
cannot measure questions that never reached the server. Actual completion rate
and time to readiness likewise require observed end-to-end sessions; do not
derive either from a lack of subsequent troubleshooting questions.
