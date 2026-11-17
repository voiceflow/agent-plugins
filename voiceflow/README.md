# Voiceflow

This plugin connects your AI assistant to your Voiceflow account. It then helps
you build, test, debug, and improve Voiceflow agents. It works in Claude Code,
Codex, Cursor, and chat assistants that can connect remote MCP servers.

## What it includes

- Eighteen skills. They cover setup, agent building, prompts and playbooks,
  workflows, functions, integrations, knowledge bases, messages, voice, phone
  numbers, the web chat widget, debugging, transcripts, evaluations, and
  environments.
- A connection to the public Voiceflow docs server. The assistant uses it to
  look up current product guidance before it answers or changes anything.

## Install

In Claude Code 2.1.275 or later, run:

```text
/plugin install voiceflow --marketplace voiceflow/agent-plugins
```

For Codex, Cursor, other Claude Code versions, and standalone skills, follow
the [client guide](skills/voiceflow-setup/references/clients.md).

## How setup works

Ask your assistant to connect you to Voiceflow. The `voiceflow-setup` skill
checks what your assistant can do, then takes one of two paths.

- **An assistant with a terminal** uses the Voiceflow CLI. If the CLI is
  missing, setup can download version 0.287.0 from the official release at
  [github.com/voiceflow/cli](https://github.com/voiceflow/cli/releases). Before
  it installs anything, it checks the download against SHA-256 checksums pinned
  in this plugin. It never replaces a CLI that is already installed. You then
  sign in through your browser.
- **An assistant with remote MCP** connects the hosted Voiceflow MCP server.
  You sign in through your browser.

Setup is done when one account read works and one docs question gets an answer.
Setup does not create a project or publish anything. After that, the assistant
asks what you want to build or improve.

If you ask for a standalone install, a setup script copies the skills into your
assistant's skills folder. It records the files it manages and refuses to
overwrite files you have edited.

## Data and services

- **Voiceflow MCP server**, `https://mcp.voiceflow.com/mcp?version=3`. It uses
  OAuth and asks for workspace read and write access. Setup only reads. Later changes
  follow your requests and your assistant's approval prompts.
- **Voiceflow docs MCP**, `https://www.voiceflow.com/docs/mcp?logging=off`. This
  plugin bundles it. It is public and needs no sign-in. Each docs request sends
  your question. The skills tell the assistant to keep credentials, customer
  data, and private code out of every question.

  With `logging=off`, the docs server writes one anonymous count line per call.
  The line holds the tool name, a `logging: off` marker, the caller label
  `public`, the error code, the duration, and a cold-start flag. It does not
  hold your question, search terms, client name, or session. Vercel, which hosts the docs, still logs each request's URL, IP
  address, user agent, status, and timing, but not the question.

  A docs connection you added by hand without `logging=off` is logged as
  before. On that connection each request also carries a short tag with the
  plugin version, the active skill, and the stage: setup, troubleshooting, or
  usage.
- **Voiceflow CLI**, downloaded as described above. It runs on your machine and
  keeps its own sign-in.

The plugin stores no credentials and sends no separate analytics. Your
assistant provider has its own data policies.

## Links

- License: [MIT](LICENSE), copyright Voiceflow, Inc.
- Support: [help and support](https://github.com/voiceflow/agent-plugins/blob/main/SUPPORT.md)
- Privacy: [Voiceflow Privacy Policy](https://www.voiceflow.com/privacy)
- Terms: [Voiceflow Terms of Service](https://www.voiceflow.com/legal/terms)
- Source: [voiceflow/agent-plugins](https://github.com/voiceflow/agent-plugins)
- Product docs: [Voiceflow documentation](https://www.voiceflow.com/docs)
