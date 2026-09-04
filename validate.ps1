#!/usr/bin/env pwsh
# Windows entry point for the repository verification contract.
# It runs the same checks as ./validate.sh, in the same order, and reports the
# checks that do not apply to this host instead of passing them silently.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# A native command's exit status is inspected, not thrown, exactly as under bash.
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$PackageDir = $PSScriptRoot
$env:PYTHONDONTWRITEBYTECODE = '1'
$script:Failures = 0
$script:Warnings = 0

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

function Invoke-Check {
    param(
        [Parameter(Mandatory)] [string] $Label,
        [Parameter(Mandatory)] [scriptblock] $Action
    )
    & $Action
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PASS  $Label"
    }
    else {
        Write-Host "FAIL  $Label"
        $script:Failures++
    }
}

$suites = @(
    @{ Label = 'upstream compatibility'; Module = 'evals/test_compatibility.py' }
    @{ Label = 'skill packages'; Module = 'evals/test_skill_packages.py' }
    @{ Label = 'removed architecture'; Module = 'evals/test_removed_architecture.py' }
    @{ Label = 'Codex lifecycle'; Module = 'distributions/codex/evals/test_lifecycle.py' }
    @{ Label = 'Claude Code lifecycle'; Module = 'distributions/claude-code/evals/test_lifecycle.py' }
    @{ Label = 'Claude Code plugin'; Module = 'evals/test_claude_code_plugin.py' }
    @{ Label = 'repository contract'; Module = 'evals/test_repository_contract.py' }
)

Push-Location $PackageDir
try {
    foreach ($suite in $suites) {
        $label = $suite.Label
        $module = $suite.Module
        Invoke-Check $label { & $python -m unittest $module -v }
    }

    # The POSIX entry points still ship, and their syntax is still a repository
    # contract; this host simply has no bash to check it with. The lifecycle
    # suites above run here in full, driving the .ps1 entry points, so the
    # transactional behavior is covered on Windows. What stays Linux-only is
    # the .sh entry points themselves. Recording both reductions as warnings
    # keeps them visible instead of silently green.
    Write-Host 'SKIP  shell syntax (no POSIX shell on this host; checked on Linux CI)'
    $script:Warnings++
    Write-Host 'SKIP  POSIX lifecycle entry points (install.sh/uninstall.sh/validate.sh; executed on Linux CI)'
    $script:Warnings++

    Invoke-Check 'package manifest' { & $python -B 'scripts/manifest.py' --verify }
}
finally {
    Pop-Location
}

Write-Host ''
Write-Host "Validation summary: $script:Failures failure(s), $script:Warnings warning(s)."
if ($script:Failures -ne 0) {
    exit 1
}
exit 0
