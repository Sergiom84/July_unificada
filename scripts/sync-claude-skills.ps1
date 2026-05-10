$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$SourceDir = Join-Path $RepoRoot "skills"
$TargetDir = Join-Path $env:USERPROFILE ".claude\skills"

if (-not (Test-Path $SourceDir -PathType Container)) {
    throw "No skills directory found at $SourceDir"
}

if ((Test-Path $TargetDir) -and ((Get-Item $TargetDir).LinkType -eq "SymbolicLink")) {
    Remove-Item $TargetDir -Force
}

New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null

Get-ChildItem $SourceDir -Directory | ForEach-Object {
    $TargetSkill = Join-Path $TargetDir $_.Name
    if (Test-Path $TargetSkill) {
        Remove-Item $TargetSkill -Recurse -Force
    }
    Copy-Item $_.FullName $TargetSkill -Recurse
}

Write-Host "Synced Claude skills from $SourceDir to $TargetDir"
