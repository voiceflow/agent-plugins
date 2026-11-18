# Install the pinned Voiceflow CLI on Windows. CI and maintainers run this file.
# Everything after the $skillDir line is the Windows block in
# voiceflow/skills/voiceflow-setup/references/installation.md, which customers' assistants run.
# scripts/validate.py fails when the two differ, so change both together.
$ErrorActionPreference = 'Stop'
$skillDir = Join-Path $PSScriptRoot '../../voiceflow/skills/voiceflow-setup'
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
