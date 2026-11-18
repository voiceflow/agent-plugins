# Website publishing contract

The repository owns the setup content. The Voiceflow website publishes it.
There is no second hand-maintained setup guide and no runtime dependency on a
private GitHub fetch.

## Build and consume

Run `python3 scripts/build.py` from a clean, approved commit. The generated
`dist/site/agents/` directory contains:

- `setup.md`: the canonical guide, with local Markdown links rewritten for web use.
- The guide routes by available capabilities; chat assistants read individual
  Markdown files without downloading the plugin archive. CLI and hosted MCP
  procedures are linked references in the same versioned payload.
- `voiceflow/`: the complete plugin and all linked skills and references, including
  the pinned CLI version and checksums.
- `voiceflow.zip`: the same plugin in a reproducible archive.
- `manifest.json`: version, source commit, dirty status, per-file hashes, and a
  content digest. The archive hash is `files["voiceflow.zip"]`.

Copy that directory into the website's static public directory as `agents/`.
The intended canonical address is `https://www.voiceflow.com/agents/setup.md`.
This repository prepares that payload; it does not deploy or claim that URL is
live. Deployment belongs to a later website change.

Serve Markdown as UTF-8 text/markdown, JSON as application/json, and ZIP as
application/zip. Avoid login walls, HTML wrappers, or client-side rendering.
Preserve relative paths. Do not serve a human documentation template at the raw
Markdown URL.

Deploy the entire directory atomically. Use revalidation for the canonical
setup guide and manifest; retain immutable snapshots under a versioned path
if the website supports them. Do not update a manifest before its archive.

## Website integration gate

1. Consume an approved commit's CI artifact, not an unreviewed branch or latest
   moving release. Reject `hasUncommittedChanges: true`.
2. Validate every file hash and confirm the manifest's sourceCommit is the
   intended approved revision. The manifest is provenance, not a signature.
3. Deploy all files together and fetch the public setup, linked skill, manifest,
   and archive from a fresh unauthenticated session.
4. Test the one-prompt journey in each supported coding and chat client and a new
   conversation. Verify chat hosts can fetch linked Markdown and connect remote
   MCP; do not treat offline fixtures as live client compatibility evidence.
5. Only then update the CTA's copied prompt to:
   “Set up Voiceflow by following https://www.voiceflow.com/agents/setup.md”.
6. Keep the previous bundle for an atomic rollback. A rollback does not
   automatically downgrade plugins already installed by customers.

Before public publication, promote the approved implementation and verify the
stable public source. The canonical guide works from the supplied revision;
keep the whole bundle together so its relative references and license notices
resolve. The rest of the install and verification flow remains shared.
