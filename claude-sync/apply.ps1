# apply.ps1 - Claude Code Settings + Auto-Memory auf diesem Windows-System einspielen
# Voraussetzung: claude CLI wurde mindestens einmal im Home-Verzeichnis gestartet
#                 (erzeugt ~/.claude/projects/<key>/)

$RepoDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"

if (-not (Test-Path $ClaudeDir)) {
    New-Item -ItemType Directory -Path $ClaudeDir | Out-Null
}

# --- settings.json ---
$SettingsSrc = Join-Path $RepoDir "settings.json"
$SettingsDst = Join-Path $ClaudeDir "settings.json"

if (Test-Path $SettingsDst) {
    Copy-Item $SettingsDst "$SettingsDst.bak" -Force
    Write-Host "Backup erstellt: $SettingsDst.bak"
}
Copy-Item $SettingsSrc $SettingsDst -Force
Write-Host "settings.json eingespielt -> $SettingsDst"

# --- Auto-Memory ---
$ProjectsDir = Join-Path $ClaudeDir "projects"
if (-not (Test-Path $ProjectsDir)) {
    Write-Host "FEHLER: $ProjectsDir existiert nicht. Erst 'claude' im Home-Verzeichnis starten, dann erneut ausfuehren."
    exit 1
}

$ProjectDirs = Get-ChildItem $ProjectsDir -Directory
if ($ProjectDirs.Count -eq 0) {
    Write-Host "FEHLER: Kein Projekt-Verzeichnis unter $ProjectsDir gefunden."
    exit 1
} elseif ($ProjectDirs.Count -gt 1) {
    Write-Host "Mehrere Projekt-Verzeichnisse gefunden, bitte manuell waehlen:"
    $ProjectDirs | ForEach-Object { Write-Host "  $($_.FullName)" }
    Write-Host "Kopiere dann manuell: Copy-Item '$RepoDir\auto-memory\*' '<gewaehltes-Verzeichnis>\memory\' -Recurse -Force"
    exit 1
}

$MemoryDst = Join-Path $ProjectDirs[0].FullName "memory"
if (-not (Test-Path $MemoryDst)) {
    New-Item -ItemType Directory -Path $MemoryDst | Out-Null
}

Copy-Item (Join-Path $RepoDir "auto-memory\*") $MemoryDst -Recurse -Force
Write-Host "Auto-Memory eingespielt -> $MemoryDst"
