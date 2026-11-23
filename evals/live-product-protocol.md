# Live product acceptance protocol

Run this separately from repository tests, with explicit customer authorization
and a disposable Voiceflow project. It performs real draft writes and small
runtime calls. Never add it to CI or run it against an existing customer agent.

## Fixed baseline

Freeze the plugin commit, skill-tree hashes, CLI version, host version, model,
reasoning setting, and request before starting. Keep raw logs in ignored
`test-results/`; publish only a sanitized report. Do not provide grader results,
expected schemas, or another run's answers to an actor. Do not change skills
during the baseline. Record any subsequent fixes and retests separately.

Use eight fresh actor contexts: GPT-6 Luna and GPT-6.1 Sol, each at low and medium
reasoning, over CLI and hosted MCP. Each context receives one five-part customer
journey, so the five items within that journey share context. One run per cell
is a diagnostic sample, not a statistically reliable model success rate.

## Connections and fixtures

1. Confirm the user's intended workspace. Reuse CLI OAuth if it works. Complete
   the MCP host's normal OAuth flow and verify an account read. Never inspect,
   copy, or print credentials.
2. Create one dedicated project, then eight equivalent draft environments with
   zero traffic. Record their initial routing, settings, and release lists.
   Cloning may create an initial release; that is not a later publish.
3. Seed each draft with a `Normalize email` function using `Buffer.from` in the
   Voiceflow sandbox. Declare input `email`, output `normalizedEmail`, and exit
   `success`. Confirm a real execution fails before the actor starts.
4. Supply each actor the unchanged skill library and a synthetic policy:
   unused items are returnable within 17 days, return shipping is free, and the
   support reference is `CEDAR-<unique run key>`. Use a unique document name per
   run because document content can be shared across environments.
5. Limit account operations to the assigned project/environment and transport.
   CLI actors use the verified CLI; MCP actors use only the account MCP for
   account operations. **Both groups also receive the public docs MCP.**
   Restricting the account transport must not exclude documentation tools.
   MCP actors may read local guidance and the fixture, but must not fall back
   to CLI or raw HTTP for account work. This tests an MCP transport path, not
   a real non-coding chat application's interface.
6. Verify docs tools are callable before starting. Follow the
   [docs integration protocol](docs-protocol.md) and preserve the actual docs
   calls/evidence separately from account reads and customer KB queries.
   Missing docs access is an infrastructure limitation, not an agent omission.

Use normal host approval controls. If a sandbox cannot access the existing
OS-keychain session, request the specific command through normal approval;
never bypass review, copy tokens, or restart authentication unnecessarily.
Record an infrastructure-only attempt separately if the harness needs repair.

## Customer journey and acceptance

| Item | Requested result | Independent checks |
| --- | --- | --- |
| Build | Appointment booking playbook collects name and preferred day one at a time, then confirms a request without claiming a booking | Stored instructions, registered route, unrelated settings preserved; conversational behavior when runnable |
| Wiring | Order support playbook calls a pure Lookup order function and captures its echoed ID and `processing` status | Declared inputs/outputs/paths, attachment UUIDs, collection/defaults, capture variable IDs, routing, two pure executions; conversation state for runtime capture proof |
| Workflow | Registered Confirmation workflow says `Your request is ready for review.` then ends | Entry connection, actual step/port topology, referenced message contents, registration; message and end traces when runnable |
| Knowledge | Import the supplied policy into this draft and verify its return window and reference code | Document name/membership, completed ingestion, draft retrieval of both 17 days and that run's unique code |
| Debug | Repair the existing Normalize email function in place | Same function ID and declarations; real executions convert `  ADA@EXAMPLE.TEST  ` and `  BoB@Example.Test ` to their trimmed lowercase addresses |

Actors must preserve existing routing and settings, inspect ambiguous writes
before retrying, and report partial completion accurately. Do not publish,
change traffic, delete resources, call phones, contact external integrations,
modify authentication, or access other customer projects. Stop an operation
if normal approval review rejects it.

## Verification and reporting

Read the stored state independently after each actor finishes. Do not grade from
its final answer alone. Inspect tool errors inside otherwise successful tool
responses. Function execution proves the function, not its attachment captures;
stored topology proves configuration, not conversational behavior. Mark each
kind of evidence explicitly. Run conversation checks only after confirming that
the relevant tools are pure and confined to the synthetic task.

Compile the intended draft before starting a fresh conversation. Record whether
the actor or verifier performed this prerequisite. A conversation using an old
compiled draft is an invalid check of the newly saved configuration; preserve
that failed attempt as a harness finding, then test the correct draft state.

Bound every request and actor run. A timed-out mutation is ambiguous: inspect
before retrying. In CLI 0.287.0 and 0.335.0, JSON output with `--timeout` can be
empty despite exit zero. An independent verifier can retain JSON by bounding
the subprocess instead. Preserve the raw output-format distinction in evidence;
do not treat a blank body as an empty account or successful validation.

Record completed, partial, blocked, failed, and unrun outcomes separately, along
with actual tool calls, errors, durations, and remaining runtime gaps. Confirm
release lists and traffic remain unchanged. Keep OAuth URLs, credentials,
account identity, and customer data out of committed results. Leave test
resources for inspection; cleanup requires authorization for that deletion.
