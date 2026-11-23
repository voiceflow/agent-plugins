#!/usr/bin/env bash
# Build the OpenAI plugin ZIP from a release tag.
#
# Usage:  scripts/openai/build_zip.sh <tag>        for example: scripts/openai/build_zip.sh v1.2.1
# Output: <repo>/.submissions/openai/package/ and voiceflow-openai-<version>-DRAFT.zip
#         next to it. .submissions/ is git-ignored.
#
# The plugin files come from the tag through `git archive`, so the working tree is
# never packaged. The review data and the MCP server come from review.json and
# mcp.json next to this script. The output folder is fixed, like scripts/build.py's
# dist/, so the script never deletes anything outside it.
set -euo pipefail
tag="${1:?usage: build_zip.sh <tag>, for example v1.2.1}"
here="$(cd "$(dirname "$0")" && pwd -P)"
repo="$(cd "$here/../.." && pwd -P)"
kit="$repo/.submissions/openai"

# Refuse symlinks anywhere on the output path, because the script replaces package/.
for path in "$repo/.submissions" "$kit" "$kit/package"; do
  if [ -L "$path" ]; then
    echo "Refusing symlinked output path: $path" >&2
    exit 1
  fi
done
if ! git -C "$repo" rev-parse --verify --quiet "$tag^{commit}" >/dev/null; then
  echo "Unknown tag: $tag. Run: git fetch --tags origin" >&2
  exit 1
fi
mkdir -p "$kit"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# 1. Export the plugin folder, its publication inventory, and the MCP surface snapshot
#    exactly as tagged.
git -C "$repo" archive --format=tar "$tag" voiceflow package-files.txt | tar -x -C "$work"
git -C "$repo" show "$tag:tests/fixtures/voiceflow-surface.json" > "$work/surface.json"
plugin="$work/voiceflow"

# 2. Fail when the tagged plugin holds a file that package-files.txt does not list, or lacks
#    one it lists. This is the same check scripts/build.py runs before every package build.
python3 -I -c 'import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1])
from build import package_files
list(package_files(Path(sys.argv[2])))' "$repo/scripts" "$work"

# 3. Remove the files for other hosts. OpenAI reads the portable plugin.json and mcp.json.
#    The tagged .mcp.json names the docs server, which would be a second MCP server.
rm -rf "$plugin/.claude-plugin" "$plugin/.cursor-plugin" "$plugin/.codex-plugin" "$plugin/.mcp.json"

# 4. Replace the docs server with the account server. An OpenAI plugin connects one MCP server.
cp "$here/mcp.json" "$plugin/mcp.json"

# 5. Merge the review and publication fields, and package_version, into plugin.json.
python3 -I "$here/package_tools.py" merge "$plugin/plugin.json" "$here/review.json"

# 6. Check the package. Errors stop the build. Blockers are printed.
python3 -I "$here/package_tools.py" validate "$plugin" --surface "$work/surface.json"

# 7. Replace package/ and write the ZIP with plugin.json at the archive root.
version="$(python3 -I -c 'import json, sys; print(json.load(open(sys.argv[1]))["version"])' "$plugin/plugin.json")"
zip_path="$kit/voiceflow-openai-$version-DRAFT.zip"
rm -rf "$kit/package" "$zip_path"
mv "$plugin" "$kit/package"
(cd "$kit/package" && zip -q -r -X "$zip_path" . -x '*.DS_Store')
echo "Built $zip_path from $tag ($(git -C "$repo" rev-parse --short "$tag^{commit}"))."
