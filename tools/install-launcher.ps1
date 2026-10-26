# Put the latest cloud-built launcher on the TV and restore everything around it: the Home button
# helper, the clock screensaver and the current skin. Safe to re-run.
#
#   tools\install-launcher.ps1 [-RunId <id>]   default: the latest successful build-launcher run
param(
    [string]$RunId = '',
    [string]$Repo = $(if ($env:TV_HOME_REPO) { $env:TV_HOME_REPO } else { gh repo view --json nameWithOwner -q .nameWithOwner }),
    [string]$TvHost = $(if ($env:TV_HOST) { $env:TV_HOST } else { throw 'Set TV_HOST to the TV''s IP address or pass -TvHost' })
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$adb = Join-Path $root '.upstream\platform-tools\adb.exe'
$out = Join-Path $root '.upstream\build'
$pkg = 'com.gathin.tvhome'

if (-not $RunId) {
    $RunId = gh run list -R $Repo -w build-launcher.yml -s success -L 1 --json databaseId --jq '.[0].databaseId'
}
Remove-Item $out -Recurse -Force -ErrorAction SilentlyContinue
gh run download $RunId -R $Repo -n tvhome-apk -D "$out\tvhome-apk"
$apk = "$out\tvhome-apk\app-release.apk"

& $adb connect "${TvHost}:5555" | Out-Null
$ErrorActionPreference = 'Continue'
$res = (& $adb -s "${TvHost}:5555" install -r $apk 2>&1) -join "`n"
if ($res -match 'UPDATE_INCOMPATIBLE') {
    # Signed with another key (builds before the key was pinned): a clean install is the only way.
    & $adb -s "${TvHost}:5555" uninstall $pkg | Out-Null
    $res = (& $adb -s "${TvHost}:5555" install $apk 2>&1) -join "`n"
}
$ErrorActionPreference = 'Stop'
if ($res -notmatch 'Success') { throw "install failed: $res" }

# Home helper (Google TV's launcher outranks this one; the helper sends Home here), TclAppBoot auto-start,
# and the black clock screensaver. An uninstall drops all three.
$svc = "$pkg/$pkg.HomeKeyService"
# Android clears the accessibility list a few seconds after an install, so wait before writing it.
& $adb -s "${TvHost}:5555" shell ("sleep 6; cmd appops set $pkg AUTO_START allow 2>/dev/null; cmd appops set $pkg APP_AUTO_START allow 2>/dev/null; appops write-settings 2>/dev/null; " +
    "s=`$(settings get secure enabled_accessibility_services); case `"`$s`" in *HomeKeyService*) ;; null|'') settings put secure enabled_accessibility_services $svc ;; *) settings put secure enabled_accessibility_services `"`$s:$svc`" ;; esac; " +
    "settings put secure accessibility_enabled 1; settings put secure screensaver_components $pkg/.ClockDream; settings put secure screensaver_enabled 1")

# Add-ons from the same run: Sleep Timer (its own accessibility helper) and Quiet Hours (starts from its screen).
foreach ($n in 'sleep-timer-apk', 'quiet-hours-apk') {
    gh run download $RunId -R $Repo -n $n -D "$out\$n"
    & $adb -s "${TvHost}:5555" install -r "$out\$n\app-release.apk" | Out-Null
}
$sleep = 'io.github.luyzfernando08.sleeptimer/io.github.luyzfernando08.sleeptimer.SleepService'
# Writing the list alone doesn't bind a new helper: clear it, switch accessibility off, then write it back.
& $adb -s "${TvHost}:5555" shell ("a=`$(settings get secure enabled_accessibility_services); case `"`$a`" in *SleepService*) ;; *) a=`"`$a:$sleep`" ;; esac; " +
    "settings put secure enabled_accessibility_services ''; settings put secure accessibility_enabled 0; sleep 1; " +
    "settings put secure enabled_accessibility_services `"`$a`"; settings put secure accessibility_enabled 1; " +
    "am start -n io.github.maxhayim.quiethours/.MainActivity >/dev/null; sleep 3; input keyevent KEYCODE_HOME")

$current = Join-Path $root 'skins\.current'
$skin = if (Test-Path $current) { (Get-Content $current).Trim() } else { 'black' }
& (Join-Path $PSScriptRoot 'skin.ps1') apply $skin -TvHost $TvHost
# TCL's TclAppBoot blocks an app's services until it may auto-start; a reinstall drops that, so grant it again.
& $adb -s "${TvHost}:5555" shell 'for p in io.github.luyzfernando08.sleeptimer io.github.maxhayim.quiethours; do cmd appops set $p AUTO_START allow 2>/dev/null; cmd appops set $p APP_AUTO_START allow 2>/dev/null; done; appops write-settings' | Out-Null
# An updated helper stays listed but unbound until the list changes: rebind both once everything is in place.
& $adb -s "${TvHost}:5555" shell ("a=`$(settings get secure enabled_accessibility_services); settings put secure enabled_accessibility_services ''; " +
    "settings put secure accessibility_enabled 0; sleep 1; settings put secure enabled_accessibility_services `"`$a`"; settings put secure accessibility_enabled 1; sleep 3")
$bound = (& $adb -s "${TvHost}:5555" shell "dumpsys accessibility | grep -o 'label=[^,]*' | sort -u") -join ' '
if ($bound -notmatch 'Home button' -or $bound -notmatch 'Sleep Timer') { throw "a helper is not running ($bound): re-run this script." }
"launcher from run $RunId installed, skin $skin applied, Home helper on"
