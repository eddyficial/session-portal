param(
    [switch]$SkipDependencies,
    [switch]$Launch
)

$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
$requirements = Join-Path $repoRoot "Codebase\requirements.txt"
$shortcutInstaller = Join-Path $repoRoot "install_desktop_shortcut.ps1"

if (-not (Test-Path -LiteralPath $requirements)) {
    throw "Could not find requirements file: $requirements. Run this script from the Session Portal repo folder."
}

if (-not (Test-Path -LiteralPath $shortcutInstaller)) {
    throw "Could not find shortcut installer: $shortcutInstaller"
}

if (-not $SkipDependencies) {
    Write-Host "Installing Session Portal dependencies..."
    py -3 -m pip install -r $requirements
}

Write-Host "Creating Desktop shortcut..."
& $shortcutInstaller

if ($Launch) {
    $launcher = Join-Path $repoRoot "Codebase\session_portal.pyw"
    Write-Host "Launching Session Portal..."
    Start-Process -FilePath "pyw" -ArgumentList @("-3", "`"$launcher`"") -WorkingDirectory (Join-Path $repoRoot "Codebase") -WindowStyle Hidden
}

Write-Host ""
Write-Host "Session Portal is installed."
Write-Host "Use the Desktop shortcut named 'Session Portal' for future launches."
