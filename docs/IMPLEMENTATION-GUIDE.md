# Ad-free, custom Google TV home screen: implementation guide

A complete, reproducible recipe for turning a stock Google TV / Android TV set into an ad-free TV with a custom home screen, switchable skins, a sleep timer, a night volume cap, network-wide ad blocking, a photo screensaver and a nightly auto-off. Written so that a person, or their AI assistant, can follow it start to finish.

It was built and tested on a **TCL 55" Google TV (platform "G10", Android TV 12, build STT2.230203.001)** in October 2026. Most of it applies to any Google TV or Android TV (Sony, Hisense, Philips, Chromecast with Google TV, onn, Nvidia Shield). TCL-specific quirks are marked **[TCL]**.

> Placeholders: `<TV_IP>` is your TV's local IP address, `<YOU>` your GitHub user, `<NAMES>` the names for the greeting. The scripts read the TV's address from `TV_HOST` (or `-TvHost`).

---

## 0. What you end up with

| Area | Result |
|---|---|
| Home screen | Google TV's launcher (and its "Sponsored" rows) disabled. An open-source launcher is the real Home: your apps only, two rows, no feeds, no network access. |
| Look | Skins: a theme file + a wallpaper drawn in code. Gold accent, serif clock, "Good evening, <NAMES>", date as "October 25th, Sunday", app logos cut out on uniform dark tiles. |
| Night | Sleep Timer (15 to 120 min, or a clock time), Quiet Hours (volume cap from 00:00 to 07:00), auto-standby at 02:00, still-photo screensaver. |
| Ads and tracking | ~22 bloat/tracking packages disabled (TCL ads, Samba TV ACR, TCL log uploader, silent installer). AdGuard DNS for the whole TV. |
| Security | Debugging turned off at the end, launcher has no internet permission, everything reversible. |

### How the pieces fit

```
Your PC (Windows/macOS/Linux)
 ├─ adb (Google platform-tools) ──Wi-Fi──▶ TV  (only while debugging is on)
 ├─ cleanyourtv repo (scripts: disable / restore / theme push)
 └─ your copy of this repo
      ├─ .github/workflows/build-launcher.yml  ─▶ GitHub Actions builds the APKs (no Android SDK on your PC)
      ├─ patches/tv-home.patch                 ─▶ our launcher + add-on changes, applied at build time
      ├─ skins/<name>/config.json + make_wallpaper.py
      └─ tools/  (skin.ps1, install-launcher.ps1, wall.py, wifi-reown.ps1)
TV
 ├─ Clean Your TV launcher (com.gathin.tvhome)  = Home, skins, clock screensaver, Home-button helper
 ├─ Sleep Timer add-on, Quiet Hours add-on
 └─ Private DNS → dns.adguard-dns.com
```

---

## 1. Requirements

- A Google TV / Android TV with **Android 9 or later** (the sleep features need 9+; the launcher needs 8+).
  - **Not** for LG (webOS), Samsung (Tizen) or Roku: those cannot run Android apps. For them, use the TV's own "Home Promotion"/ads toggles and set an ad-blocking DNS on the router.
- A computer on the same network. Commands below are PowerShell (Windows); macOS/Linux use the `.sh` equivalents in the upstream repo.
- A free GitHub account (for the cloud build). `gh` CLI logged in makes it easier.
- Python 3.10+ on the computer.
- 30 to 90 minutes.

---

## 2. Turn on developer mode and connect

On the TV:
1. Settings > System > About > select **Android TV OS build** 7 times ("You are now a developer").
2. Settings > System > **Developer options** > turn on **USB debugging**. If there is a **Network/Wireless debugging** switch, turn it on too.

On the computer:
```powershell
# Google's official tools (about 7 MB): https://developer.android.com/tools/releases/platform-tools
adb connect <TV_IP>:5555
adb devices -l        # the TV shows "Allow debugging?": tick "Always allow", press OK
```
- Find `<TV_IP>` in Settings > Network & Internet > your network, or Settings > System > About > Status.
- If port 5555 is refused and the TV has **Wireless debugging** with pairing: `adb pair <ip>:<pair-port>` with the 6-digit code shown, then `adb connect <ip>:<port>`.
- Check the model: `adb shell getprop ro.product.name` (the original was `G10_4K_US_NF`).

---

## 3. Debloat (disable, never uninstall)

Use **Clean Your TV** ([github.com/Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv)), which has tested package lists for 80+ TV models and safety guards (refuses to disable boot-critical packages, the HDMI input layer, Settings, or the app that owns Home; records state so `restore` puts everything back).

```powershell
# from the root of your copy of this repo; the tools expect it in .upstream\cleanyourtv
git clone https://github.com/Gathin23/cleanyourtv .upstream\cleanyourtv
cd .upstream\cleanyourtv
python -m venv tools\venv
tools\venv\Scripts\python.exe -m pip install -r tools\requirements.txt
# pick your model's list under examples\, copy it, comment out (#) anything you want to keep
tools\disable.ps1 -TvHost <TV_IP> examples\tcl-g10-google-tv\debloat.txt
```

What was disabled on the TCL G10, and why:

| Package | What it is |
|---|---|
| com.tcl.tv.plus, com.tcl.channelplus, com.tcl.tv.tclhome_passive, com.tcl.partnercustomizer, com.tcl.interactive | TCL content, FAST channels, home-screen promos |
| com.tcl.smartlink.core | contains a silent app installer |
| com.tcl.exhibit, com.tcl.esticker | store demo mode |
| com.tcl.ocean.instructions, com.tcl.repairguide, com.tcl.gamebar, com.tcl.UpdatePeripheral | e-manual, repair guide, game overlay, soundbar updater |
| android.autoinstalls.config.google.gtvpai, com.google.android.feedback, com.google.android.marvin.talkback | Google auto-installs, feedback, TalkBack |
| tv.samba.ssm.ui | **Samba TV ACR**: watches what is on screen for ad targeting |
| com.tcl.logkit | log capture and upload |
| com.google.android.apps.tv.dreamx | Google ambient-mode screensaver (replaced by our own) |
| com.tcl.guard, com.tcl.messagebox, com.tcl.usercenter, com.tcl.smartalexa | memory "cleaner", TCL notices, TCL account, Alexa link |

**Kept on purpose:** `com.tcl.tv` (Live TV and HDMI playback), `com.tcl.tvinput`, `com.tcl.ttvs` (TCL firmware updates depend on it), `com.google.android.tv.remote.service` (the remote's mic button), `com.tcl.ui_mediaCenter` (USB media), AirPlay, Chromecast built-in, Google Assistant, every streaming app.

**Unused apps:** decide from real usage, not guesses:
```powershell
adb shell dumpsys usagestats   # look for totalTimeUsed per package; 00:00 for a year = never opened
adb shell pm uninstall --user 0 <package>          # removes for this user only
adb shell cmd package install-existing <package>   # brings it back
```
Spotify can show 00:00 and still be used: Spotify Connect plays from a phone without opening the app. Ask before removing it.

Undo any list: `tools\restore.ps1 -TvHost <TV_IP> <same list> -Stock com.google.android.apps.tv.launcherx`.

---

## 4. Build the launcher in the cloud (no Android Studio needed)

Clean Your TV ships its launcher as source only. Building locally needs JDK 17 + Android SDK (~900 MB). Instead, build it in GitHub Actions from your own copy of this repo.

1. Click **Use this template** (or fork) to get `<YOU>/tv-home`. The workflow is already in `.github/workflows/build-launcher.yml`; for reference:

```yaml
name: build-launcher
on:
  workflow_dispatch:
    inputs:
      ref:
        description: Gathin23/cleanyourtv commit to build
        default: 575d73f0f30c329aa7ebaea2bc863943fd9bf7f9
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          repository: Gathin23/cleanyourtv
          ref: ${{ inputs.ref }}
      - uses: actions/checkout@v4
        with:
          path: tv-home
      - name: Apply tv-home patches
        run: for p in tv-home/patches/*.patch; do git apply "$p"; done
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "17"
      - uses: gradle/actions/setup-gradle@v4
      - name: Signing key
        env:
          KEY_B64: ${{ secrets.DEBUG_KEYSTORE_B64 }}
        run: |
          mkdir -p ~/.android
          if [ -n "$KEY_B64" ]; then echo "$KEY_B64" | base64 -d > ~/.android/debug.keystore; else
            keytool -genkeypair -keystore ~/.android/debug.keystore -storepass android -alias androiddebugkey \
              -keypass android -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US"
            mkdir -p newkey && cp ~/.android/debug.keystore newkey/; fi
      - name: Build
        working-directory: launcher
        env:
          TVHOME_KEYSTORE: /home/runner/.android/debug.keystore
        run: ./gradlew --no-daemon assembleRelease
      - name: Build add-ons
        env:
          TVHOME_KEYSTORE: /home/runner/.android/debug.keystore
        run: for a in sleep-timer quiet-hours; do (cd addons/$a && chmod +x gradlew && ./gradlew --no-daemon assembleRelease); done
      - uses: actions/upload-artifact@v4
        with: { name: sleep-timer-apk, path: addons/sleep-timer/app/build/outputs/apk/release/app-release.apk }
      - uses: actions/upload-artifact@v4
        with: { name: quiet-hours-apk, path: addons/quiet-hours/app/build/outputs/apk/release/app-release.apk }
      - uses: actions/upload-artifact@v4
        with: { name: tvhome-apk, path: launcher/app/build/outputs/apk/release/app-release.apk }
      - uses: actions/upload-artifact@v4
        if: hashFiles('newkey/debug.keystore') != ''
        with: { name: new-keystore, path: newkey/debug.keystore, retention-days: 1 }
```

2. `patches/tv-home.patch` (section 5) is already in the repo. On a fork, enable Actions in the repo's Actions tab first.
3. Run it: `gh workflow run build-launcher.yml -R <YOU>/tv-home`, then `gh run download <run-id> -R <YOU>/tv-home`.
4. **First run only:** download the `new-keystore` artifact and store it as a secret so every later build is signed with the same key (otherwise updates fail with `INSTALL_FAILED_UPDATE_INCOMPATIBLE`):
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("new-keystore\debug.keystore")) | gh secret set DEBUG_KEYSTORE_B64 -R <YOU>/tv-home
```

**Pitfalls we hit:** `android-actions/setup-android@v3` fails on current runners (the runner already has the SDK; leave it out). Gradle ignores `~/.android/debug.keystore` on the runner, which is why the patch adds an explicit `signingConfigs.debug` that reads `TVHOME_KEYSTORE`.

---

## 5. The patch (what we changed in the launcher and add-ons)

`patches/tv-home.patch` applies to cleanyourtv commit `575d73f`. Regenerate it after edits with `git -C <cleanyourtv clone> diff --output=patches/tv-home.patch`. New theme keys it adds:

| Key | Type | Effect |
|---|---|---|
| `tile_color` | `#RRGGBB` | One fill for every tile (with `uniform_tiles`). |
| `logo_cutout` | bool | Each app's icon loaded at xxxhdpi, its background cut away, logo kept in colour, cropped and scaled so every logo fills the same space. |
| `mono_icons` | bool | Same cutout, but every logo in one light tone. |
| `home_accent` | `#RRGGBB` | Accent for focus outline, greeting, date and divider. |
| `clock_serif` | bool | Clock in the system serif. |
| `greeting_below` | bool | Greeting under the clock and date instead of above. |
| `date_ordinal` | bool | Date as "October 25th, Sunday", centred vertically on the clock. |
| `screensaver_clock` | bool | `false` hides the clock and date on the screensaver. |
| `auto_off_time` | `"HH:MM"` | Every night in the 10 minutes from that time, a TV that is still on goes to standby. |
| `screensaver.jpg` | file in the skin | Still photo behind the screensaver (dimmed by `clock_wallpaper_dim`). |

Other changes in the patch: module cards (add-ons) draw like normal tiles under `logo_cutout`; the build reads a fixed signing key; Sleep Timer gets a row of clock times (22:30 to 01:00) and an icon; Quiet Hours allows 1 % volume steps and defaults to a cap of 7/100 from 00:00 to 07:00; both add-ons are restyled to the dark/gold look.

---

## 6. Make the launcher the real Home (remove Google TV's home screen)

**Why this is the hard part:** Android always gives Home to a *system* app with a higher intent priority, whatever default you pick. Google TV's launcher (`com.google.android.apps.tv.launcherx`, priority 2) and the setup wizard's `RecoveryActivity` (`com.google.android.tungsten.setupwraith`, priority 1) both outrank any installed launcher (priority 0). Both must be disabled.

**[TCL] The Wi-Fi trap:** the saved Wi-Fi network is often *owned* by the setup wizard (`setupwraith`). Disabling it deletes that network and the TV drops off Wi-Fi. Check:
```powershell
adb shell "dumpsys wifi | grep -o 'cname=[^ ]*' | sort -u"
```
If it says `setupwraith`, forgetting and re-joining in Settings does **not** help on this firmware (the re-join also goes through setupwraith). Re-save the network from the shell instead. The person who owns the network types the password locally; it never goes into a file:
```powershell
# tools\wifi-reown.ps1 does exactly this, with checks and a reconnect loop
$job = "sleep 3; cmd wifi forget-network <id>; sleep 3; cmd wifi connect-network '<SSID>' wpa2 '<PASSWORD>'"
adb shell "nohup sh -c '$job' >/dev/null 2>&1 &"   # runs on the TV; the ADB link drops for ~20 s
# afterwards the owner reads cname=android.uid.shell:2000
```
Then:
```powershell
# record + disable, with cleanyourtv's guards (FORCE_HOME because the new launcher is not Home yet)
$env:FORCE_HOME='1'; tools\disable.ps1 -TvHost <TV_IP> <list with setupwraith and launcherx>
adb shell cmd package set-home-activity --user 0 com.gathin.tvhome/.MainActivity
adb shell cmd role add-role-holder --user 0 android.app.role.HOME com.gathin.tvhome 0
adb shell "cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME | tail -1"
```
**Fallback if the Wi-Fi cannot be re-owned:** keep `launcherx` enabled, set `"stock_home_redirect": "com.google.android.apps.tv.launcherx"` in the skin and do **not** set `key_filter: false`. The launcher's accessibility helper then catches the Home button and sends Google TV's home back to yours (a split-second flash). Do not point the redirect at `setupwraith`: that loops.

---

## 7. Install the launcher, helpers and add-ons

`tools/install-launcher.ps1` automates all of this (it downloads the latest successful build from your repo; set `TV_HOME_REPO` if `gh` cannot tell which repo you are in); the steps are:
```powershell
adb install -r tvhome-apk\app-release.apk
adb install -r sleep-timer-apk\app-release.apk
adb install -r quiet-hours-apk\app-release.apk
# [TCL] TclAppBoot blocks an app's services until it may auto-start; a reinstall resets this
adb shell "for p in com.gathin.tvhome io.github.luyzfernando08.sleeptimer io.github.maxhayim.quiethours; do cmd appops set \$p AUTO_START allow; cmd appops set \$p APP_AUTO_START allow; done; appops write-settings"
# accessibility helpers: launcher Home button + auto-off, and Sleep Timer's standby action.
# Writing the list alone does not bind an updated service: clear, switch off, write back, switch on.
$svc = "com.gathin.tvhome/com.gathin.tvhome.HomeKeyService:io.github.luyzfernando08.sleeptimer/io.github.luyzfernando08.sleeptimer.SleepService"
adb shell "settings put secure enabled_accessibility_services ''; settings put secure accessibility_enabled 0; sleep 1; settings put secure enabled_accessibility_services $svc; settings put secure accessibility_enabled 1"
adb shell "dumpsys accessibility | grep -o 'label=[^,]*' | sort -u"   # expect: Home button, Sleep Timer
# screensaver = the launcher's clock/photo screensaver
adb shell "settings put secure screensaver_components com.gathin.tvhome/.ClockDream; settings put secure screensaver_enabled 1"
# Quiet Hours starts its service once its screen has been opened
adb shell am start -n io.github.maxhayim.quiethours/.MainActivity
```
The first time Home shows an add-on, the launcher asks "Show card?": answer yes.

---

## 8. Skins

A skin is a folder `skins/<name>/` with:
- `config.json`: theme keys (upstream `themes/README.md` documents ~90; section 5 adds ours),
- `make_wallpaper.py`: draws `wallpaper.jpg` (1920x1080) with `tools/wall.py`,
- optional `screensaver.jpg` (keep personal photos out of git).

Push one: `tools\skin.ps1 apply <name>` (renders the wallpaper if missing, pushes through the launcher's ThemeProvider, restarts Home). `tools\skin.ps1 list | render | new <name> <from> | reset`.

The shared block every skin carries (the final daily skin, "marble"):
```json
{
  "dock_apps": ["com.netflix.ninja","com.wbd.stream","com.disney.disneyplus","com.peacocktv.peacockandroid","com.crunchyroll.crunchyroid","com.hulu.livingroomplus"],
  "hidden_apps": ["<every launchable package you do not want on Home>"],
  "live_tv_package": "com.tcl.tv",
  "columns": 6, "rows_below_dock": 1, "show_library_pill": false,
  "uniform_tiles": true, "tile_color": "#1E1C1A", "logo_cutout": true, "always_show_names": true,
  "background_color": "#050505", "wallpaper": true, "wallpaper_true_color": true,
  "home_accent": "#D8A93E", "glass_style": "rim", "app_glow": false, "ambient_glow": false,
  "clock_serif": true, "greeting_name": "<NAMES>", "greeting_below": true, "date_ordinal": true,
  "app_library": true, "library_button": true, "tile_menu": true, "icon_only_buttons": true,
  "wifi_status_color": true, "wifi_status_warnings": true, "focus_overshoot": false,
  "advanced_effects": true, "fade_rows": true, "key_filter": false,
  "screensaver_clock": false, "clock_wallpaper_dim": 25, "home_idle_clock_minutes": 0,
  "auto_off_time": "02:00"
}
```
Design rules that made it work on a real TV (55", viewed from bed):
- Order the front row by real watch time (`dumpsys usagestats`), not by guess.
- Show **exactly** the number of apps that fill whole rows (here 12 = 6 x 2); hide the rest so no half-row peeks in. Build the hide list from `cmd package query-activities --brief -a android.intent.action.MAIN -c android.intent.category.LEANBACK_LAUNCHER`.
- Tiles must be clearly lighter than the background; keep wallpaper detail away from text lines or soften it there.
- Draw wallpaper line art at 4x and downsample (`deco_layer` in `wall.py`): soft glows look blurry on a TV, crisp hairlines do not.
- Always render, look at a real screenshot (`adb exec-out screencap -p > shot.png`), then adjust.

---

## 9. Night features

| Feature | How |
|---|---|
| Sleep Timer | Add-on tile: 15/30/60/90/120 min or a clock time; a one-minute warning offers "15 more minutes". Uses the accessibility "lock screen" action, which sends Android 9+ to standby. |
| Quiet Hours | Add-on: caps media volume (here 7/100) from 00:00 to 07:00; headphones uncapped. |
| Nightly standby | `auto_off_time` in the skin; runs inside the launcher's Home helper. |
| Screensaver | `ClockDream` + `screensaver.jpg`; starts after the TV's screensaver delay (10 min). Crop photos to 16:9 1920x1080 around the faces. |
| Idle sleep | The TV's own `sleep_timeout` (~19 min idle) still applies; playback keeps it awake. |

---

## 10. Ad blocking and other settings

```powershell
adb shell "settings put global private_dns_mode hostname; settings put global private_dns_specifier dns.adguard-dns.com"
adb shell "ping -c1 doubleclick.net"   # 127.0.0.1 = blocked; netflix.com should resolve normally
adb shell "settings put global window_animation_scale 0.5; settings put global transition_animation_scale 0.5; settings put global animator_duration_scale 0.5"
```
AdGuard DNS blocks ads/trackers in the browser and most apps; it cannot block YouTube's in-video ads.

On the TV: Settings > System > Power & Energy > **Quick Start / Instant power on** for fast power-on (uses a few watts in standby).

---

## 11. Finish: security

```powershell
adb shell "settings put global adb_wifi_enabled 0; settings put global adb_enabled 0"
```
- With debugging off, nothing can connect; turn it back on in Developer options only when changing something.
- `ro.adb.secure` should be `1` (only approved computers connect).
- The launcher declares no INTERNET permission.
- Check Settings > System > About > System update after setup. A firmware update may re-enable disabled packages: re-run the disable list and `install-launcher.ps1`.

---

## 12. Troubleshooting (every problem we actually hit)

| Symptom | Cause | Fix |
|---|---|---|
| `adb connect` refused on 5555 | debugging not on, or TV uses Wireless debugging | Section 2; pair with code. |
| Install script rolls back: Home resolves to `setupwraith/.RecoveryActivity` | setup wizard outranks the launcher | Section 6 (re-own Wi-Fi, disable setupwraith). |
| TV off Wi-Fi after disabling setupwraith | it owned the network | Re-join in Settings; then re-own with wifi-reown before disabling. |
| Home loops / task ids climb fast | `stock_home_redirect` pointed at setupwraith | Re-enable launcherx immediately; never redirect to setupwraith. |
| Home button opens Google TV while it is already showing | `key_filter: false` with the redirect method | Remove `key_filter` (redirect method), or remove Google TV entirely (section 6). |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | build signed with a different key | Store the keystore secret (section 4); one-time uninstall + install. |
| Sleep Timer says "accessibility service is off" after an update | updated service not rebound / [TCL] TclAppBoot | appops AUTO_START + clear/rewrite the accessibility list (section 7). |
| Logos blurry | icon loaded at TV density (96 px) | `logo_cutout` loads xxxhdpi and processes at 512 px. |
| A row cut off at the bottom | more apps than whole rows | Hide apps until visible = columns x rows. |
| ADB drops every evening | TCL turns Wi-Fi off in standby | Only work while the TV is on. |
| Photo of the screen looks blue | phone camera white balance under warm light | Check with `screencap`; or TV colour temperature set to Cool. |

---

## 13. Undo everything

```powershell
tools\restore.ps1 -TvHost <TV_IP> <each list you disabled> -Stock com.google.android.apps.tv.launcherx
adb shell pm enable --user 0 com.google.android.apps.tv.launcherx
adb shell pm enable --user 0 com.google.android.tungsten.setupwraith
adb uninstall com.gathin.tvhome
adb shell "settings put global private_dns_mode off"
```

---

## 14. Hand this to an AI assistant

Give the assistant this file, the repo (or the `patches/`, `tools/`, `skins/` and `.github/` folders), and this prompt:

> I want to make my Google TV ad-free with a custom home screen, following docs/IMPLEMENTATION-GUIDE.md exactly. My TV is `<model>` at `<TV_IP>`; USB debugging is on and this computer is approved. Work phase by phase (sections 2 to 11). Before each phase, say what you will change and how to undo it. Never enter my Wi-Fi password yourself: give me the wifi-reown script to run. After each visual change, take a screenshot with `adb exec-out screencap -p` and show it to me. Keep my names `<NAMES>` in the greeting. At the end, turn debugging off.

---

## 15. File map

| Path | Purpose |
|---|---|
| `.github/workflows/build-launcher.yml` | Cloud build of launcher + add-ons with the patch and fixed key |
| `patches/tv-home.patch` | All source changes (section 5) |
| `tools/install-launcher.ps1` | Install latest build, re-grant auto-start, rebind helpers, set screensaver, re-apply skin |
| `tools/skin.ps1` | List, render, create, apply, reset skins |
| `tools/wall.py` | Wallpaper drawing toolkit (gradients, glows, stars, aurora, ridges, crisp line art at 4x) |
| `tools/wifi-reown.ps1` | Moves the saved Wi-Fi off the setup wizard (asks for the password locally) |
| `skins/*` | marble (daily), cinema, black, midnight, synthwave, aurora |
| `skill/SKILL.md` | Claude skill "tv-skin": describe a look, get a skin |
| `docs/` | This guide and the plain-language explainer |

Credits: [Clean Your TV](https://github.com/Gathin23/cleanyourtv) (launcher, scripts, model lists, add-ons by its community), [AdGuard DNS](https://adguard-dns.io), Google platform-tools.
