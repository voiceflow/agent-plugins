# Changelog

Package versions are independent of the Voiceflow CLI version. This file records
changes; an entry is not proof that a GitHub release or marketplace listing exists.

## 1.2.0

This guidance needs voiceflow/creator-app#24625 deployed on the account MCP.
Until it is, the dynamic URL below serves the full tool list without the two
caller tools, as the plain URL does.

- Codex, Cursor, and GitHub Copilot now connect the account MCP at
  `https://mcp.voiceflow.com/mcp?version=3&dynamic=true`. These hosts cap or
  trim long tool lists. In Codex, the full list hid tools such as
  `vf_project_list`. This URL lists about a dozen tools. Claude Code, Claude, ChatGPT, and other
  hosts keep `https://mcp.voiceflow.com/mcp?version=3`. On Codex, Cursor, or
  GitHub Copilot, setup changes a saved URL that lacks `dynamic=true`.
- The skills reach an operation that is not in the tool list in three steps.
  They find it with `vf_search_operations`, read its schema with
  `vf_describe_operations`, then run it with `vf_call_read_operation` or
  `vf_call_write_operation`. A listed tool is still called directly. A write
  through the caller follows the same draft and approval rules as a direct
  call.
- When the docs MCP is not connected, as in a host with only the account MCP,
  the skills use the account MCP's docs tools, such as `vf_docs_ask`. The data
  notes say what those calls send to the docs server.
- The reference checks accept the new tool names. Validation accepts only the
  two account MCP URLs, and fails when a line gives a host the other one.
- Two new acceptance cases: `setup-mcp-dynamic-host` and
  `dynamic-operation-by-name`. The two version-repair cases now expect the
  dynamic URL in Codex, Cursor, and GitHub Copilot.

## 1.1.1

- Removed: the standalone skill installer, `install_skills.py`. Hosts now
  install the plugin through their own plugin systems. Claude Code, Codex, and
  GitHub Copilot CLI use their plugin commands, and Cursor uses a team
  marketplace. A host without a plugin system installs the skills with
  skills.sh, `npx skills add voiceflow/agent-plugins`, which needs Node.js.
  Add `--skill <name>` to install one skill.
- If you used the installer, its skill folders and its `.voiceflow-skills.json`
  receipt stay where it put them, and nothing updates them. Look in
  `~/.claude/skills/` (or `$CLAUDE_CONFIG_DIR/skills/`), `~/.codex/skills/`
  (or `$CODEX_HOME/skills/`), `~/.cursor/skills/`, or the folder you passed
  with `--target`. The receipt sits in that folder and lists every file the
  installer copied. To move, keep a copy of any skill you edited. Then delete
  the `voiceflow` and `voiceflow-*` folders the receipt lists, and the receipt.
  Then install through the host's plugin system or skills.sh.
- Each skill now works when it is installed alone. Before, most skills linked
  files in other skill folders. A single-skill install, such as
  `npx skills add voiceflow/agent-plugins --skill <name>`, copies one folder, so
  those links broke. GitHub's awesome-copilot marketplace lint rejects such
  links for the same reason.
- Skills now name each other, such as "the `voiceflow-wiring` skill", instead
  of linking to each other's files. If a named skill is not installed, the
  assistant says so and uses the documentation workflow.
- The shared references, such as the operation contract and the docs workflow,
  still have one source in the `voiceflow` skill. A script copies each one
  into every skill that links it, and validation fails when a copy differs
  from its source. Each copy carries the package version, so a single-skill
  install reports the real version in docs requests.
- The setup guide keeps one link to the entry skill, because chat assistants
  that read the guide from the website follow it to find the skills.
- Port the latest Atlas product guidance into ten skills: build, debug,
  environments, evaluations, functions, integrations, messages,
  optimize-playbooks, voice, and workflows. Debugging now covers duplicate
  replies after a model fallback. Seven new acceptance cases cover these
  changes.

## 1.1.0

- Connect the docs MCP with `logging=off` in every native plugin and standalone
  setup. With this option, the docs server writes one anonymous count line per
  call and does not log the question, search terms, or client details. A docs
  connection the user added by hand is logged as before. This requires
  voiceflow/voiceflow-website#617 to be deployed on the docs server.
- Leave the docs `why` field out when the tool marks it optional, as it does
  with `logging=off`. When a tool still requires it, send only the package,
  skill, and stage tag, with no task, symptom, or setup-state sentence.
- Add a plugin README that explains setup, the services the plugin contacts,
  and what each one receives. Anthropic's directory shows it as the listing.
- Add directory listing metadata: display name, links, keywords, the
  `Developer Tools` category, starter prompts, and `voiceflow-setup` as the
  onboarding skill. Add the Voiceflow listing icon.
- Add `skills.sh.json` so `npx skills add voiceflow/agent-plugins` finds every
  skill under `voiceflow/skills`.
- Add MCP Registry entries for the account and docs servers. They are not
  published.

## 1.0.0

Breaking: the skills now name the account MCP v3 tools. The account MCP URL is
pinned to `https://mcp.voiceflow.com/mcp?version=3`. To migrate, change a saved
account MCP connection to that URL, then reload the host's tools.

- Name every account MCP tool by its v3 name, `vf_<group>_<operation>`, such as
  `vf_agent_get`, in place of `voiceflow_<group>.<operation>`. Request examples
  put path and query fields at the top level and the write body in `body`.
- Pin the account MCP URL to `https://mcp.voiceflow.com/mcp?version=3`. Setup
  repairs a saved connection that has no version or another version. The plugin
  pins the MCP surface it was written for, so each plugin release pairs with one
  MCP server version. The server default can move to a later version without
  breaking installed plugins. A later plugin release moves the pin.
- Refuse a `vf_*` name that v3 does not serve, and every older
  `voiceflow_<group>` name, in the skill reference checks.
- Add the Optimize playbooks skill: condense long instructions, or move a job
  out of the main agent's instructions, with tests before and after.
- Port the latest product guidance: workflow tools sit on the main agent,
  playbook exit paths hold message IDs, transcripts are read in the summary
  view first, and an evaluation run scores one transcript per call.

## 0.5.0

- Pin the account MCP URL to `https://mcp.voiceflow.com/mcp?version=2`, because the server default is moving to the new v3 tool names. The next major release moves the skills to v3.

## 0.4.2

- Update package and support links for the transfer to `voiceflow/agent-plugins`.
- Attribute the MIT license and package authorship to Voiceflow, Inc.
- Include the license in every standalone skill, native package, and website bundle.
- Add public support, security reporting, contribution, and conduct guidance.
- Explain docs MCP logging, account permissions, and service/license boundaries.
- Summarize current compatibility separately from historical evidence.
- Prepare versioned release archives, checksums, release notes, and a draft-release workflow.
- Gate CI and release assets on secret scanning; test detection with synthetic canaries.
- Restrict package contents to a reviewed inventory and isolate release publishing permissions.
- Add Claude contributor instructions, security check guidance, and Actions dependency updates.
- Require releases to originate from the protected default branch and reject unmerged source commits.
- Reject incomplete account responses and bound JSON connection checks outside the CLI.
- Verify effective branch review/check requirements before preparing releases.
- Add isolated adversarial safety evaluations and recorded behavioral evidence.
- Align release verification with the owner's sole-maintainer policy while requiring PRs and all security/platform checks.

## 0.4.1 — 2026-10-16 (development milestone)

- Consult docs MCP for every new troubleshooting issue.
- Attribute useful docs requests to package version, skill, and task stage.
- Add focused low-reasoning evaluations and measurement guidance.

## 0.4.0 — 2026-10-16 (development milestone)

- Integrate the public docs MCP throughout all sixteen skills and native packages.
- Add documentation connection, verification, and fallback guidance.

## 0.3.0 — 2026-10-16 (development milestone)

- Add widget customization and installation guidance for eight website platforms.
- Add widget CLI contract fixtures and acceptance specifications.

## 0.2.2 — 2026-10-16 (development milestone)

- Improve collection, identity, and handoff workflows from live regression evidence.

## 0.2.1 — 2026-10-16 (development milestone)

- Harden product workflows and request shapes using live acceptance evidence.

## 0.2.0 — 2026-10-16 (development milestone)

- Add capability-based onboarding for chat assistants and an offline setup harness.

## 0.1.0 — 2026-10-16 (development milestone)

- Introduce the shared setup guide, portable skills, native adapters, verified CLI
  installers, reproducible website bundle, and cross-platform checks.
