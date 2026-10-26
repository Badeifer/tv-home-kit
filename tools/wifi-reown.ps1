# Re-save the TV's Wi-Fi so it belongs to the shell instead of Google's setup wizard (setupwraith).
# After this, setupwraith and Google TV's launcher can be disabled without the TV losing Wi-Fi.
#
# Run it yourself: it asks for the Wi-Fi password, which stays on this PC and the TV, never in a file or log.
#   tools\wifi-reown.ps1
# If anything goes wrong the TV is only off Wi-Fi: join the network again in Settings > Network & Internet.
param([string]$TvHost = $(if ($env:TV_HOST) { $env:TV_HOST } else { throw 'Set TV_HOST to the TV''s IP address or pass -TvHost' }))
$ErrorActionPreference = 'Stop'
$adb = Join-Path (Split-Path -Parent $PSScriptRoot) '.upstream\platform-tools\adb.exe'
$t = "${TvHost}:5555"

& $adb connect $t | Out-Null
$status = (& $adb -s $t shell 'cmd wifi status') -join "`n"
if ($status -notmatch 'connected to "([^"]+)"') { throw 'the TV is not on Wi-Fi or not reachable; turn it on and check USB debugging' }
$ssid = $Matches[1]
$owner = (& $adb -s $t shell "dumpsys wifi | grep -o 'cname=[^ ]*' | sort -u") -join ' '
if ($owner -notmatch 'setupwraith') { "Wi-Fi already belongs to $owner; nothing to do."; exit 0 }
$id = ((& $adb -s $t shell 'cmd wifi list-networks') | Where-Object { $_ -match "^\s*(\d+)\s+$([regex]::Escape($ssid))\b" } | Select-Object -First 1) -replace '^\s*(\d+).*', '$1'
if ($id -notmatch '^\d+$') { throw 'could not find the saved network id' }

$sec = Read-Host "Wi-Fi password for $ssid" -AsSecureString
$pw = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
$q = { param($s) "'" + ($s -replace "'", "'\''") + "'" }   # shell single-quote
# Runs on the TV in the background: forgetting the network cuts this ADB connection.
$job = "sleep 3; cmd wifi forget-network $id; sleep 3; cmd wifi connect-network $(& $q $ssid) wpa2 $(& $q $pw)"
& $adb -s $t shell "nohup sh -c $(& $q $job) >/dev/null 2>&1 &" | Out-Null
$pw = $null

'Re-saving the network; the TV drops off Wi-Fi for about 20 seconds...'
Start-Sleep 25
$back = $false
foreach ($i in 1..12) {
    & $adb disconnect $t 2>$null | Out-Null
    if ((& $adb connect $t) -match 'connected') { $back = $true; break }
    Start-Sleep 5
}
if (-not $back) { throw 'the TV did not come back on Wi-Fi: join it again in Settings > Network & Internet' }
Start-Sleep 3
$owner = (& $adb -s $t shell "dumpsys wifi | grep -o 'cname=[^ ]*' | sort -u") -join ' '
if ($owner -match 'setupwraith') { "Still owned by setupwraith ($owner). Tell Claude." } else { "Done: Wi-Fi now belongs to $owner. Tell Claude to finish the Google TV removal." }
