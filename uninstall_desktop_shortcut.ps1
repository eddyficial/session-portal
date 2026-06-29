param(
    [switch]$RemoveLocalData
)

$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Session Portal.lnk"

if (Test-Path -LiteralPath $shortcutPath) {
    Remove-Item -LiteralPath $shortcutPath -Force
    Write-Host "Removed desktop shortcut:"
    Write-Host $shortcutPath
} else {
    Write-Host "Desktop shortcut was not found:"
    Write-Host $shortcutPath
}

if ($RemoveLocalData) {
    $localFiles = @(
        (Join-Path $repoRoot "Codebase\v2\settings.json"),
        (Join-Path $repoRoot "Codebase\v2\renames.json"),
        (Join-Path $repoRoot "Codebase\settings.json"),
        (Join-Path $repoRoot "Codebase\renames.json")
    )

    foreach ($file in $localFiles) {
        if (Test-Path -LiteralPath $file) {
            Remove-Item -LiteralPath $file -Force
            Write-Host "Removed local app data:"
            Write-Host $file
        }
    }

    $trashDir = Join-Path $repoRoot "Codebase\v2\.trash"
    if (Test-Path -LiteralPath $trashDir) {
        Remove-Item -LiteralPath $trashDir -Recurse -Force
        Write-Host "Removed local app trash:"
        Write-Host $trashDir
    }
}

Write-Host "Session Portal uninstall helper finished."
