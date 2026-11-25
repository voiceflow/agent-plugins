# MCP Registry

Registry: https://registry.modelcontextprotocol.io. There is no web form. The
**Publish MCP Registry entries** workflow, `.github/workflows/publish-mcp.yml`,
publishes the entries in `mcp-registry/voiceflow/server.json` and
`mcp-registry/docs/server.json`. Never sign in to the registry from a laptop,
and never generate, read, or upload the signing key.

| Name | Version | Remote URL |
| --- | --- | --- |
| `com.voiceflow/voiceflow` | 3.0.0 | `https://mcp.voiceflow.com/mcp?version=3&dynamic=true` |
| `com.voiceflow/docs` | 1.0.0 | `https://www.voiceflow.com/docs/mcp` |

The account entry uses the dynamic URL because the registry's main users are
IDE hosts that cap long tool lists. The docs entry leaves out `?logging=off` on
purpose. `mcp-registry/README.md` explains both choices.

## Before the first publish

The infrastructure owner adds the `MCPv1` TXT value on `voiceflow.com` and
stores `MCP_REGISTRY_DNS_KEY` in the `mcp-registry-production` environment. A
repository admin sets that environment to `main` only, with required
reviewers. The steps are under "One-time setup" in `mcp-registry/README.md`.
Check that the DNS value is live:

```bash
dig TXT voiceflow.com +short | grep MCPv1
```

## Publish

A new version reaches `main` through a reviewed pull request that raises
`version` in `server.json`. Then run the workflow from `main`: a dry run first,
then a publish. Run them only when the owner asks.

```bash
gh workflow run publish-mcp.yml --repo voiceflow/agent-plugins --ref main -f publish=false
gh run list --workflow publish-mcp.yml --repo voiceflow/agent-plugins --limit 3
gh run view <run id> --repo voiceflow/agent-plugins --log-failed
```

The dry run checks the allowlist and fields, validates each entry with the
registry, and tests both live servers. Its summary shows each entry as new,
identical, or conflict. A conflict needs a new version.

For the publish, run the first command with `-f publish=true`. The job waits
for a reviewer to approve the `mcp-registry-production` environment in GitHub.
It then publishes only the new versions and reads each record back. Confirm the
result in the public listing. The audit reads every page, including deleted
versions, and fails on a name outside the allowlist:

```bash
python3 -I scripts/mcp_registry.py audit
```

## If something goes wrong

A failed read-back or an unexpected entry under `com.voiceflow/` needs the
owner. If the key may be exposed, follow "If the key may be exposed" in
`mcp-registry/README.md`: halt the workflow, delete the secret, rotate the key
with the DNS owner, audit the namespace with `python3 -I scripts/mcp_registry.py audit`,
review the workflow runs, and contact the registry maintainers.
