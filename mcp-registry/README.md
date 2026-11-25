# MCP Registry entries

These files describe Voiceflow's two remote MCP servers for the official
[MCP Registry](https://registry.modelcontextprotocol.io). They are not part of
the plugin package. Only the **Publish MCP Registry entries** workflow,
`.github/workflows/publish-mcp.yml`, publishes them. Nobody signs in to the
registry from a laptop.

| Folder | Name | Server | URL |
| --- | --- | --- | --- |
| `voiceflow/` | `com.voiceflow/voiceflow` | Voiceflow account MCP, OAuth | `https://mcp.voiceflow.com/mcp?version=3&dynamic=true` |
| `docs/` | `com.voiceflow/docs` | Voiceflow docs MCP, no sign-in | The public docs MCP URL, without the package's `logging=off` option |

The account entry adds `dynamic=true`. Most people who install from the
registry use IDE hosts such as VS Code with GitHub Copilot. These hosts cap or
trim long tool lists. With `dynamic=true`, the server lists about a dozen tools
and runs the rest by name. The setup guide gives these hosts the same URL.

The docs entry has no `logging=off` option. People who add the server from the
registry are treated like people who add it by hand. The docs server logs their
requests in full, and its tools require `why`.

A published name cannot change. A published version cannot be edited, so each
change needs a new `version` value.

## Publish a new version

1. Raise `version` in the changed `server.json` in a pull request, and merge it.
2. Run **Publish MCP Registry entries** from `main` with **publish** unchecked.
   This dry run does not use the signing key. It checks the names and fields,
   validates each entry with the registry, and tests both live servers. The
   run summary shows the plan for each entry: new, identical, or conflict.
3. Run it again from `main` with **publish** checked. The publish job waits
   until a reviewer approves the `mcp-registry-production` environment.
4. The job plans again, because the registry can change while it waits. It
   skips a version that is already active with the same content. It fails on a
   conflict: the same version with different content, or a version that is
   deprecated or deleted. Fix a conflict with a new version.
5. The job signs in with the DNS key, publishes each new version, and signs out.
6. The job reads back each public record. It fails unless the status is active
   and the name, version, title, description, website URL, and remotes match
   the manifest.

The live tests change nothing. The docs server gets one synthetic question
through `ask_voiceflow`, with a `why` that names the automated check. The
answer must cite a docs URL. The docs server logs this call. The account
server gets `initialize` without credentials. It must answer HTTP 401 and point
to OAuth metadata that names an authorization server. The test never signs in.

## Guardrails

- The workflow publishes only `com.voiceflow/docs` and `com.voiceflow/voiceflow`,
  the list in `scripts/mcp_registry.py`. The DNS key can publish any
  `com.voiceflow/*` name, and any name under a subdomain such as
  `com.voiceflow.example/*`. So this list is a guardrail, not a security boundary.
- Only a run from `main` can publish. The environment must also allow only
  `main` and require a reviewer.
- The signing key is an environment secret. The dry run job cannot read it.
  The publisher reads it from an environment variable, so it never appears in
  a command line.
- `.github/CODEOWNERS` names owners for the workflows, the installer, the
  script, and the manifests. The jobs run the script with `python -I`. Python
  then imports nothing else from the checkout, so a new file in `scripts/`
  without a code owner cannot run in the publish job.
- `scripts/install_mcp_publisher.sh` pins the publisher version and its SHA-256.
  Change both together after you review the upstream release.

## One-time setup

The infrastructure owner proves the domain and stores the key. Nobody else
handles the private key.

1. Make an Ed25519 key with OpenSSL 3. The LibreSSL that ships with macOS
   cannot. Keep the key folder outside every repository. The commands print
   only the TXT value, which holds the public key.
   ```bash
   OPENSSL=/opt/homebrew/opt/openssl@3/bin/openssl
   KEY_DIR=<folder outside any repository>
   umask 077
   mkdir -p "$KEY_DIR"
   KEY="$KEY_DIR/voiceflow-mcp-registry.pem"
   "$OPENSSL" genpkey -algorithm Ed25519 -out "$KEY"
   echo "v=MCPv1; k=ed25519; p=$("$OPENSSL" pkey -in "$KEY" -pubout -outform DER | tail -c 32 | base64)"
   ```
2. In AWS Route 53, add the printed value as one more value of the TXT record
   on the apex, `voiceflow.com` itself. Keep SPF and every other value.
   Check it with `dig TXT voiceflow.com +short | grep MCPv1`.
3. A repository admin creates the `mcp-registry-production` environment. Allow
   only the `main` branch. Add required reviewers and turn on "Prevent
   self-review". The admin also turns on "Require review from Code Owners" in
   the `main` ruleset.
4. Upload the raw private key as hex, over standard input, as an environment
   secret. Never store it as a repository or organization secret.
   ```bash
   "$OPENSSL" pkey -in "$KEY" -noout -text | awk '/priv:/{f=1;next}/pub:/{f=0}f' | tr -d ' :\n' \
     | gh secret set MCP_REGISTRY_DNS_KEY --env mcp-registry-production --repo voiceflow/agent-plugins
   ```
5. Run the dry run, then a publish, as described above.

## If the key may be exposed

1. Halt publishing. Disable the **Publish MCP Registry entries** workflow and
   reject any run that waits for approval.
2. Delete `MCP_REGISTRY_DNS_KEY` from the `mcp-registry-production` environment.
3. With the DNS owner, remove the exposed `MCPv1` value from the apex TXT
   record at once. Keep SPF and every other value. Then make a new key with the
   setup steps above. Remove every stale `MCPv1` value. Anyone who holds a key
   can sign in while its value is published.
4. Audit the namespace with `python3 -I scripts/mcp_registry.py audit`. It
   reads every page of the public listing, including deleted versions and
   subdomain names. It prints each name, version, and status, and fails on any
   name outside the allowlist. Review the recent runs of the workflow too.
5. Contact the registry maintainers through
   [modelcontextprotocol/registry](https://github.com/modelcontextprotocol/registry)
   to remove entries that Voiceflow did not publish.

Rotating the key stops new sign-ins only. A registry token that was issued
before the rotation stays valid until it expires, currently five minutes after
it was issued. See the registry's
[authentication guide](https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/authentication.mdx).
