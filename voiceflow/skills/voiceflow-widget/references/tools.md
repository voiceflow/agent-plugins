# Widget tools and targeting

CLI contract checked against 0.287.0 on 2026-10-16. Inspect installed help or
connected MCP schemas if they differ. Examples use placeholders, not real IDs.

| Task | CLI | Account MCP tool |
| --- | --- | --- |
| Read draft settings | `vf widget get` | `vf_widget_get` |
| Patch draft settings | `vf widget update` | `vf_widget_update` |
| Get installation code | `vf widget get-snippet` | `vf_widget_get_snippet` |

The public Knowledge MCP supplies documentation; it does not perform these
account operations. If a tool is absent, rediscover tools/check connection
before concluding the feature is unavailable. Do not invent an MCP command.

## Read and get the snippet

```sh
vf widget get --project-id PROJECT_ID --environment-alias ENVIRONMENT_ALIAS --timeout 20s -o toon
vf widget get-snippet --project-id PROJECT_ID --environment-alias ENVIRONMENT_ALIAS --version-param published --timeout 20s -o toon
```

`get` reads the environment's **draft**, even if the website serves published
content. `get-snippet` defaults to `published`; `--version-param draft` is for
an explicitly requested preview. Do not install a draft snippet on the public
site by accident. The output contains installation code: extract that code,
not the CLI's surrounding structured envelope, for the site's HTML field.

Each MCP tool takes `projectID` and `environmentAlias` at the top level of its
input. Read its schema for the snippet version selector and update body
placement. Do not translate the CLI's `--version-param` spelling into an
invented MCP property. See the shared [request shapes](../../voiceflow/references/request-shapes.md#mcp-input-and-function-declarations).

## Patch only the intended settings

Read current settings first. A minimal color change uses `common.primaryColor`:

```json
{"common":{"primaryColor":{"color":"#245D58"}}}
```

Save the body as `widget-patch.json`, then, for an authorized draft edit:

```sh
vf widget update --project-id PROJECT_ID --environment-alias ENVIRONMENT_ALIAS --timeout 20s -o toon < widget-patch.json
```

Read back the changed fields. The merge rules matter:

- `chat`, `voice`, and `common` merge one level deep. Nested objects such as
  `banner`, `launcher`, and `footerLink` replace their entire stored object;
  merge the requested edits into the existing object before sending it.
- `common.primaryColor` also merges internally. Sending `color` alone
  regenerates its palette. Retain a deliberately customized palette if the
  requested change should preserve it.
- `security` replaces the entire block. Retain existing domain restrictions
  and other security settings unless the user requested their change.
- Some fields require entitlements. A forbidden field can reject the whole
  patch with 403, including otherwise allowed changes. Explain the specific
  limit; do not retry the same write or use CSS to bypass a paid feature.

## Preserve routing

Generated snippets contain the correct verification, runtime, and targeting
fields for the selected project. Preserve them during framework adaptation.
Never place an OAuth bearer token, personal key, or server API secret in browser
code. A generated browser verification identifier is not a management credential.

The generic widget API can follow traffic allocation when no environment is
pinned; an explicit environment overrides that behavior. The snippet operation
instead takes a selected environment and version. Do not silently remove that
pin or substitute legacy `production`/`development` values. If the user wants
traffic-split routing, inspect the current API docs and existing snippet first.

Saved widget settings require publication to affect the published widget.
Before publishing, inspect the environment's complete pending changes: a widget
request is not permission to release unrelated agent edits. If authorization
already covers that release, proceed; otherwise finish the reviewable draft
and explain the specific publication decision. See
[environments](../../voiceflow-environments/SKILL.md).

Source: [Widget API](https://www.voiceflow.com/docs/documentation/deploy/widget/web-chat-api).
