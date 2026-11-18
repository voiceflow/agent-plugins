#!/usr/bin/env bash
# Install the pinned Voiceflow CLI on macOS or Linux. CI and maintainers run this file.
# Everything after the skill_dir line is the macOS and Linux block in
# voiceflow/skills/voiceflow-setup/references/installation.md, which customers' assistants run.
# scripts/validate.py fails when the two differ, so change both together.
set -euo pipefail
skill_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../voiceflow/skills/voiceflow-setup" && pwd)"
(
  set -euo pipefail
  version="$(tr -d '\r\n' < "$skill_dir/scripts/cli-version.txt")"
  platform="$(uname -s)"
  arch="$(uname -m)"
  case "$platform" in Darwin|Linux) ;; *) echo "Unsupported platform: $platform" >&2; exit 2 ;; esac
  case "$arch" in arm64|aarch64) arch=arm64 ;; x86_64|amd64) arch=x86_64 ;; *) echo "Unsupported architecture: $arch" >&2; exit 2 ;; esac
  target_dir="${VF_INSTALL_DIR:-$HOME/.local/bin}"
  target="$target_dir/vf"
  if [ -e "$target" ] || [ -L "$target" ]; then
    echo "Existing executable preserved: $target. Check its version before upgrading." >&2
    exit 3
  fi
  asset="vf_${platform}_${arch}.tar.gz"
  expected="$(awk -v asset="$asset" '$2 == asset {print $1}' "$skill_dir/scripts/checksums.txt")"
  if [ "${#expected}" -ne 64 ]; then echo "Missing pinned checksum." >&2; exit 2; fi
  scratch="$(mktemp -d)"
  stage=""
  cleanup() { rm -rf -- "$scratch"; if [ -n "$stage" ]; then rm -f -- "$stage"; fi; }
  trap cleanup EXIT
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
    --connect-timeout 15 --max-time 120 --retry 1 --retry-max-time 150 \
    "https://github.com/voiceflow/cli/releases/download/v$version/$asset" -o "$scratch/archive.tar.gz"
  if command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "$scratch/archive.tar.gz" | awk '{print $1}')"
  else
    actual="$(shasum -a 256 "$scratch/archive.tar.gz" | awk '{print $1}')"
  fi
  if [ "$actual" != "$expected" ]; then echo "Checksum mismatch; nothing installed." >&2; exit 4; fi
  # Extract only the expected executable from the verified release.
  tar -xzf "$scratch/archive.tar.gz" -C "$scratch" vf
  if [ ! -f "$scratch/vf" ] || [ -L "$scratch/vf" ]; then echo "Invalid executable." >&2; exit 4; fi
  chmod 755 "$scratch/vf"
  reported="$("$scratch/vf" version)"
  if [ "${reported%%$'\n'*}" != "vf $version" ]; then
    echo "Unexpected executable version." >&2
    exit 4
  fi
  mkdir -p -- "$target_dir"
  target_dir="$(cd -- "$target_dir" && pwd)"
  target="$target_dir/vf"
  stage="$(mktemp "$target_dir/.vf.XXXXXX")"
  cp "$scratch/vf" "$stage"
  chmod 755 "$stage"
  # An atomic no-clobber link also protects an executable created during download.
  ln "$stage" "$target"
  printf '%s\n' "$target"
)
