---
name: voiceflow-widget
description: Customize, install, and troubleshoot the Voiceflow chat or voice widget on websites. Use for embedding agents, matching a site's brand, website launchers, and browser integration.
license: MIT
---

# Put a Voiceflow agent on a website

For questions about widget options, styling, browser APIs, installation, or troubleshooting
that this skill does not answer, follow the
[docs MCP workflow](../voiceflow/references/documentation.md) before answering
or implementing. For every new Voiceflow troubleshooting issue, consult it even
when this skill suggests a fix. Leave `why` out when it is optional; otherwise
send only the package/skill/stage tag described there. Reuse guidance for the
same issue; consult it whenever unsure.

Read the [operation contract](../voiceflow/references/operations.md). Finish with
the requested widget working on the intended site, or an exact installation
handoff and a clear statement of what remains unverified. This skill covers
the website widget, including its voice mode; phone numbers are a separate task.

## Resolve only what is missing

Use the user's request, site source, and live Voiceflow reads to identify:

- The project and intended environment/version.
- The website URL/platform and available edit access.
- Site-wide versus selected pages, and floating versus embedded placement.
- The requested appearance or behavior. Reuse the site's brand when asked to
  match it; do not make the user complete a design questionnaire.

Do not make someone repeat choices already supplied. If the target project is
ambiguous, ask before writing. For a simple new install, propose the existing
published widget as a floating launcher; keep customization optional.

## Use the access this assistant has

| Available access | What to do |
| --- | --- |
| Voiceflow CLI or account MCP, plus site editing | Read/configure the widget, get its snippet, implement it in the site's normal workflow, and verify in a browser. |
| Voiceflow CLI or account MCP only | Do the Voiceflow work, supply the returned snippet and the relevant platform steps, then help verify the result. |
| Site access and a user-supplied snippet | Inspect and install that snippet; preserve its targeting. Explain if remote settings cannot be verified. |
| Guidance only | Guide the user to Voiceflow's Widget tab and their platform's insertion point. Do not invent a project ID or claim account access. |

An account MCP connection manages Voiceflow, not the website. Do not ask a
chat-only user to install a terminal when MCP can do the Voiceflow portion.
For missing Voiceflow access, use [setup](../voiceflow-setup/SKILL.md).

## Configure, install, verify

1. Read [tools and targeting](references/tools.md) before any widget operation.
   Inspect existing settings and site installs. Reuse one installation owner;
   a second script can create duplicate launchers or reset conversations.
2. For changes to branding, layout, behavior, identity, or custom CSS, read
   [customization](references/customization.md). Keep remote widget settings
   separate from browser `chat.load()` options: their shapes differ.
3. Get the generated snippet for the intended target. Read
   [installation and verification](references/installation.md), then **only the
   relevant platform guide** below. Preserve generated verification and runtime
   fields; do not replace them with a generic snippet from memory.
4. Complete authorized edits and test the intended pages. Widget settings,
   Voiceflow publishing, and website deployment are distinct steps. A request
   for a draft or preview must not publish either system. Existing authorization
   to launch should be honored without asking again.
5. If it fails, use [troubleshooting](references/troubleshooting.md) to isolate
   the stage before changing settings, credentials, or agent instructions.

## Platform guides

| Site | Guide |
| --- | --- |
| Plain HTML, static sites, Astro | [HTML and Astro](references/html-astro.md) |
| React, Next.js, other client-routed apps | [React and Next.js](references/react-nextjs.md) |
| Webflow | [Webflow](references/webflow.md) |
| Framer | [Framer](references/framer.md) |
| WordPress, including WordPress.com | [WordPress](references/wordpress.md) |
| Shopify storefront | [Shopify](references/shopify.md) |
| Wix | [Wix](references/wix.md) |
| Squarespace | [Squarespace](references/squarespace.md) |

For another platform, apply the shared installation contract and check that
platform's official custom-code documentation. Do not guess menu locations or
promise a native Voiceflow plugin exists.

## Completion

Report the site/pages and Voiceflow target, what was changed, and what was
actually checked. Distinguish **prepared**, **installed in preview**, and
**verified live**. Name the specific remaining step if access or publishing is
pending. Give the user the one place to edit/remove this installation later.

Sources: [Install widget](https://www.voiceflow.com/docs/documentation/deploy/widget/embedding-the-chat-widget),
[Customize widget](https://www.voiceflow.com/docs/documentation/deploy/widget/custom-web-chat-styling),
[Widget API](https://www.voiceflow.com/docs/documentation/deploy/widget/web-chat-api).
