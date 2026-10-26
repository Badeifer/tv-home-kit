# What this does to your TV, in plain English

## The short version

A stock Google TV opens on Google's home screen, which is mostly advertising: "Sponsored" rows, shows from apps you don't pay for, TCL's own channels, and software quietly reporting what you watch. This kit replaces all of that with a home screen that only shows **your** apps, looks the way you want, and does a few useful things at night. Nothing was physically changed, nothing was paid for, and every step can be undone.

## What changed, and why it matters

### 1. The ads and the snooping are gone
- **Google TV's home screen is switched off.** It is the source of the "Sponsored" rows and recommendations. It's still on the TV, just turned off, so it can come back if you ever want it.
- **About 20 built-in extras are switched off**, the ones that pushed ads and TCL content or sent data back. One of them, Samba TV, literally looks at what's on your screen to sell ads. Apps you have never opened can be removed too, after checking the TV's own usage records.
- **An ad blocker for the whole TV.** The TV now looks up websites through a free filtering service (AdGuard). Requests to known ad and tracking companies simply go nowhere. It works in the browser and most apps. It can't remove the ads inside YouTube videos, because those come from the same place as the videos.

### 2. A home screen that's yours
- **Only the apps you use,** in two neat rows of six, in the order you actually watch them. Everything else is tucked behind the grid button at the top, not deleted.
- **One look across every tile:** dark tiles, each app's real logo, a gold outline on the one you've selected.
- **A greeting and clock:** "Good evening" with your names, a classic-style clock, and the date written as "October 25th, Sunday".
- **Skins:** the whole look can be swapped like a phone wallpaper. The daily one is black marble with gold veins. Others are ready (a gold "cinema", stars and aurora, pure black). You can also describe a new look to Claude ("make the TV look like a rainy night in Tokyo") and it builds one.

### 3. Made for falling asleep
- **Sleep Timer** (on the home screen): turn the TV off in 15, 30, 60, 90 or 120 minutes, or at a set time (10:30 PM to 1 AM). A minute before, it asks if you want 15 more minutes.
- **Quiet Hours:** from midnight to 7 AM, the volume can't go above 7, so a loud ad or show can't wake you up.
- **Automatic off at 2 AM** if the TV is still on.
- **Screensaver:** your photo, full screen and still, slightly dimmed, with no clock on top.

### 4. Safe
- The special "developer" access used to make the changes is **turned off again**, so nothing on your network can connect to the TV.
- The new home screen app has **no internet access at all**. It can't send anything anywhere.
- Every change is recorded and can be reversed.

## How it was done (the idea, not the commands)

1. **Developer mode.** Every Android-based TV has a hidden "developer" switch. With it on, a computer on the same Wi-Fi can send the TV instructions, after you approve it on screen once.
2. **Switching things off instead of deleting them.** Android lets you disable built-in apps. They stop running and disappear, but they're still there to switch back on. This is why everything is reversible.
3. **A free, open-source home screen.** A project called *Clean Your TV* publishes a replacement home screen for Android TVs. This kit adds its own tweaks to it (the gold accents, the logo style, the date format, the 2 AM switch-off, the photo screensaver) and GitHub builds it in the cloud, so the computer didn't need any big software installed.
4. **The tricky part.** Google's built-in apps always get first claim on the Home button, so they had to be turned off. On this TCL TV, the Wi-Fi connection had been saved by Google's setup wizard, and switching that wizard off would have erased the Wi-Fi. So the Wi-Fi was saved again in a different way first (the owner types the password on the PC; it never goes into a file), and then the Google apps could be switched off safely.
5. **Design by checking the real thing.** Each change was photographed straight off the TV's screen and adjusted until it looked right from the bed: no half-hidden rows, crisp logos, text that stays readable over the background.

## Living with it

- **Day to day:** nothing to do. Press Home and you're on your screen.
- **To change something** (a new skin, a different app order), turn debugging back on: Settings > System > Developer options > USB debugging. Then ask Claude. Turn it off again afterwards.
- **If a TV update ever brings Google's screen back,** turn debugging on and ask Claude to "re-run the TV setup". Everything needed is saved.
- **To undo everything:** ask Claude to "restore the TV to stock". The exact steps are in the technical guide.

## Good to know

- This works on TVs that run Google TV or Android TV (TCL, Sony, Hisense, Philips, Chromecast). It won't work on LG, Samsung or Roku, because they run different systems. On those, the best you can do is turn off "Home Promotion" in their settings and use an ad-blocking setting on your router.
- Want to do this yourself? Use this repository as a template. The technical guide (IMPLEMENTATION-GUIDE.md) has a ready-made message to paste into your own AI assistant.
