# MCP Registry entries

These files describe Voiceflow's two remote MCP servers for the official
[MCP Registry](https://registry.modelcontextprotocol.io). They are not part of
the plugin package, and nothing in this repository publishes them.

| Folder | Server | URL |
| --- | --- | --- |
| `voiceflow/` | Voiceflow account MCP, OAuth | `https://mcp.voiceflow.com/mcp?version=3` |
| `knowledge/` | Voiceflow Knowledge docs MCP, no sign-in | The public docs MCP URL, without the package's `logging=off` option |

The docs entry has no `logging=off` option. People who add the server from the
registry are treated like people who add it by hand. The docs server logs their
requests in full, and its tools require `why`.

Publishing needs an owner decision on the server names, because a published
name is hard to change. The `com.voiceflow/` namespace also needs DNS or HTTP
verification of `voiceflow.com`. See the registry's
[authentication guide](https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/authentication.mdx).
Each published version needs a new `version` value.
