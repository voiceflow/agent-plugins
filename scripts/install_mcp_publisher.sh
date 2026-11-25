#!/usr/bin/env bash
# CI-only Linux x64 install of the MCP Registry publisher for .github/workflows/publish-mcp.yml.
# The checksum was reviewed against the release's checksums file. Change the version and the
# checksum together, after reviewing the upstream release; never fetch the checksum at run time.
set -euo pipefail
version=1.8.16
asset=mcp-publisher_linux_amd64.tar.gz
checksum=6e2f799550cf843c6fd3350498d56cc49be3dc0af1e6237eb0e6435c7a9d5c05
target="${1:?Provide a tools directory outside the repository}"
scratch="$(mktemp -d)"
trap 'rm -rf -- "$scratch"' EXIT
mkdir -p -- "$target"
curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
  --tlsv1.2 --connect-timeout 15 --max-time 120 --retry 2 \
  "https://github.com/modelcontextprotocol/registry/releases/download/v$version/$asset" -o "$scratch/$asset"
printf '%s  %s\n' "$checksum" "$scratch/$asset" | sha256sum --check --status
tar -xzf "$scratch/$asset" -C "$scratch" mcp-publisher
test -f "$scratch/mcp-publisher" && test ! -L "$scratch/mcp-publisher"
install -m 755 "$scratch/mcp-publisher" "$target/mcp-publisher"
