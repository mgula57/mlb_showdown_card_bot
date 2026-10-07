# Making Images for Your Google Drive Image Library

This guide walks through making player images for your own Google Drive image library and getting Showdown Bot to use them on your cards. It covers the whole process, from editing an image to how it will present on a card.


---

## Contents

1. [How it works](#how-it-works)
2. [Which images you need](#which-images-you-need)
3. [Setting up your canvas](#setting-up-your-canvas)
4. [Editing a Background image](#editing-a-bg-image)
5. [Editing a Cutout image](#editing-a-cut-image)
6. [Exporting](#exporting)
7. [Naming your files](#naming-your-files)
8. [Uploading and connecting your folder](#uploading-and-connecting-your-folder)
9. [Testing a card](#testing-a-card)
10. [Troubleshooting](#troubleshooting)
11. [Quick checklist](#quick-checklist)

---

## How it works

When you build a card with an automatic image, Showdown Bot looks through your image libraries in the order you set on your **Account** page. The built-in Showdown Bot library is always on the list.

For each library, the bot:

1. Finds files whose name contains the player's ID in parentheses, like `(bondsba01)`.
2. Checks that the library has **every image type the card needs** (see [Which images you need](#which-images-you-need)). If one is missing, it skips the whole library and moves to the next one.
3. Picks the best image of each type based on the year, team, and other tags in the file name.

The card shows which library the image came from, so you can tell when your own image was used.

![Image](images/ILRM-AccountPage.png)

## Which images you need

There are two image types:

| Type | What it is | Format |
|------|------------|--------|
| `BG` | The full photo: player **and** background, edge to edge. | PNG or JPG |
| `CUT` | Only the player, cut out, on a **transparent** background. Glow/Shadow NOT included (Bot handles that part) | PNG with transparency |

Each set uses a different combination:

| Set | Standard cards | Special editions and parallels |
|-----|----------------|--------------------------------|
| 2000, 2001 | `CUT` | `CUT` |
| 2002, 2003, 2004, 2005 | `BG` | `BG` + `CUT` |
| Classic, Expanded | `BG` + `CUT` | `BG` + `CUT` |

Special editions include Super Season and Cooperstown Collection. Parallels include Rainbow Foil, Gold, and Moonlight.

> **Tip:** Make both a `BG` and a `CUT` for every player. Then your image works on every set and every option, and you never fall back to another library by accident.

**[Screenshot: the same player as a BG and as a CUT, side by side]** → `images/bg-vs-cut.png`

---

## Setting up your canvas

These steps work in any editor: Photoshop, Photopea (free, in the browser), GIMP, Affinity, Procreate, and others.

### Pick a canvas size

| Option | Canvas size | What happens |
|--------|-------------|--------------|
| **Showdown Bot bleed** | **exactly** `1950 x 2730` px | **Auto-positioned per set**, the same way Showdown Bot library images are. Enables you to make one image and have it work for any style (00, 01, Expanded, etc) |
| **Card size** | `1500 x 2100` px | **Shown as is.** What you see in your editor is what's on the card, on every set. |
| **Bordered card size** | `1644 x 2244` px | Shown as is, and also fills the border on bordered cards. |

All of these are **5:7 portrait** (or very close), the same shape as the card.

### Card size: shown as is

Any image that isn't exactly `1950 x 2730` is placed on the card the same way an uploaded image is:

- It's scaled to fill the card and center-cropped if the shape isn't 5:7.
- **Bigger is fine** as long as the shape stays 5:7 (for example `3000 x 4200`). The bot scales it down.
- **Smaller images get scaled up** and can look blurry.
- On **bordered** cards, a `1500 x 2100` image sits inside the border. Use `1644 x 2244` if you want your image to run under the border too.

Compose the image exactly how you want the card to look. The bot doesn't zoom or shift it for different sets.

### Bleed size: auto-positioned per set

A `1950 x 2730` image is treated like a Showdown Bot library image. Each set crops a different window out of it, zooms in, and shifts the player into the spot that set's design expects. Special editions (like WBC and All-Star) shift it further.

Use this size if you want your images to be framed per set like the built-in library. The middle `1500 x 2100` (x `225`–`1725`, y `315`–`2415`) is the card area. The rest is bleed that some sets and bordered cards show, so fill it with real background.

Each set shows this window of a `1950 x 2730` image on a standard (non-bordered) card:

| Set | Visible window (x) | Visible window (y) |
|-----|--------------------|--------------------|
| 2000 | `200`–`1700` | `15`–`2115` |
| 2001 | `340`–`1540` | `65`–`1745` |
| 2002 | `397`–`1703` | `201`–`2029` |
| 2003 | `397`–`1703` | `301`–`2129` |
| 2004, 2005 | `225`–`1725` | `315`–`2415` |
| Classic, Expanded | `375`–`1575` | `315`–`1995` |

To make one bleed image work on every set, keep the player's face and key details inside x `397`–`1540`, y `315`–`1745`.

> **Important:** The bleed behavior only kicks in at **exactly** `1950 x 2730`. A double-size bleed canvas (`3900 x 5460`) is shown as is, bleed and all, so the player looks zoomed out. Resize to exactly `1950 x 2730` before exporting.

### Leave room for the card design

Card templates put the name, team logo, and stat chart over parts of the image, and where they go changes from set to set. Build a test card (see [Testing a card](#testing-a-card)) to see what gets covered.

**[Screenshot: 1500 x 2100 image next to the finished card, showing it's used as is]** → `images/canvas-card-size.png`

**[Screenshot: 1950 x 2730 canvas with the card area and per-set windows drawn on it]** → `images/canvas-guides-bleed.png`

---

## Editing a BG image

1. **Start with a high-resolution photo.** Portrait photos work best. Aim for at least 1500 px wide once cropped.
2. **Place and scale it** on your canvas. On a card-size canvas, frame it exactly how you want the card to look. On a bleed canvas, keep the player inside the all-sets window.
3. **Fill the whole canvas.** A `BG` must reach every edge, with no transparent or blank areas.
4. **Clean up** anything distracting: watermarks, stray logos, or busy areas behind where the name and chart will sit.
5. **Color-correct as you like.** Keep in mind that some parallels and special editions change the color or saturation on top of your image.
6. **Flatten** the image before exporting.

> If you're also making a `CUT` for this player, **save your layered file**. The `CUT` needs to line up with the `BG` pixel for pixel.

**[Screenshot: finished BG image in the editor]** → `images/bg-editing.png`

---

## Editing a CUT image

The `CUT` is layered on top of the background, and the bot adds the glow or shadow around it. It has to be clean and lined up exactly with the `BG`.

1. **Start from your BG file** (or the same photo at the same size and position). Don't move or resize the player. On Classic and Expanded cards, the `CUT` sits right on top of the `BG`, so any shift shows up as a double outline.
2. **Select the player.** Use your editor's subject-selection or quick-selection tool, then refine the edge. Pay attention to hair, cap brims, gloves, and the bat.
3. **Mask or delete the background** so everything except the player is fully transparent.
4. **Clean the edges:**
   - Remove leftover background halos (a thin line of the old background color around the player).
   - Delete stray specks and partly transparent pixels away from the player. The bot's glow outlines anything that isn't fully transparent, so stray pixels show up as glowing dots.
   - Fill in any holes inside the player.
5. **Don't add your own glow, shadow, or outline.** The bot adds these and matches them to the set. If you add your own, the card gets a doubled effect.
6. **Keep the canvas size** the same as your `BG` (`1500 x 2100`, `1644 x 2244`, or `1950 x 2730`).

**[Screenshot: CUT with the background removed, shown over a checkerboard]** → `images/cut-transparent.png`

**[Screenshot: zoomed-in edge before and after halo cleanup]** → `images/cut-edge-cleanup.png`

---

## Exporting

| | BG | CUT |
|--|----|-----|
| Format | PNG (best) or JPG | **PNG only** |
| Transparency | Not needed | **Required** |
| Size | `1500 x 2100`, `1644 x 2244`, or exactly `1950 x 2730` | Same as the matching BG |
| Color | sRGB | sRGB |

- If you export a JPG, use high quality (90 or more) to avoid blocky artifacts.
- Don't export a `CUT` as a JPG. JPGs can't be transparent, so the background turns white or black.

**[Screenshot: PNG export settings with transparency on]** → `images/export-settings.png`

---

## Naming your files

The file name is how the bot matches an image to a player and decides which image fits best, so it has to follow this format exactly:

```
{TYPE}-{YEAR}-{NAME}-({PLAYER ID})-({TEAM}).png
```

**Examples**

```
BG-2001-Bonds-(bondsba01)-(SFG).png
CUT-2001-Bonds-(bondsba01)-(SFG).png
BG-2023-Ohtani-(ohtansh01)-(LAA)-(PITCHER).png
CUT-1995-Griffey-(griffke02)-(SEA)-(DARK).png
```

### Each part of the name

| Part | Required | Rules |
|------|----------|-------|
| `TYPE` | Yes | `BG` or `CUT`, in capital letters, at the very start, followed by a dash. |
| `YEAR` | Yes | A single 4-digit season, such as `2001`. When a player has several images, the one closest to the card's year wins. Don't use a range like `2000-2004`, because the dash breaks the format. |
| `NAME` | Yes | Anything you like (just for organizing). Leave dashes out of the name to keep it easy to read. |
| `(PLAYER ID)` | **Yes** | Must be exact and in parentheses. Use the Baseball Reference ID (for example `bondsba01`, from `baseball-reference.com/players/b/bondsba01.shtml`) or the MLB ID (for example `111188`, from `mlb.com/player/barry-bonds-111188`). |
| `(TEAM)` | Recommended | The **Baseball Reference** team abbreviation, such as `SFG` (not `SF`). You can find it in team page links like `baseball-reference.com/teams/SFG/2001.shtml`. |

### Optional tags

Put any of these in parentheses after the team to target certain cards:

| Tag | Use it for |
|-----|-----------|
| `(DARK)` | Dark mode cards |
| `(POST)` | Postseason cards. These images rank **lower** on regular-season cards. |
| `(HITTER)` / `(PITCHER)` | Two-way players, to pick the hitter or pitcher version |
| `(CC)`, `(SS)`, `(ASG)`, `(RS)`, `(HOL)`, `(PM)` | A certain edition: Cooperstown Collection, Super Season, All-Star Game, Rookie Season, Holiday, Promo |

### How the best image is picked

When a player has several images of the same type, each file name gets a score:

- **Team tag:** counts double.
- **Edition tag** that matches the card's edition: counts triple.
- **Year:** the exact year gets full credit; nearby years get partial credit.
- **`(DARK)` and `(HITTER)`/`(PITCHER)`:** add points when they match the card.
- **`(POST)` or a WBC tag** on a card that isn't postseason or WBC: points taken away.

The highest score wins. If two files tie, the one with the **shorter file name** wins.

---

## Uploading and connecting your folder

1. **Create a folder** in Google Drive. A personal Google account works best, because work and school accounts often block sharing outside the organization. Folders in Shared Drives work too.
2. **Upload your images directly into that folder.** Images in subfolders are **not** searched.
3. **Share the folder** with the Showdown Bot email shown on your Account page:
   - Right-click the folder and choose **Share**.
   - Paste the bot's email.
   - Set the role to **Viewer**. Folders shared with edit access are rejected.
   - Uncheck **Notify people**, then click **Share**.
4. **Connect it** on the Account page: paste the folder link, click **Test connection**, and save.

The test shows how many images it found and how many follow the naming format. It also lists examples of files that don't match, so you can fix their names.

You can connect up to **5 folders** and drag them into the order you want them searched.

**[Screenshot: Google Drive share dialog with the bot email set to Viewer]** → `images/drive-share-dialog.png`

**[Screenshot: setup modal "Prepare folder" step]** → `images/setup-prepare.png`

**[Screenshot: connection test result with recognized and unrecognized counts]** → `images/setup-test-result.png`

### Updating images later

- **Replacing a file** with an edited version is picked up automatically on the next card build.
- **Adding new files** works right away. The image counts on your Account page only update when you connect (save) the same folder link again.
- **To revoke access**, remove the bot's email from the folder's sharing settings in Google Drive.

---

## Testing a card

1. Open the **Custom Card Builder**.
2. Enter the player and the year that matches your image.
3. Leave the image on the automatic setting. Don't upload an image or paste a link.
4. Build the card and check the image source badge. It should show your library's name.
5. Try the sets you care about. For `1950 x 2730` images, check **2001** and **Classic** (most zoomed in and shifted) and **2004** (whole card area shows).
6. If you made a `CUT`, try a **Classic** card to check that the `CUT` lines up with the `BG`.

**[Screenshot: built card with the image source badge showing the library name]** → `images/card-source-badge.png`

**[Screenshot: one image across 2000, 2001, 2004, and Classic sets]** → `images/set-comparison.png`

---

## Troubleshooting

| Problem | Likely cause |
|---------|--------------|
| The card uses the Showdown Bot image (or a silhouette) instead of mine | An image type the card needs is missing (check [the table](#which-images-you-need)), the player ID is wrong, or the image is in a subfolder. |
| Works on 2004 but not on Classic, or not with a parallel | Only a `BG` was added. Classic, special editions, and parallels also need a `CUT`. |
| A file shows up as "doesn't match the naming format" | The type isn't capital `BG`/`CUT` at the start, the year has a dash in it, or the player ID isn't in parentheses. |
| The wrong image of the player gets picked | Add the `(TEAM)` tag, use the exact year, or add `(DARK)`/edition tags. Remember that `(POST)` images rank lower on regular-season cards. |
| Player looks zoomed out or small | The image was made with bleed at a size other than exactly `1950 x 2730`, so the bleed is shown as is. |
| Head or feet cut off on some sets (bleed images only) | Key details are outside the all-sets window for `1950 x 2730` images. |
| Blurry image | The source is smaller than `1500 x 2100`. |
| White or black box behind the player | The `CUT` was saved as a JPG or without transparency. |
| Double outline on Classic or Expanded | The `CUT` doesn't line up with the `BG` (it was moved or resized). |
| Glowing dots or a ring around the player | Stray partly transparent pixels or a halo left on the `CUT`. |
| Glow or shadow looks doubled | A glow or shadow was baked into the `CUT`. Remove it and let the bot add it. |
| Image doesn't reach the border on bordered cards | `1500 x 2100` images sit inside the border. Use `1644 x 2244` to fill it. |
| "Folder not found" when connecting | The folder isn't shared with the bot's email, or your work or school account blocks outside sharing. |
| "Shared with edit access" | Change the bot's role on the folder to **Viewer**. |

---

## Quick checklist

- [ ] Canvas is `1500 x 2100` (shown as is), or exactly `1950 x 2730` (auto-positioned per set)
- [ ] Bleed images only: face and key details are inside the all-sets window
- [ ] `BG` fills the whole canvas
- [ ] `CUT` is a PNG, has a transparent background, has clean edges, and has no glow or shadow added
- [ ] `CUT` lines up with the `BG` (same size and position)
- [ ] Both `BG` and `CUT` made, if you want the image on every set and option
- [ ] Named `{TYPE}-{YEAR}-{NAME}-({PLAYER ID})-({TEAM}).png`
- [ ] Uploaded directly into the shared folder (not a subfolder)
- [ ] Folder shared with the bot as **Viewer**
- [ ] Test card built and the source badge shows your library
