# Switch, render and create skins for the TV's launcher.
#
#   tools\skin.ps1 list                 skins in skins\, the one on the TV marked with *
#   tools\skin.ps1 apply <name>         render its wallpaper if missing, push it to the TV, restart Home
#   tools\skin.ps1 render <name>        re-run skins\<name>\make_wallpaper.py
#   tools\skin.ps1 new <name> [from]    copy a skin (default: midnight) as a starting point
#   tools\skin.ps1 reset                back to the launcher's built-in look
param(
    [Parameter(Position = 0)][ValidateSet('list', 'apply', 'render', 'new', 'reset')][string]$Cmd = 'list',
    [Parameter(Position = 1)][string]$Name,
    [Parameter(Position = 2)][string]$From = 'midnight',
    [string]$TvHost = $(if ($env:TV_HOST) { $env:TV_HOST } else { throw 'Set TV_HOST to the TV''s IP address or pass -TvHost' })
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$skins = Join-Path $root 'skins'
$up = Join-Path $root '.upstream\cleanyourtv'
$py = Join-Path $up 'tools\venv\Scripts\python.exe'
$current = Join-Path $skins '.current'

function Render($n) {
    $dir = Join-Path $skins $n
    if (-not (Test-Path "$dir\make_wallpaper.py")) { return }
    & $py "$dir\make_wallpaper.py"
    if ($LASTEXITCODE -ne 0) { throw "make_wallpaper.py failed for $n" }
}

switch ($Cmd) {
    'list' {
        $on = if (Test-Path $current) { (Get-Content $current).Trim() } else { '' }
        Get-ChildItem $skins -Directory | ForEach-Object {
            $note = (Get-Content "$($_.FullName)\make_wallpaper.py" -ErrorAction SilentlyContinue | Where-Object { $_ -match '^# ' } | Select-Object -First 1) -replace '^# ', ''
            '{0} {1,-14} {2}' -f $(if ($_.Name -eq $on) { '*' } else { ' ' }), $_.Name, $note
        }
    }
    'render' { Render $Name; "rendered $Name" }
    'apply' {
        $dir = Join-Path $skins $Name
        if (-not (Test-Path "$dir\config.json")) { throw "no skin named $Name" }
        Get-Content "$dir\config.json" -Raw | ConvertFrom-Json | Out-Null  # a broken file would be ignored by the launcher
        if (-not (Test-Path "$dir\wallpaper.jpg")) { Render $Name }
        # Push only what the launcher reads, never the generator script.
        $stage = Join-Path $env:TEMP "tvskin-$Name"
        Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
        New-Item -ItemType Directory $stage | Out-Null
        Copy-Item "$dir\config.json" $stage
        foreach ($f in 'wallpaper.jpg', 'wallpapers', 'screensaver.jpg') { if (Test-Path "$dir\$f") { Copy-Item "$dir\$f" $stage -Recurse } }
        & (Join-Path $up 'tools\theme.ps1') -TvHost $TvHost $stage
        Set-Content -Encoding ascii $current $Name
        "skin $Name is on the TV"
    }
    'new' {
        $dir = Join-Path $skins $Name
        if (Test-Path $dir) { throw "$Name already exists" }
        Copy-Item (Join-Path $skins $From) $dir -Recurse
        Remove-Item "$dir\wallpaper.jpg" -ErrorAction SilentlyContinue
        "created skins\$Name from $From; edit config.json and make_wallpaper.py, then: tools\skin.ps1 apply $Name"
    }
    'reset' {
        & (Join-Path $up 'tools\theme.ps1') -TvHost $TvHost -Reset
        Remove-Item $current -ErrorAction SilentlyContinue
        'built-in look restored'
    }
}
