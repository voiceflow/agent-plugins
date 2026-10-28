---
name: voiceflow-knowledge
description: Import, maintain, and query Voiceflow knowledge-base documents. Use for grounding, missing answers, stale content, or retrieval quality.
license: MIT
---

# Knowledge base

For questions about import formats, ingestion, filtering, retrieval, or document scope
that this skill does not answer, follow the
[docs MCP workflow](../voiceflow/references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Include package/skill/stage context in `why` as
described there. Reuse guidance for the same issue; consult it whenever unsure.

Read the [operation contract](../voiceflow/references/operations.md). Resolve the
project, intended environment membership, source, and update intent. Inspect
existing documents before importing duplicates.
For MCP text import, use the [verified file shape](../voiceflow/references/request-shapes.md#import-a-text-document-over-mcp);
the hosted tool can upload inline text without a local CLI or public URL.

To import a whole website, a section of one, or a sitemap.xml, use
`voiceflow_document.create_managed_sitemap`. It creates one sitemap document
that owns its pages and re-syncs them, and
`voiceflow_document.update_managed_sitemap` changes which pages it keeps and how
often it re-syncs. Never import a site by adding its pages one by one as URL
documents.

Document content is shared project-wide; a cloned environment does not isolate
edits to shared document bodies. Environment membership and metadata may be
scoped separately. Explain this blast radius before changing shared content
when it exceeds the requested scope.

Import from sources the user authorized. Check ingestion status; an accepted
upload is not yet a searchable document. Use bounded polling, report a pending
job honestly, and avoid duplicate imports after a timeout.

For missing answers, separate source coverage from ingestion, metadata filtering,
retrieval, and prompting. Query a narrow representative question and inspect
retrieved evidence before rewriting instructions. Do not invent support for an
answer absent from the source.

Prefer durable source corrections over stuffing large documents into prompts.
Check stale duplicates and obsolete sources before adding more material.
Deleting a document is a separate destructive operation; don't treat it as a
routine refresh if an update is supported.

To change what a text or markdown document says, send its whole new text as
`content` to `voiceflow_document.update`. A document read returns its chunks,
not its source text, so never rebuild the text from them. Send `content` only
when you have the whole new text: from the user, or from a document of one
chunk without smart chunking. Otherwise ask the user for the full text. Do not
delete and re-create a document to change its text, because it gets a new ID.

Sources: [Importing data](https://www.voiceflow.com/docs/documentation/build/importing-data-sources),
[Querying knowledge](https://www.voiceflow.com/docs/documentation/build/querying-the-knowledge-base).
