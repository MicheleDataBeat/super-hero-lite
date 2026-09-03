#!/usr/bin/env pwsh
# Windows entry point for the Codex Distribution.
# It installs or updates package-owned state.
# It delegates to the same Python implementation as ./install.sh.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# A native command's exit status is inspected, not thrown, exactly as under bash.
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$DistributionDir = $PSScriptRoot
$PackageRoot = (Resolve-Path (Join-Path $DistributionDir '../..')).Path
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
$env:PYTHONDONTWRITEBYTECODE = '1'

$python = $null
foreach ($name in 'python3', 'python', 'py') {
    $found = @(Get-Command $name -CommandType Application -ErrorAction SilentlyContinue)
    if ($found.Count -gt 0) {
        # More than one command can answer to a name on Windows, where a real
        # interpreter and a Microsoft Store alias both do. Take the first, which
        # is the one PATH order would have run.
        $python = $found[0].Source
        break
    }
}
if (-not $python) {
    [Console]::Error.WriteLine('ERROR: missing required command: python3')
    exit 1
}

# managed_state.py validates git, gh, an interpreter, the host command and
# the GitHub CLI session itself, so this wrapper does not repeat those checks.
& $python -B (Join-Path $DistributionDir 'lib/managed_state.py') install `
    --package-root $PackageRoot `
    --home $HOME `
    --codex-home $CodexHome
exit $LASTEXITCODE
