# Sources and adaptation

Reviewed 2026-10-16.

## Product knowledge

The Voiceflow website documentation is the product authority. The initial audit
used the website's current docs for CLI, MCP, playbooks, workflows, function/API
tools, references, secrets, knowledge, transcripts, evaluations, tests, and
environments. Each specialist skill links its relevant public documentation.

The current Creator skill library was reviewed at revision
`811c78c61b6c50df69922bf686de12c5779a2cdf`. Its thirteen customer-facing
specialties informed the portable workflows. The internal coach skill was
excluded. Private helper calls, implicit in-app page context, UI suggestion
protocols, and internal tooling dependencies were removed. These are concise
new customer-facing instructions, not a vendored copy of private source files.

Where an older skill conflicted with current website documentation, the website
won. Where command examples lagged the released CLI, the actual executable's
help and schemas determined command syntax. The release baseline is 0.287.0.
No old product-hub content was used.

The request-shape reference added in 0.2.1 comes from authorized live tests of
the public CLI and hosted account MCP, including read-back and conversation
verification. It contains synthetic examples, not private implementation code
or customer resource IDs. The [live acceptance report](../evals/reports/2026-10-16-live-product.md)
records the baseline, corrections, retests, and remaining limits.

Version 0.2.2 adds explicit global-identity read/write fields and draft-conversation
request shapes from further public CLI/MCP use. Its collection and handoff guidance
responds to observed runtime failures in unfamiliar synthetic tasks. The
[quality protocol](../evals/quality-product-protocol.md) separates the initial
frozen runs, targeted retests, and independent conversation checks. No private
implementation code or real customer content was used in these additions.
The [quality report](../evals/reports/2026-10-16-quality-product.md) records the
observations and distinguishes initial runs from post-failure retests.

Version 0.3.0 adds the portable widget skill and eight platform guides. Product
behavior comes from the website's Install widget, Customize widget, Widget API,
and Extensions pages; platform insertion/lifecycle guidance was checked against
the official Webflow, Framer, WordPress, Shopify, Wix, Squarespace, React, Next.js,
and Astro documentation on 2026-10-16. Links are included in each guide. Interface
labels and plan eligibility should be rechecked when an account differs.

The widget CLI examples were exercised with the released 0.287.0 binary against
a localhost fixture: draft-settings read, published/draft snippet selection, and
a minimal JSON patch supplied on stdin. The fixture verifies HTTP paths, query
parameters, request body, and output handling; it does not verify server-side
entitlements, live widget rendering, or a hosted MCP call. MCP operation names
were checked against the current tool surface, with payload discovery delegated
to the connected schema. No customer project or website was changed for these
repository checks. The [widget acceptance protocol](../evals/widget-protocol.md)
records the next behavioral and live-platform checks; they are not claimed as
passed by the unit suite.

## Creator skill sync

Later changes to the Creator skill library are adapted by a scheduled sync.
Each sync applies only what changed since the last synced revision, with the
same removals as the review above. Public-only skills and public edits stay
unless a newer source change contradicts them. The last sync covered revision
`da3aa8b2a244987908dfbac77182f5c19a0ba2a3` from 2026-10-28;
[creator-sync.json](creator-sync.json) holds the sync state.

## Packaging references

- [Agent Plugins specification](https://agent-plugins.org/)
- [OpenAI plugin authoring](https://developers.openai.com/plugins/build/plugins)
- [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference)
- [Claude marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Cursor plugin reference](https://cursor.com/docs/reference/plugins)
- [Cursor skills](https://cursor.com/docs/skills)

Host formats are thin adapters around the same skill tree. No automatic
permission-granting hooks are included.

## CLI supply chain

The native installers use assets from the public Voiceflow CLI v0.287.0 release.
All six SHA-256 values are pinned in the skill bundle, rather than trusting an
unversioned latest installer. The binary remains a separately distributed
Voiceflow component under its own licensing; it is not included in this repo
or its plugin archive.

## Docs MCP integration (0.4.0)

Every skill now routes unresolved product/how-to questions to the shared docs
workflow. Setup treats the public Knowledge MCP as a standard companion to CLI
or account MCP, with verified public-docs fallbacks where unsupported. Portable
`mcp.json` and the native `.mcp.json` adapter bundle only this public server;
account OAuth remains capability-based setup, not a packaged credential.

The [current Knowledge MCP documentation](https://www.voiceflow.com/docs/mcp/knowledge)
and a read-only live probe on 2026-10-16 verified the endpoint, no-auth access,
four tool names, and required context arguments. Server version 2.1.2 returned
a low-confidence, non-answerable result for an embedded-widget question;
`read_voiceflow_page` then retrieved the Widget API page with its embedded
rendering options. The shared workflow explicitly handles that distinction.
These probes establish retrieval, not model adherence or site implementation.

## Docs attribution and troubleshooting (0.4.1)

Every new Voiceflow troubleshooting issue now consults the docs MCP even when
a skill suggests a fix. Useful requests carry package version, active skill,
and setup/troubleshooting/usage context in the existing `why` field. Metadata
lives in the shared workflow so standalone and native installs carry it without
an extra read. No separate telemetry service or progress-reporting call is added.

Fresh low-reasoning Luna and Sol evaluations exposed skipped reads of an earlier
separate version file. The final inline metadata design passed all eight focused
attribution/consultation checks; the original failures remain in the
[report](../evals/reports/2026-10-16-docs-attribution.md). Live public docs were used;
account state was synthetic, with no customer mutation or new authentication.

## Public distribution preparation (0.4.2)

The copyright holder and package author metadata are Voiceflow, Inc. Each skill
now carries the same MIT notice as the root package, including standalone copies.
Support and security contacts were verified against Voiceflow's public docs and
security page on 2026-10-16. Public-facing data guidance points to the existing
Voiceflow privacy policy and service terms; it does not create a new policy.
Release tooling prepares verified archives and an optional unpublished draft;
publication, transfer, and website deployment remain separate steps.
