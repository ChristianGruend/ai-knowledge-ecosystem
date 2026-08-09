# setup.ps1 — Einmalig auf Windows ausführen (PowerShell als Admin oder Developer Mode aktiv)
# Erstellt Symlink: ~/.claude/CLAUDE.md → <repo>\memory\CLAUDE.md

$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = Join-Path $RepoDir "memory\CLAUDE.md"
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
$Link = Join-Path $ClaudeDir "CLAUDE.md"

if (-not (Test-Path $ClaudeDir)) {
    New-Item -ItemType Directory -Path $ClaudeDir | Out-Null
}

$existingItem = Get-Item $Link -ErrorAction SilentlyContinue
if ($existingItem -and $existingItem.LinkType -eq "SymbolicLink") {
    Write-Host "Symlink existiert bereits: $Link"
} elseif (Test-Path $Link) {
    Write-Host "WARNUNG: $Link ist eine normale Datei. Backup erstellt."
    Rename-Item $Link "$Link.bak"
    New-Item -ItemType SymbolicLink -Path $Link -Target $Target
    Write-Host "Symlink erstellt: $Link → $Target"
} else {
    New-Item -ItemType SymbolicLink -Path $Link -Target $Target
    Write-Host "Symlink erstellt: $Link → $Target"
}
