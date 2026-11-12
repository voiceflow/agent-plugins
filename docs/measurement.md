# Understand headless onboarding through docs questions

This package does not log its own docs requests. Measure it with controlled
evaluations, and use the Voiceflow Knowledge MCP logs only for traffic that
the package does not configure.

## Who is logged

Every docs connection this package creates adds `logging=off` to the server URL.
That covers the native plugins and the standalone-skill setup. Once the docs
server supports this option, it does not log those requests.

The docs server still logs connections without the option. These include
people who add the docs MCP by hand from the Voiceflow docs, and Voiceflow's
own products that call the docs server. A host can hold both a package
connection and a hand-added one; requests through the hand-added one are logged.

`logging=off` is a provisional name. The docs server does not support it yet.
Until it does, the server ignores the parameter and logs package requests as
before. `scripts/validate.py` holds the exact URL, so a rename changes one value
and the check then lists every file to update.

## Package tag

While the docs tools require a `why` field, the shared
[documentation workflow](../voiceflow/skills/voiceflow/references/documentation.md)
fills it with this tag and nothing else:

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

The website's Knowledge MCP handler records redacted/truncated question and
context, tool, intent, response URLs, confidence/label where available, errors,
latency, and client/session information when the host supplies it. Its existing
log collection and docs-gap reporting are owned by the website repository.
This plugin change does not deploy changes to that pipeline or its dashboard.

Once the server supports `logging=off`, these logs hold no package traffic.
They still show where people with hand-added connections need help. Until then,
package requests also appear, and filtering `why` by the tag separates them:

| Signal | Useful interpretation | Limit |
| --- | --- | --- |
| Setup questions by version/client | Observed setup activity and common connection blockers | Not total installs or unique customers |
| Normal setup documentation checks | The assistant attempted to verify current guidance | A docs answer alone does not prove account access or completed onboarding |
| Troubleshooting topics by skill | Repeated product friction and candidate regression cases | Volume also reflects adoption and consultation behavior |
| Weak answers and tool errors | Candidate documentation, retrieval, or schema gaps | Confidence is not correctness or customer resolution |
| Rephrased questions and follow-up reads | Possible difficulty finding enough evidence | Follow-up reads can be appropriate; session grouping is approximate |

Keep evaluation traffic separate using the test client's declared name and a
recorded run window. Keep unattributed/missing-session traffic visible. Missing
events can mean a host did not use MCP, a connection failed, or collection was
unavailable; they cannot establish a successful or abandoned journey.

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
