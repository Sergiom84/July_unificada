$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$SourceDir = Join-Path $RepoRoot "skills"
$TargetDir = Join-Path $env:USERPROFILE ".codex\skills"

if (-not (Test-Path $SourceDir -PathType Container)) {
    throw "No skills directory found at $SourceDir"
}

New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null

Get-ChildItem $SourceDir -Directory | ForEach-Object {
    $TargetSkill = Join-Path $TargetDir $_.Name
    if (Test-Path $TargetSkill) {
        Remove-Item $TargetSkill -Recurse -Force
    }
    Copy-Item $_.FullName $TargetSkill -Recurse
}

Write-Host "Synced Codex skills from $SourceDir to $TargetDir"
