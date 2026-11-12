# Changelog

Package versions are independent of the Voiceflow CLI version. This file records
changes; an entry is not proof that a GitHub release or marketplace listing exists.
Add each customer-facing change under Unreleased. When the release workflow
releases a version, it moves those lines under that version number.

## Unreleased

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
