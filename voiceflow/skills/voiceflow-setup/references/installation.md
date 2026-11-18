# Install the released CLI

First follow the reuse checks in [setup](setup.md). The steps below download
the pinned Voiceflow CLI from Voiceflow's official GitHub releases. They check
the download's SHA-256 before they run or install anything. They do not sign
in, edit profiles, or replace an existing `vf`.

The pinned version is in `scripts/cli-version.txt` in this skill's folder. The
six release checksums are in `scripts/checksums.txt`. The steps read both
files, so never type a version or a checksum into them.

Each block below does the same five things:

1. Reads the pinned version and finds the operating system and architecture.
2. Stops if a `vf` already exists at the target path.
3. Downloads the release asset for that version over HTTPS, with timeouts and
   one retry.
4. Compares its SHA-256 with the asset's line in `scripts/checksums.txt`. On a
   mismatch it stops, and nothing is installed.
5. Runs `vf version` on the extracted file to confirm the pinned version, moves
   the file into place without replacing anything, and prints its absolute path.

Before you run a block, change its first line to the absolute path of the
folder that holds this skill's `SKILL.md`. Run the whole block as one command,
because each step uses values from the step before.

## macOS and Linux

Run this in bash or zsh. It needs curl, tar, and shasum or sha256sum.

```sh
skill_dir='/path/to/voiceflow-setup'
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
```

## Windows

Run this in Windows PowerShell 5.1 or later, or in PowerShell 7.

```powershell
$skillDir = 'C:\path\to\voiceflow-setup'
& {
    $ErrorActionPreference = 'Stop'
    $version = (Get-Content (Join-Path $skillDir 'scripts/cli-version.txt') -Raw).Trim()
    $arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()
    if ($arch -eq 'x64') { $arch = 'x86_64' }
    if ($arch -notin @('arm64', 'x86_64')) { throw "Unsupported architecture: $arch" }
    $targetDir = $env:VF_INSTALL_DIR
    if (-not $targetDir) { $targetDir = Join-Path $env:LOCALAPPDATA 'Voiceflow\bin' }
    $targetDir = [System.IO.Path]::GetFullPath($targetDir)
    $target = Join-Path $targetDir 'vf.exe'
    if (Test-Path -LiteralPath $target) { throw "Existing executable preserved: $target. Check its version before upgrading." }
    $asset = "vf_Windows_$arch.zip"
    $checksumLines = Get-Content (Join-Path $skillDir 'scripts/checksums.txt')
    $entry = @($checksumLines | Where-Object { ($_ -split '\s+')[1] -eq $asset })
    if ($entry.Count -ne 1) { throw 'Missing pinned checksum.' }
    $expected = ($entry[0] -split '\s+')[0]
    $scratch = Join-Path ([System.IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
    $stage = $null
    New-Item -ItemType Directory -Path $scratch | Out-Null
    try {
        $archive = Join-Path $scratch 'vf.zip'
        $url = "https://github.com/voiceflow/cli/releases/download/v$version/$asset"
        for ($attempt = 0; $attempt -lt 2; $attempt++) {
            try {
                Invoke-WebRequest -Uri $url -OutFile $archive -TimeoutSec 120 -UseBasicParsing
                break
            } catch {
                if ($attempt -eq 1) { throw }
                Start-Sleep -Seconds 1
            }
        }
        if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
            throw 'Checksum mismatch; nothing installed.'
        }
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [System.IO.Compression.ZipFile]::OpenRead($archive)
        try {
            $binary = $zip.GetEntry('vf.exe')
            if (-not $binary) { throw 'Release does not contain vf.exe.' }
            $extracted = Join-Path $scratch 'vf.exe'
            [System.IO.Compression.ZipFileExtensions]::ExtractToFile($binary, $extracted)
        } finally { $zip.Dispose() }
        $reported = & $extracted version
        if ($LASTEXITCODE -ne 0 -or $reported[0] -ne "vf $version") { throw 'Unexpected executable version.' }
        New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
        $stage = Join-Path $targetDir ('.vf-' + [guid]::NewGuid().ToString() + '.exe')
        Copy-Item -LiteralPath $extracted -Destination $stage
        # File.Move without overwrite preserves a binary created during download.
        [System.IO.File]::Move($stage, $target)
        Write-Output $target
    } finally {
        if ($stage -and (Test-Path -LiteralPath $stage)) { Remove-Item -LiteralPath $stage -Force }
        Remove-Item -LiteralPath $scratch -Recurse -Force
    }
}
```

## After the install

`VF_INSTALL_DIR` sets a custom install folder. The defaults are `~/.local/bin`
on macOS and Linux, and `%LOCALAPPDATA%\Voiceflow\bin` on Windows. Use the
printed absolute path for the rest of this session. You may add its folder to
this session's PATH, but do not edit persistent profiles without asking. Agents
can find the saved path in later sessions.

For an upgrade the user approved, keep a copy of the old binary outside the
target path, and restore it if the install fails. Never use sudo to force an
install. A failed download or checksum leaves the target folder unchanged. The
checksums come from the same release over HTTPS, so they detect a corrupt
download. They are not an independent publisher signature.

If these steps cannot run, for example on an unsupported architecture or in a
restricted shell, explain the obstacle. Then point to the
[official CLI install page](https://www.voiceflow.com/docs/cli/install). Its
methods install the latest release unless you pin one. After any of them, run
`vf version` and continue with the [CLI guide](cli.md). Do not substitute
another project's `vf` executable.
