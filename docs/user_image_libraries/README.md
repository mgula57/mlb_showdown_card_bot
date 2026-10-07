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

![Image](images/ILRM-BgVsCut.png)

---

## Setting up your canvas

These steps work in any editor: Photoshop, Photopea (free, in the browser), GIMP, Affinity, Procreate, and others.

> **Photoshop template:** [`templates/ShowdownBotPlayerImageTemplate.psd`](templates/ShowdownBotPlayerImageTemplate.psd) already has steps 1, 2, and 4 done: a `1950 x 2730` canvas, the guides, and an example player with `BG` and `CUT` layers. Photopea can open it too. If you use it, duplicate the example group, swap in your photo, rename the layers, and start at [Step 3](#step-3-frame-the-player).

### Step 1: Pick a canvas size

| Option | Canvas size | What happens |
|--------|-------------|--------------|
| **Showdown Bot bleed (recommended)** | **exactly** `1950 x 2730` px | **Auto-positioned per set**, the same way Showdown Bot library images are. Make one image and it works for every set (2000, 2001, Expanded, etc.). |
| **Card size** | `1500 x 2100` px | **Shown as is.** What you see in your editor is what's on the card, on every set. |
| **Bordered card size** | `1644 x 2244` px | Shown as is, and also fills the border on bordered cards. |

All of these are **5:7 portrait** (or very close), the same shape as the card.

**Bleed size.** The bot crops a different window out of the image for each set, zooms in, and shifts the player into the spot that set's design expects. Special editions (like WBC and All-Star) shift it further. Steps 2 and 3 set your image up for this.

> **Important:** The bleed behavior only kicks in at **exactly** `1950 x 2730`. A double-size bleed canvas (`3900 x 5460`) is shown as is, bleed and all, so the player looks zoomed out. Resize to exactly `1950 x 2730` before exporting.

**Card size.** The image is placed on the card the same way an uploaded image is. The bot doesn't zoom or shift it for different sets.

- It's scaled to fill the card and center-cropped if the shape isn't 5:7.
- **Bigger is fine** as long as the shape stays 5:7 (for example `3000 x 4200`). The bot scales it down. **Smaller images get scaled up** and can look blurry.
- On **bordered** cards, a `1500 x 2100` image sits inside the border. Use `1644 x 2244` if you want your image to run under the border too.

If you're using card size, skip Steps 2 and 3. Frame the image exactly how you want the card to look, then go to [Step 4](#step-4-set-up-bg-and-cut-layers).

### Step 2: Add guides

![Photoshop setup for a 1950 x 2730 bleed image](images/ILRM-Photoshop.png)

Add guides that mark the `1500 x 2100` card area inside the bleed canvas (the red arrows above). In Photoshop, use **View > Guides > New Guide**.

- Vertical guides at x `225` and x `1725`.
- Horizontal guides at y `315` and y `2415`.
- A center guide at x `975` to line up the player.

Everything outside the guides is bleed. Keep the photo going past the guides all the way to the canvas edge, so sets and bordered cards that show part of the bleed get real background instead of empty space.

### Step 3: Frame the player

Frame every bleed image the same way, and let the bot handle each set:

- **Head:** just inside the **top** guide (y `315`), centered on the middle guide (x `975`).
- **Feet:** on the **bottom** guide (y `2415`).
- **Body:** centered left to right, inside the side guides.

That's how the Showdown Bot library images are framed, and each set's crop is built around it. Some sets crop the lower legs on purpose, so don't shrink the player to fit every set. Stick to the framing above.

![One BG and CUT pair turned into a 2004 Super Season card and a 2001 card](images/ILRM-PhotoshopToCards.png)

This one `BG` + `CUT` pair works for every set:

- **2004 Super Season (front):** the bot shows the whole card area, with the `CUT` layered over the `BG` photo. The player runs from just under the top edge down to the chart.
- **2001 (back):** the bot uses only the `CUT`, zooms in on the upper body, and puts the set's own background behind it.

Card templates also put the name, team logo, and stat chart over parts of the image, and where they go changes from set to set. Build a test card (see [Testing a card](#testing-a-card)) to see what gets covered.

<details>
<summary>Reference: what each set shows of a 1950 x 2730 image</summary>

On a standard (non-bordered) card:

| Set | Visible window (x) | Visible window (y) |
|-----|--------------------|--------------------|
| 2000 | `200`–`1700` | `15`–`2115` |
| 2001 | `340`–`1540` | `65`–`1745` |
| 2002 | `397`–`1703` | `201`–`2029` |
| 2003 | `397`–`1703` | `301`–`2129` |
| 2004, 2005 | `225`–`1725` | `315`–`2415` |
| Classic, Expanded | `375`–`1575` | `315`–`1995` |

</details>

### Step 4: Set up BG and CUT layers

If you're making both a `BG` and a `CUT` (recommended), put both in the same file so they line up exactly. In the Photoshop screenshot in [Step 2](#step-2-add-guides), the yellow arrows show how:

- **One group per player** (here, `EXAMPLE: Barry Bonds 1990`) holds two copies of the same photo layer, at the same size and position.
- **CUT layer:** has a layer mask that shows only the player (the white silhouette in the mask thumbnail).
- **BG layer:** has the same mask **turned off** (the red X on the mask thumbnail), so the full photo shows. To turn a mask off or back on, Shift-click its thumbnail.
- **Layer names** match the file names they export to, like `CUT-1990-Bonds-(bondsba01)-(PIT)` and `BG-1990-Bonds-(bondsba01)-(PIT)`. Photoshop's layer export options use the layer name as the file name (see [Naming your files](#naming-your-files)).

The next two sections cover editing each layer.

---

## Editing a BG image

1. **Start with a high-resolution photo.** Portrait photos work best. Aim for at least 1500 px wide once cropped.
2. **Place and scale it** on your canvas. On a card-size canvas, frame it exactly how you want the card to look. On a bleed canvas, put the head near the top guide, centered, and the feet on the bottom guide (see [Step 3](#step-3-frame-the-player)).
3. **Fill the whole canvas.** A `BG` must reach every edge, with no transparent or blank areas. If you need to fill area, many modern photo editing tools have generative/content aware fills that can help.
4. **Clean up** anything distracting: watermarks, stray logos, or busy areas behind where the name and chart will sit.
5. **Color-correct as you like.** Keep in mind that some parallels and special editions change the color or saturation on top of your image.
6. **Flatten** the image before exporting.

> If you're also making a `CUT` for this player, **save your layered file**. The `CUT` needs to line up with the `BG` pixel for pixel.

---

## Editing a CUT image

The `CUT` is layered on top of the background, and the bot adds the glow or shadow around it. It has to be clean and lined up exactly with the `BG`.

1. **Start from your BG file** (or the same photo at the same size and position). Don't move or resize the player. On Classic and Expanded cards, the `CUT` sits right on top of the `BG`, so any shift shows up as a double outline.
2. **Select the player.** Use your editor's subject-selection or quick-selection tool, then refine the edge. Pay attention to hair, cap brims, gloves, and the bat.
3. **Mask or delete the background** so everything except the player is fully transparent. A layer mask works well, because you can reuse the same layer for the `BG` with the mask turned off (see [Step 4](#step-4-set-up-bg-and-cut-layers)).
4. **Clean the edges:**
   - Remove leftover background halos (a thin line of the old background color around the player).
   - Delete stray specks and partly transparent pixels away from the player. The bot's glow outlines anything that isn't fully transparent, so stray pixels show up as glowing dots.
   - Fill in any holes inside the player.
5. **Don't add your own glow, shadow, or outline.** The bot adds these and matches them to the set. If you add your own, the card gets a doubled effect.
6. **Keep the canvas size** the same as your `BG` (`1500 x 2100`, `1644 x 2244`, or `1950 x 2730`).

---

## Exporting

| | BG | CUT |
|--|----|-----|
| Format | PNG (best) or JPG | **PNG only** |
| Transparency | Not needed | **Required** |
| Size | `1500 x 2100`, `1644 x 2244`, or exactly `1950 x 2730` | Same as the matching BG |
| Color | sRGB | sRGB |

- If you export a JPG, use high quality (90 or more) to avoid blocky artifacts.
- After exporting, check that each file is still the full canvas size. Some layer export options trim transparent edges, which shrinks a `CUT` to the player's outline. A trimmed `CUT` is treated as card size and won't line up with the `BG`.
- Don't export a `CUT` as a JPG. JPGs can't be transparent, so the background turns white or black.

## Naming your files

The file name is how the bot matches an image to a player and decides which image fits best, **so it has to follow this format exactly**:

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

- **Team tag:** counts 2x.
- **Edition tag** that matches the card's edition: counts 3x.
- **Year:** the exact year gets full credit; nearby years get partial credit.
- **`(DARK)` and `(HITTER)`/`(PITCHER)`:** add points when they match the card.
- **`(POST)` or a WBC tag** on a card that isn't postseason or WBC: points taken away.

The highest score wins. If two files tie, the one with the **shorter file name** wins.

---

## Uploading and connecting your folder

1. **Create a folder** in Google Drive. A personal Google account works best, because work and school accounts often block sharing outside the organization. Folders in Shared Drives work too.
2. **Upload your images directly into that folder.** Images in subfolders are **not** searched.
3. **Share the folder** with the Showdown Bot email shown on your [Account](https://www.showdownbot.com/account) page:
   - Right-click the folder and choose **Share**.
   - Paste the bot's email: `showdown-bot-user-images@showdown-bot-315820.iam.gserviceaccount.com`
   - Set the role to **Viewer**. Folders shared with edit access are rejected.
   - Uncheck **Notify people**, then click **Share**.
4. **Connect it** on the Account page: paste the folder link, click **Test connection**, and save.

The test shows how many images it found and how many follow the naming format. It also lists examples of files that don't match, so you can fix their names.

You can connect up to **5 folders** and drag them into the order you want them searched.

![Image](images/ILRM-GdriveShare.png)

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

![Image](images/ILRM-FinalShowdownImage.png)

---

## Troubleshooting

| Problem | Likely cause |
|---------|--------------|
| The card uses the Showdown Bot image (or a silhouette) instead of mine | An image type the card needs is missing (check [the table](#which-images-you-need)), the player ID is wrong, or the image is in a subfolder. |
| Works on 2004 but not on Classic, or not with a parallel | Only a `BG` was added. Classic, special editions, and parallels also need a `CUT`. |
| A file shows up as "doesn't match the naming format" | The type isn't capital `BG`/`CUT` at the start, the year has a dash in it, or the player ID isn't in parentheses. |
| The wrong image of the player gets picked | Add the `(TEAM)` tag, use the exact year, or add `(DARK)`/edition tags. Remember that `(POST)` images rank lower on regular-season cards. |
| Player looks zoomed out or small | The image was made with bleed at a size other than exactly `1950 x 2730`, so the bleed is shown as is. |
| Player too high, too low, or head cut off on some sets (bleed images only) | The player isn't framed with the head at the top guide and the feet at the bottom guide. Some sets crop the lower legs on purpose. |
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
- [ ] Bleed images only: head near the top guide and centered, feet on the bottom guide
- [ ] `BG` fills the whole canvas
- [ ] `CUT` is a PNG, has a transparent background, has clean edges, and has no glow or shadow added
- [ ] `CUT` lines up with the `BG` (same size and position)
- [ ] Both `BG` and `CUT` made, if you want the image on every set and option
- [ ] Named `{TYPE}-{YEAR}-{NAME}-({PLAYER ID})-({TEAM}).png`
- [ ] Uploaded directly into the shared folder (not a subfolder)
- [ ] Folder shared with the bot as **Viewer**
- [ ] Test card built and the source badge shows your library
