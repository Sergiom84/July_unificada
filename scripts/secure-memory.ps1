param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("seal", "open", "list")]
  [string]$Action,

  [string]$Key,
  [string]$Text,
  [string]$PlaintextPath
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SecureRoot = Join-Path $RepoRoot "context\secure"
$VaultDir = Join-Path $SecureRoot "vault"
$IndexPath = Join-Path $SecureRoot "index.json"

function Ensure-Vault {
  New-Item -ItemType Directory -Force -Path $VaultDir | Out-Null
  if (-not (Test-Path -LiteralPath $IndexPath)) {
    "[]" | Set-Content -LiteralPath $IndexPath -Encoding UTF8
  }
}

function Get-KeyId([string]$Value) {
  $sha = [System.Security.Cryptography.SHA256]::Create()
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
  $hash = $sha.ComputeHash($bytes)
  return (($hash | ForEach-Object { $_.ToString("x2") }) -join "")
}

function Protect-Plaintext([string]$Plaintext, [string]$ValueKey) {
  $secure = ConvertTo-SecureString -String $Plaintext -AsPlainText -Force
  return ConvertFrom-SecureString -SecureString $secure
}

function Unprotect-Ciphertext([string]$Ciphertext, [string]$ValueKey) {
  $secure = ConvertTo-SecureString -String $Ciphertext
  $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try {
    return [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  } finally {
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  }
}

function Read-Index {
  Ensure-Vault
  $raw = Get-Content -LiteralPath $IndexPath -Raw -Encoding UTF8
  if ([string]::IsNullOrWhiteSpace($raw)) {
    return @()
  }
  $items = $raw | ConvertFrom-Json
  if ($null -eq $items) {
    return @()
  }
  return @($items)
}

function Write-Index($Items) {
  ConvertTo-Json -InputObject @($Items) -Depth 5 |
    Set-Content -LiteralPath $IndexPath -Encoding UTF8
}

function Read-Plaintext {
  if ($Text) {
    return $Text
  }

  if ($PlaintextPath) {
    return Get-Content -LiteralPath $PlaintextPath -Raw -Encoding UTF8
  }

  $secure = Read-Host "Texto a cifrar" -AsSecureString
  $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try {
    return [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  } finally {
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  }
}

function Seal-Item {
  if (-not $Key) {
    throw "Falta -Key."
  }

  Ensure-Vault
  $keyId = Get-KeyId $Key
  $fileName = "$keyId.dpapi.json"
  $relativePath = "context/secure/vault/$fileName"
  $absolutePath = Join-Path $VaultDir $fileName
  $now = (Get-Date).ToUniversalTime().ToString("o")
  $plaintext = Read-Plaintext
  $ciphertext = Protect-Plaintext $plaintext $Key

  [ordered]@{
    version = 1
    key = $Key
    protection = "windows-dpapi-current-user"
    created_at = $now
    updated_at = $now
    ciphertext = $ciphertext
  } |
    ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath $absolutePath -Encoding UTF8

  $items = Read-Index
  $items = @($items | Where-Object { $_.key -ne $Key })
  $items += [pscustomobject]@{
    key = $Key
    key_id = $keyId
    file = $relativePath
    protection = "windows-dpapi-current-user"
    updated_at = $now
  }
  Write-Index $items

  Write-Output "Sellado: $relativePath"
}

function Open-Item {
  if (-not $Key) {
    throw "Falta -Key."
  }

  $keyId = Get-KeyId $Key
  $absolutePath = Join-Path $VaultDir "$keyId.dpapi.json"
  if (-not (Test-Path -LiteralPath $absolutePath)) {
    throw "No existe entrada cifrada para key '$Key'."
  }

  $payload = Get-Content -LiteralPath $absolutePath -Raw -Encoding UTF8 |
    ConvertFrom-Json
  if ($payload.protection -ne "windows-dpapi-current-user") {
    throw "Protección no soportada: $($payload.protection)"
  }

  Unprotect-Ciphertext $payload.ciphertext $Key
}

function List-Items {
  Read-Index |
    Select-Object key, file, protection, updated_at |
    Format-Table -AutoSize
}

switch ($Action) {
  "seal" { Seal-Item }
  "open" { Open-Item }
  "list" { List-Items }
}
