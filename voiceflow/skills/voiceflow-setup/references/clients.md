# Persist skills in the current client

Use one method. Keep the checkout or extracted bundle in a stable user-owned
directory; native local marketplaces reference it. Replace the example path
with the checkout's absolute path.

## Claude Code

```sh
claude plugin marketplace add /path/to/agent-plugins --scope user
claude plugin install voiceflow@voiceflow-plugins --scope user
claude plugin list
```

Check `claude plugin marketplace list` first and reuse a matching source. Do not
replace an unrelated marketplace with the same name. For the website bundle,
use standalone skills below unless a marketplace checkout already exists.

## Codex

```sh
codex plugin marketplace add /path/to/agent-plugins
codex plugin add voiceflow@voiceflow-plugins
codex plugin list
```

Check `codex plugin marketplace list` first; reuse a matching source. Older
versions without these commands can use standalone skills. Do not bypass the
host's installation policy or change trust settings.

## Cursor and standalone skills

Standalone installation does not depend on a marketplace listing. With
Python 3.10+ already available, use the helper for the current client:

```sh
python3 voiceflow/skills/voiceflow-setup/scripts/install_skills.py --client cursor
```

It also accepts `claude` and `codex`. It is idempotent and refuses conflicting
files. For an intentional package update use `--update`; user edits still cause
a refusal. `--target /absolute/directory` supports custom locations and tests.

Without Python, copy the whole `voiceflow/skills/` tree using the agent's file
tools, checking all destinations before copying. Preserve identical files and
refuse conflicts. Copy the entire skill tree, including each skill's LICENSE,
to retain its notices and relative references.

| Client | Default user skill directory |
| --- | --- |
| Cursor | `~/.cursor/skills/` |
| Claude Code | `~/.claude/skills/` (or configured `CLAUDE_CONFIG_DIR`) |
| Codex | `$CODEX_HOME/skills/`, otherwise `~/.codex/skills/` |

Verify the entry skill and references exist and check the host's skill/plugin
inventory when available. Reading a file does not prove automatic discovery.
Load the entry skill directly now if needed; tell the user if a reload is needed
for future native discovery. Do not install into every agent on the machine.

## Docs MCP for standalone skills

Native plugin packages include the public Voiceflow Knowledge MCP configuration.
After installation, discover and verify its tools; host approval or reload may
still be needed. Standalone skill copying does not install server configuration.

For standalone installs, inspect existing connections first. Reuse a connection
to the Voiceflow docs server that the user already added. If there is none, add
it with the URL below, using the current host's supported MCP setup. The URL
ends in `logging=off`, which turns off docs request logging for this connection.
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

Use native update/uninstall commands for plugins; inspect current host help.
For standalone installs, `--uninstall` removes only unchanged files managed by
the helper. It refuses edited files. Manual copies have no management receipt;
compare their contents before replacement/removal. Keep a backup of edits.
Removal does not revoke Voiceflow OAuth access or remove the CLI.
