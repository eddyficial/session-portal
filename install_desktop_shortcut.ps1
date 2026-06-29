$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
$appScript = Join-Path $repoRoot "Codebase\session_portal.pyw"
$workingDirectory = Join-Path $repoRoot "Codebase"

if (-not (Test-Path -LiteralPath $appScript)) {
    throw "Could not find Session Portal launcher: $appScript. Run this script from the Session Portal repo folder."
}

$launcher = Get-Command pyw.exe -ErrorAction SilentlyContinue
if (-not $launcher) {
    $launcher = Get-Command pythonw.exe -ErrorAction SilentlyContinue
}
if (-not $launcher) {
    throw "Could not find pyw.exe or pythonw.exe. Install Python for Windows, then run this script again."
}

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Session Portal.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $launcher.Source
$shortcut.Arguments = "`"$appScript`""
$shortcut.WorkingDirectory = $workingDirectory
$shortcut.WindowStyle = 3
$shortcut.Description = "Launch Session Portal"
$shortcut.IconLocation = "$($launcher.Source),0"
$shortcut.Save()

Write-Host "Created desktop shortcut:"
Write-Host $shortcutPath
Write-Host "Shortcut target:"
Write-Host $appScript
