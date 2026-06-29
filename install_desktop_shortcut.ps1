$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
$appScript = Join-Path $repoRoot "Codebase\session_portal.pyw"
$workingDirectory = Join-Path $repoRoot "Codebase"
$appIcon = Join-Path $repoRoot "Codebase\v2\assets\session_portal.ico"

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
if (Test-Path -LiteralPath $appIcon) {
    $shortcut.IconLocation = "$appIcon,0"
} else {
    $shortcut.IconLocation = "$($launcher.Source),0"
}
$shortcut.Save()

function Set-ShortcutAppUserModelId {
    param(
        [Parameter(Mandatory=$true)][string]$ShortcutPath,
        [Parameter(Mandatory=$true)][string]$AppUserModelId
    )

    if (-not ("SessionPortal.ShortcutProperties" -as [type])) {
        Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

namespace SessionPortal {
    [ComImport]
    [Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    public interface IPropertyStore {
        void GetCount(out uint cProps);
        void GetAt(uint iProp, out PROPERTYKEY pkey);
        void GetValue(ref PROPERTYKEY key, out PROPVARIANT pv);
        void SetValue(ref PROPERTYKEY key, ref PROPVARIANT pv);
        void Commit();
    }

    [StructLayout(LayoutKind.Sequential, Pack = 4)]
    public struct PROPERTYKEY {
        public Guid fmtid;
        public uint pid;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PROPVARIANT {
        public ushort vt;
        public ushort wReserved1;
        public ushort wReserved2;
        public ushort wReserved3;
        public IntPtr p;
        public int p2;
    }

    public static class ShortcutProperties {
        private const int GPS_READWRITE = 0x00000002;
        private const ushort VT_LPWSTR = 31;

        [DllImport("shell32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern int SHGetPropertyStoreFromParsingName(
            string pszPath,
            IntPtr pbc,
            int flags,
            ref Guid riid,
            out IPropertyStore propertyStore);

        [DllImport("ole32.dll")]
        private static extern int PropVariantClear(ref PROPVARIANT pvar);

        public static void SetAppUserModelId(string shortcutPath, string appUserModelId) {
            Guid iid = new Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99");
            IPropertyStore store;
            int hr = SHGetPropertyStoreFromParsingName(shortcutPath, IntPtr.Zero, GPS_READWRITE, ref iid, out store);
            if (hr != 0) {
                Marshal.ThrowExceptionForHR(hr);
            }

            PROPERTYKEY key = new PROPERTYKEY {
                fmtid = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"),
                pid = 5
            };
            PROPVARIANT value = new PROPVARIANT {
                vt = VT_LPWSTR,
                p = Marshal.StringToCoTaskMemUni(appUserModelId)
            };
            try {
                store.SetValue(ref key, ref value);
                store.Commit();
            } finally {
                PropVariantClear(ref value);
            }
        }
    }
}
"@
    }

    [SessionPortal.ShortcutProperties]::SetAppUserModelId($ShortcutPath, $AppUserModelId)
}

Set-ShortcutAppUserModelId -ShortcutPath $shortcutPath -AppUserModelId "SessionPortal.LocalAIWorkspace"

Write-Host "Created desktop shortcut:"
Write-Host $shortcutPath
Write-Host "Shortcut target:"
Write-Host $appScript
