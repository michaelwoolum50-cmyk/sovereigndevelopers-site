# App Showcase — the repeatable per-app pattern

Michael's order (2026-09-25): every app on sovereigndevelopers.org gets the SAME entry —
app icon, 3–4 interior walkthrough screenshots exactly as a user sees them, a short
description, and a download button hot-linked to the Play Store listing.

## The pattern (no deviations)

1. **Icon** — `static/apps/<slug>-icon.png`, 512×512 PNG.
   The real product icon. No stretching, no clipped edges, no text baked over UI,
   no tight face-crops. If the build's icon needs framing, frame it on dark `#070d14`
   with rounded corners — never squash it.
2. **Screenshots** — `static/apps/<slug>-shot-1.jpg` … `-shot-4.jpg`, 3–4 of them.
   Real screens captured during Boss's device walk, exactly as a user sees them.
   NEVER: photos of upload dialogs, browser chrome, instructional text baked in
   ("GOOGLE PLAY STORE LISTING 1024x500"), AI mockups passed off as screens.
3. **Description** — 2–4 sentences, plain words. What it is, what the user does,
   what makes it worth downloading.
4. **Download button** — hot link to the Play Store listing. Until the listing is
   public, the button renders as a disabled "Coming soon to Google Play".

## How to ship a new app entry

```bash
cd /path/to/sovereigndevelopers-site
# 1. drop assets in place
#    static/apps/<slug>-icon.png  (512x512)
#    static/apps/<slug>-shot-{1..4}.jpg
# 2. write the manifest
cp showcase/_manifest-example.json showcase/<slug>.json   # then fill it in
# 3. generate the page
python3 showcase/make-showcase.py showcase/<slug>.json
# 4. commit + push to main (GitHub Pages publishes it)
```

Manifest fields: `slug`, `name`, `tagline`, `description`, `icon`, `screenshots`
(list of `{src, caption}`), `play_url` (null until public), `status`
(`live` | `coming_soon` | `early_access`).

## Pipeline integration

- **At submission:** the showcase entry is STAGED — icon + description + screenshots
  from the device walk, button in "coming soon" state, page generated but Play link empty.
- **When the Play listing goes public:** set `play_url`, flip `status` to `live`,
  regenerate, push. The button goes live the same day.
- **Screenshots come from Boss's walk** — that is the standing source. No stock
  art, no AI filler.

## What was cleaned (2026-09-25 audit)

- `forever-us-icon.png` → replaced with the real 512×512 build icon (was a sloppy
  crop with clipped text).
- `forever-us-infinity-logo.jpg` → was a PHOTO OF A PHONE showing an upload
  dialog ("Apply/Cancel/Upload" + app dock). Rebuilt as a clean render of the
  real icon art.
- `ibot-social-icon.jpg` → was a tight face-crop with the head clipped at the
  edges. Reframed as a proper 512×512 icon with padding and rounded corners.
- `full-metal-bookshelf-banner.jpg` → had "GOOGLE PLAY STORE LISTING 1024x500
  pixels" instructional text baked across the top. Cropped out.
- `multimind-journal-library.jpg` → had browser chrome at the top, including a
  visible "Base44 Superag..." tab. Cropped out; now pure app UI.
- `titan-chip-icon.png` → magenta placeholder background replaced with deep navy.
- 19 byte-duplicate image files deleted (same image saved under 2–4 names).
