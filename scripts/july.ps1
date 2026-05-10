$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$JulyScript = Join-Path $Root "apps\july\scripts\july.ps1"

& $JulyScript @args
exit $LASTEXITCODE
