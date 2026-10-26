---
name: tv-skin
description: Design, preview and switch skins for a Google TV or Android TV home screen running the Clean Your TV launcher with the TV Home kit. Use whenever the user asks for a new TV skin, theme, look, wallpaper or home screen style, describes one ("make the TV look like...", "TV skin: rainy Tokyo night"), or asks to switch, list, tweak or undo a TV skin.
---

# TV skin

The user describes a look (often loosely, sometimes by voice). Turn it into a skin, show it, push it.
Work from the root of the user's copy of the TV Home kit repo. Install this skill by copying this folder
to `~/.claude/skills/tv-skin/`.

## Tools
- `tools\skin.ps1 list | apply <name> | render <name> | new <name> [from] | reset` (PowerShell, from the repo root).
- `tools\wall.py`: wallpaper building blocks on a float canvas: `canvas, gradient, glow, stars, aurora,
  ridge, retro_sun, perspective_grid, water_reflection, shade_bottom, vignette, save`. Add a new
  primitive there when a look needs one (rain streaks, city skyline, clouds), with a one-line docstring.
- Theme keys: `.upstream\cleanyourtv\themes\README.md` (table "Keys") plus the keys in section 5 of
  `docs\IMPLEMENTATION-GUIDE.md`. Read only the rows you need.
- Python: `.upstream\cleanyourtv\tools\venv\Scripts\python.exe` (numpy and Pillow installed).
- TV: the address in `TV_HOST`. If `apply` cannot connect, the user must turn USB debugging on again
  (Settings > System > Developer options) and accept the prompt on the TV.

## Steps
1. Pick a short kebab-case name. `tools\skin.ps1 new <name> <closest existing skin>`.
2. Write `make_wallpaper.py` (1920x1080). First line is a `# Name: one-sentence description` comment,
   which `list` shows. Rules the launcher imposes: clock and greeting sit top-left, the dock across the
   lower third. Put the bright subject upper-right or centre; keep the lower 40% dark (`shade_bottom`);
   always end with `vignette` and `save` (grain prevents banding on the TV).
3. Edit `config.json`. Keep the shared block from the user's current skin (dock_apps, hidden_apps,
   live_tv_package, app_library, library_button, tile_menu, wallpaper_true_color, greeting_name,
   key_filter, screensaver_clock, auto_off_time). Keep `screensaver.jpg` out of git: it is usually a
   personal photo. Set the character keys: `background_color` (darkest colour of the wallpaper),
   `glass_style` (glass|rim), `dock_glass`, `dock_band`, `dock_opacity`, `app_glow`, `glow_style`
   (radial|horizon), `cinematic_home`, `uniform_tiles`, `focus_overshoot`, `fade_rows`. Several
   wallpapers that rotate: a `wallpapers\` folder plus `wallpaper_rotation_minutes`.
4. Render, then look at it: downscale `wallpaper.jpg` to 960x540 into `preview\` and read it. Fix
   anything that reads as clip art: hard edges where light should be soft, banding, a busy area
   behind the clock or dock. Re-render until it looks hand-made. Never show an unchecked render.
5. `tools\skin.ps1 apply <name>`, then check a real screenshot: `adb exec-out screencap -p > shot.png`.
   Show the user the preview with one line on the look.
6. Commit the skin folder (`skin <name>`).

## Rules
- Never add ads, sponsored rows or third-party content feeds.
- Use readable type; no pixel or bitmap fonts. The launcher's own type stays.
- Undo a skin: `apply` the previous one (`list` marks the current one). Back to the launcher's own look: `reset`.
