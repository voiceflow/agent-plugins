# Persist skills in the current client

Use one method, for the current host only. A host with a plugin system installs
the Voiceflow plugin, which brings every skill and the docs MCP. A host without
one installs the skills alone with skills.sh. These are standalone skills.
Do not install both in the same host, because the host then sees each skill twice.

The plugin source is this repository: `voiceflow/agent-plugins` on GitHub, or a
checkout in a stable user-owned directory. A marketplace added from a checkout
keeps pointing at it, so the checkout must stay in place. To use a checkout,
replace `voiceflow/agent-plugins` in the commands below with its absolute path.
The website bundle's `voiceflow.zip` holds the plugin folder but no marketplace
file, so install from GitHub or a checkout instead.

Before installing, look in the host's user skills folder for existing
`voiceflow` and `voiceflow-*` folders. Folders left by the retired installer are
covered in [updates and removal](#updates-and-removal).

## Claude Code

```sh
claude plugin marketplace add voiceflow/agent-plugins --scope user
claude plugin install voiceflow@voiceflow-plugins --scope user
claude plugin list
```

Check `claude plugin marketplace list` first and reuse a matching source. Do not
replace an unrelated marketplace with the same name. In a session, Claude Code
2.1.275 or later can also run
`/plugin install voiceflow --marketplace voiceflow/agent-plugins`.

## Codex

```sh
codex plugin marketplace add voiceflow/agent-plugins
codex plugin add voiceflow@voiceflow-plugins
codex plugin list
```

Check `codex plugin marketplace list` first; reuse a matching source. Start a
new session before using the skills. Older versions without these commands use
skills.sh. Do not bypass the host's installation policy or change trust settings.

## GitHub Copilot CLI

```sh
copilot plugin marketplace add voiceflow/agent-plugins
copilot plugin install voiceflow@voiceflow-plugins
copilot plugin list
```

Check `copilot plugin marketplace list` first; reuse a matching source.
Copilot CLI reads this repository's Claude marketplace file, so the marketplace
name is the same.

## Cursor

Voiceflow is not listed in the Cursor Marketplace. On a Cursor Teams or
Enterprise plan, an admin can import this repository as a team marketplace:
**Dashboard > Plugins & MCPs > Add Marketplace > Import from Repo**. Members
then install Voiceflow from **Customize** in the sidebar. Without a team
marketplace, use skills.sh with the agent name `cursor`.

## Other hosts: skills.sh

Use skills.sh for a host without a plugin system, or a host version too old for
the commands above. It needs Node.js 22.20 or later, because it runs through
`npx`. Ask before installing Node.js. Install for the current host only, in the
user's skills folder:

```sh
npx skills add voiceflow/agent-plugins --skill '*' -g -a cursor -y
```

Replace `cursor` with the current host's skills.sh agent name, such as
`github-copilot`, `claude-code`, or `codex`. Without `-g`, the skills go into
the current project instead. To install one skill, give its name in place of
`'*'`, such as `--skill voiceflow-widget`; each skill works alone. skills.sh is
a third-party tool. It sends anonymous usage data unless `DISABLE_TELEMETRY=1`
or `DO_NOT_TRACK=1` is set.

If the host has no plugin system and Node.js is not available, read the skills
from the checkout in this conversation. Tell the user that future chats need the
plugin or skills.sh.

Verify the entry skill and references exist and check the host's skill/plugin
inventory when available. Reading a file does not prove automatic discovery.
Load the entry skill directly now if needed; tell the user if a reload is needed
for future native discovery. Do not install into every agent on the machine.

## Docs MCP for standalone skills

Native plugin packages include the public Voiceflow Knowledge MCP configuration.
After installation, discover and verify its tools; host approval or reload may
still be needed. skills.sh installs only the skills, not server configuration.

For standalone installs, inspect existing connections first. Reuse a connection
to the Voiceflow docs server that the user already added. If there is none, add
it with the URL below, using the current host's supported MCP setup. The URL
ends in `logging=off`, so the docs server keeps only anonymous counts for it.
Keep the URL in quotes in a shell, because `?` is a wildcard in some shells.

- Claude Code: `claude mcp add --transport http --scope user voiceflow-knowledge "https://www.voiceflow.com/docs/mcp?logging=off"`.
- Codex: `codex mcp add voiceflow-knowledge --url "https://www.voiceflow.com/docs/mcp?logging=off"`.
- Cursor: add a `voiceflow-knowledge` entry with
  `{"url":"https://www.voiceflow.com/docs/mcp?logging=off"}` to `mcpServers` in its current
  user/project MCP settings. Merge with existing configuration, preserving other
  entries. A different server already using that name is not safe to replace.

Check installed command help before use; older hosts can differ. Configure only
the current client and intended scope. No sign-in or token is needed. Follow
[docs verification](mcp.md#documentation-connection); a restart requirement is
not proof that tools are callable in this conversation.

## Updates and removal

Update and remove plugins through the host, and check its current help first:

- Claude Code: `claude plugin update voiceflow@voiceflow-plugins`, and
  `claude plugin uninstall voiceflow@voiceflow-plugins`.
- GitHub Copilot CLI: `copilot plugin update voiceflow`, and
  `copilot plugin uninstall voiceflow`.
- Codex: `codex plugin remove voiceflow@voiceflow-plugins`. For updates, check
  `codex plugin --help` or the `/plugins` browser.
- Cursor: **Customize** in the sidebar.

For skills.sh, `npx skills check` lists available updates. For project installs
it also lists skills with local changes. `npx skills update` installs updates,
and `npx skills remove` removes skills. Add `-g` for user-folder installs.
An update can replace the user's edits. Before updating, compare the installed
files with the source, keep a copy of each edited file, and tell the user.
Removal does not revoke Voiceflow OAuth access or remove the CLI.

### Skills from the retired installer

Package versions before 1.1.1 included `install_skills.py`, which copied the
skills into a user skills folder. Version 1.1.1 removes it. The folders it
copied and its `.voiceflow-skills.json` receipt stay where it put them, and
nothing updates them. Unless `--target` named another folder, it used:

| Client | Folder |
| --- | --- |
| Claude Code | `$CLAUDE_CONFIG_DIR/skills/`, otherwise `~/.claude/skills/` |
| Codex | `$CODEX_HOME/skills/`, otherwise `~/.codex/skills/` |
| Cursor | `~/.cursor/skills/` |

The receipt sits in that folder. Its `files` list holds each file the installer
copied, as a path that starts with the skill folder name, `voiceflow` or
`voiceflow-<name>`. Each file's value is its SHA-256 at install time, so a
different hash means the user edited that file. To move to the plugin or
skills.sh, keep a copy of each edited file, then delete those skill folders and
the receipt. Then install with one method above.
