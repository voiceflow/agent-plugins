# Cursor Marketplace

Submit at https://cursor.com/marketplace/publish. The Cursor team reviews every
plugin and update by hand. Its checklist asks that the plugin was tested
locally first.

## Local test

```bash
mkdir -p ~/.cursor/plugins/local/voiceflow
git archive <tag> voiceflow | tar -x -C ~/.cursor/plugins/local/voiceflow --strip-components=1
```

1. In Cursor, run **Developer: Reload Window**.
2. **Customize** shows 18 Voiceflow skills and the `voiceflow-knowledge` docs server.
3. A docs question, such as "How do I add a knowledge base source in
   Voiceflow?", uses the docs server.
4. "Connect my Voiceflow account and list my agents" opens a browser sign-in,
   then lists agents. Setup connects Cursor to the dynamic account URL.
5. Remove the local copy afterwards: `rm -rf ~/.cursor/plugins/local/voiceflow`.

## Form values

| Field | Value |
| --- | --- |
| Repository | `https://github.com/voiceflow/agent-plugins` |
| Tag | The release tag |
| Plugin folder | `voiceflow` |
| Short description | Connect to Voiceflow, then build and improve agents with shared product guidance. |
| Long description | `longDescription` from `voiceflow/plugin.json` at the tag |
| Website | `https://www.voiceflow.com` |
| Docs | `https://www.voiceflow.com/docs` |
| Category | Developer Tools |

The repository has `.cursor-plugin/marketplace.json` at the root and
`voiceflow/.cursor-plugin/plugin.json`. Cursor does not document the form's
other fields; read them from the owner's screenshot.
