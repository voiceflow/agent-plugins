# Voiceflow for AI assistants

Connect Voiceflow. Tell your assistant what you want to build.

A shared setup guide and sixteen skills help coding agents and chat assistants
build, customize, test, and improve Voiceflow agents. Setup chooses the connection
that works in your current app, reuses existing access, and asks you to complete
browser sign-in only when needed.

**Status: beta.** Maintained in the [Voiceflow organization](https://github.com/voiceflow/agent-plugins).
Use the default branch for the development preview. There is no published
marketplace listing or website setup URL yet.
See [compatibility](docs/compatibility.md) for tested and experimental paths.

## Get started

Give your assistant this prompt together with this repository or checkout:

> Follow this repository's setup guide at
> voiceflow/skills/voiceflow-setup/references/setup.md to connect me to Voiceflow.
> Complete setup where you can, then ask what I would like to build or improve.

[Open the setup guide](voiceflow/skills/voiceflow-setup/references/setup.md).
You need a Voiceflow account (you can create one during browser sign-in) and
an assistant with either a persistent local terminal or a host that supports
remote MCP with OAuth. An assistant with only web access can guide you, but
cannot operate your account. Never paste passwords or tokens into the chat.

Setup verifies a read of your account and access to product guidance. It does
not create a project or publish anything. When ready, your assistant asks:

> You're connected to Voiceflow. What would you like to build or improve?

Skill persistence depends on the host. A connected conversation does not imply
that every future conversation has inherited the skills.

## What can I ask it to do?

- “Build a support agent that answers from our help center and hands off when needed.”
- “Add the chat widget to my Shopify theme and help me customize its appearance.”
- “Investigate why my agent answers twice after a playbook finishes.”
- “Create evaluations for our refund flow and explain what needs improvement.”

These are example requests, not claims that every platform has passed live
acceptance. Later account changes follow your request and normal host approvals.

## Installation and supported paths

| Your assistant can… | Setup uses… |
| --- | --- |
| Run tools in your persistent local environment | Voiceflow CLI and browser OAuth; native plugins or standalone skills |
| Connect remote MCP servers | Voiceflow account MCP and browser OAuth; readable skills in the current conversation |
| Only read web pages | Guided setup instructions; no claim of account access |

The public **Voiceflow Knowledge MCP** supplies current product documentation
without sign-in alongside either account connection. The assistant consults it
for unresolved how-tos and every new troubleshooting issue.

For manual installation, updates, and removal, use the
[client guide](voiceflow/skills/voiceflow-setup/references/clients.md).
[Compatibility](docs/compatibility.md) separates package installation, model
behavior, and real client onboarding. Cursor and live widget-platform paths
remain experimental.

## Skills and guides

The [skill index](voiceflow/skills/voiceflow/SKILL.md) covers setup, building,
prompts, workflows, functions, integrations, knowledge, messages, voice,
widgets, debugging, transcripts, evaluations, environments, and wiring.

The [widget guide](voiceflow/skills/voiceflow-widget/SKILL.md) covers Webflow,
Framer, WordPress, Shopify, Wix, Squarespace, HTML/Astro, and React/Next.js.
Product knowledge comes from the [Voiceflow documentation](https://www.voiceflow.com/docs).

## Data, permissions, and services

Account access uses Voiceflow's CLI or hosted MCP OAuth. The hosted account MCP
requests workspace read and write access; setup itself only reads.
Documentation questions go to Voiceflow's public docs MCP and can be logged with
package version, skill, task stage, and client/session context to improve docs
and onboarding. Skills instruct assistants to omit secrets and customer data.
See [data and services](voiceflow/skills/voiceflow/references/data-and-services.md)
and the [Voiceflow Privacy Policy](https://www.voiceflow.com/privacy).

This repository's MIT license covers its instructions and utilities. It does
not make Voiceflow's hosted service or separately distributed CLI open source,
free of charge, or exempt from their applicable terms and plan limits.

## Help and contribute

- [Support and bug reports](SUPPORT.md)
- [Report a vulnerability privately](SECURITY.md)
- [Contribute](CONTRIBUTING.md) · [Code of conduct](CODE_OF_CONDUCT.md)
- [Changelog](CHANGELOG.md) · [Release and maintenance policy](docs/releasing.md)
- [Acceptance evidence](evals/README.md) · [Onboarding measurement](docs/measurement.md)
- [Source provenance](docs/provenance.md) · [Website publishing](docs/website-publishing.md)

For local checks, install Python 3.10+; no Python packages or Voiceflow account
are required:

```sh
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 scripts/build.py
```

Generated files go to `dist/`. See [contributing](CONTRIBUTING.md) for the full
workflow and the separate, opt-in host and live acceptance checks.

## License

[MIT](LICENSE). Copyright (c) 2026 Voiceflow, Inc.
The full plugin and each standalone skill include the license notice.
