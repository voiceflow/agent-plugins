# MCP Registry

Registry: https://registry.modelcontextprotocol.io. There is no web form; a
maintainer runs `mcp-publisher`. The entries are `mcp-registry/voiceflow/server.json`
and `mcp-registry/knowledge/server.json`.

| Name | Version | Remote URL |
| --- | --- | --- |
| `com.voiceflow/voiceflow` | 3.0.0 | `https://mcp.voiceflow.com/mcp?version=3` |
| `com.voiceflow/knowledge` | 2.1.2 | `https://www.voiceflow.com/docs/mcp` |

The docs entry leaves out `?logging=off` on purpose; see `mcp-registry/README.md`.
A published name cannot change and a published version cannot be edited, so
the owner approves the names before the first publish.

## Prove the domain with DNS

1. Make an Ed25519 key with OpenSSL 3 (macOS LibreSSL cannot), and keep it
   outside every repository. `.gitignore` also blocks `*.pem`.
   ```bash
   OPENSSL=/opt/homebrew/opt/openssl@3/bin/openssl
   KEY=<path outside any repository>/voiceflow-mcp-registry.pem
   (umask 077 && "$OPENSSL" genpkey -algorithm Ed25519 -out "$KEY")
   echo "v=MCPv1; k=ed25519; p=$("$OPENSSL" pkey -in "$KEY" -pubout -outform DER | tail -c 32 | base64)"
   ```
2. Add the printed value as one more TXT record on the apex, `voiceflow.com`
   itself, in AWS Route 53. Keep the existing TXT values. The value holds only
   the public key.
3. Check it: `dig TXT voiceflow.com +short | grep MCPv1`.

Without DNS, `mcp-publisher login github` works for `io.github.voiceflow/...`
names. That needs new names in the entries and a release.

## Install the publisher, pinned

```bash
D=~/bin && mkdir -p $D && cd $(mktemp -d) \
  && gh release download v1.8.7 -R modelcontextprotocol/registry \
       -p 'mcp-publisher_darwin_arm64.tar.gz' -p 'registry_1.8.7_checksums.txt' \
  && grep ' mcp-publisher_darwin_arm64.tar.gz$' registry_1.8.7_checksums.txt | shasum -a 256 -c - \
  && tar -xzf mcp-publisher_darwin_arm64.tar.gz -C $D mcp-publisher
```

## Log in and publish from the tag

```bash
MCP_PRIVATE_KEY="$("$OPENSSL" pkey -in "$KEY" -noout -text | sed -n '/priv:/,/pub:/p' | sed '1d;$d' | tr -d ' :\n')" \
  ~/bin/mcp-publisher login dns --domain voiceflow.com

TAG=<release tag>; OUT="$(mktemp -d)"
git show "$TAG:mcp-registry/voiceflow/server.json" > "$OUT/voiceflow.json"
git show "$TAG:mcp-registry/knowledge/server.json" > "$OUT/knowledge.json"
~/bin/mcp-publisher validate "$OUT/voiceflow.json" && ~/bin/mcp-publisher validate "$OUT/knowledge.json"
~/bin/mcp-publisher publish "$OUT/voiceflow.json" && ~/bin/mcp-publisher publish "$OUT/knowledge.json"
curl -s "https://registry.modelcontextprotocol.io/v0.1/servers?search=com.voiceflow"
```

Publish only after the owner approves the names and the record is live. Each
later publish needs a new `version` in `server.json`, raised in a release. When
the key rotates, remove the old TXT record first.
