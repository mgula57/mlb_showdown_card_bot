# Showdown Bot design language

A modern, flat app with a handful of touches lifted straight off the 2000–2005 MLB Showdown cards. The structure stays quiet so the numbers and the cards do the talking.

Every new screen and component follows this document. If something you need isn't covered, extend this file in the same change rather than inventing a one-off style.

Visual reference: the approved style guide artifact (Showdown Bot Design Language) shows each rule below rendered in light and dark.

## Three rules

1. **Modern base.** Plain surfaces, one small corner radius, hairline borders, no decorative gradients (the search frame's navy-to-red border is the one exception). Body copy, forms and controls look like a clean modern app.
2. **Period accents in five places only:** headings, labels, numbers, badges and frames. Never on body text. Texture stays at the top of a page (`PinstripeBackdrop`) and never runs behind the whole page.
3. **Numbers are the hero.** Points, On-Base, Control and chart ranges get the card's treatment: tabular figures, set in plates or the command badge.

## Color

All colors come from tokens in [`src/index.css`](src/index.css). Components never use raw Tailwind palette colors (`blue-500`, `green-600`) or hex values. Light mode is a pale 2001 card-back silver; dark mode is a navy-tinted near-black.

| Role | Token | Notes |
|---|---|---|
| Page background | `--background-primary` | Silver in light, near-black in dark |
| Panels, inputs, chart boxes | `--background-secondary` | White in light |
| Quiet fills, skeletons, table headers | `--background-tertiary`, `--background-quaternary` | Silver steps |
| Hairline borders | `--divider` | Default border for everything |
| Strong rule | `--rule-strong` | Frames, hover borders, `shadow-raised` edge |
| Text | `--text-primary`, `--text-secondary`, `--text-tertiary` | Tertiary is captions and meta |
| Brand | `--showdown-blue`, `--showdown-red` | Navy for primary actions, selection and frames; red for the active tab and emphasis |
| Stat plates | `--plate`, `--plate-ink` | Silver plate in light, raised gray plate in dark. Team-color fields use the dark `onField` plate instead |
| Status | `--green`, `--red`, `--warning`, `--success`, `--error`, `--live` | Semantic only, never decorative |
| Team-color fields | `--card-edge`, `--field-ink`, `--field-live` | Same in both themes; see below |
| Highlight gold | `--gold` | Starred teams, Hall of Fame, All-Star marks. Never decorative |
| Bronze | `--bronze` | Third-place medals only (1st is `--gold`, 2nd `--text-secondary`) |

Older tokens (`--primary`, `--secondary`, `--tertiary`, `--quaternary`) still work. Prefer the `--text-*` names in new code. If you need a color that doesn't exist, add a token for both themes in `index.css` and list it here.

**Team colors** appear only where a team is the subject: the team preview tile, the year/team plate (primary) and points plate (secondary) on a card, the command number, the out results on a chart. Pass them inline (`style`) from the card or team data, and run them through `getContrastTextColor` / `darkenIfLowContrastOnWhite` from `functions/colors.ts` for text.

## Type

| Role | Class | Use |
|---|---|---|
| Display | `font-display uppercase` | Headlines that stand alone: page and section titles, release names, team abbreviations and names on team tiles, tab labels. The bundled Helvetica Neue Condensed Heavy Oblique (already slanted, so never add `italic`) |
| Command number | `font-display-black` | On-Base and Control numbers in `CardCommand`. Helvetica Neue 107 Extra Black Condensed |
| Card name | `font-display-upright` | Player names and the year/team plate next to them on cards (`CardItem`, `CardItemCompact`), stat-badge values, game scores, and form section titles (`FormSection`), which sit inline with summary chips. Helvetica Neue Bold Condensed |
| Eyebrow | `<Eyebrow>` | Small, widely spaced caps above a title |
| Field label | `FIELD_LABEL_CLASS` (`fieldStyles.ts`) | The label above every input, dropdown, picker and toggle group: 11px semibold body-face caps, lightly spaced, tertiary ink, like ON-BASE / SPEED on the card front. Hint text inside a label goes back to `normal-case` |
| Caps label | `CAPS_LABEL_CLASS` (`fieldStyles.ts`) | The field label's type with no color or `block`: group labels in a list ("Rotation", "Overperformers" in green), table column headers, inline labels ("On Deck"). Add the ink yourself, `text-(--text-tertiary)` unless it carries a status color. Caps labels of 7–9px inside plates and chart visuals are card-stat micro labels and stay as they are |
| Body | default sans | Paragraphs, controls, helper text. Weights stop at `font-bold`: no `font-extrabold` or `font-black`, since titles use `Heading` and standalone numbers the display face |
| Data | `tabular-nums` | Every number that lines up in a column, ranges, points |

The italic display face is loud, so it's only for a headline that sits on its own. It never goes inline next to upright plates or stats, which is why card names use the upright condensed face. Everything else on a card or tile (plates, stat lines, chart labels and ranges, set numbers, counts) uses the body face. Paragraphs and descriptions always use the body face.

Display-face text never `truncate`s. The faces are wide, and the italic leans past its own box, so an `overflow: hidden` edge cuts off both long names and the slant of the last letter. A one-line title that can run long (a team, release or round name) uses `<Heading fit>`, or `FitText` for display text that isn't a heading (the team tile abbreviation). It shrinks from the CSS size down to `minScale`, then ellipsizes. Multi-line clamps (`line-clamp-2` on a release name) add `SLANT_ROOM_CLASS` from `headingStyles.ts`.

The display fonts' vertical metrics are normalized so capitals sit centered in their line box. Uppercase text in any display face centers in plates, badges and flex rows with plain `items-center` and `leading-none`, so never nudge it with offsets or padding tweaks. When adding or replacing a display font, run `uv run --with fonttools python frontend/scripts/normalize_font_metrics.py` (and add the file to its list).

Charts keep their compact footprint: don't increase cell padding, minimum widths or font sizes in `CardChart`, because cards are laid out around its width.

## Shape and depth

- **Corners:** `rounded-card` (5px) for panels and tiles, `rounded-control` (4px) for buttons and inputs. `rounded-plate` (2px) for plates, badges and skeleton bars, just enough to soften them at small sizes. Circles only for avatars, the command art and small status dots. No `rounded-xl` or larger, and no pills for counts or status (use a `Plate`).
- **Depth has three steps:**
  - **Flat:** 1px `--divider` border. Most things.
  - **Raised:** `shadow-raised`, a hard 2px bottom edge, for primary buttons and pressable tiles.
  - **Overlay:** `shadow-overlay`, the only soft shadow, for modals, menus, sheets and floating buttons.
- **Selection** is a navy outline: `border-(--showdown-blue) ring-1 ring-(--showdown-blue)`. Never an inverted fill (`bg-(--secondary) text-(--background-primary)`), which reads as a primary button. Rows of options use `choiceClass`.

## Components

Use these before writing new styles. All live in `src/components/shared/` unless noted.

| Component | What it is |
|---|---|
| `Plate` | The stat box from the card front, in semibold body-face caps. Variants: `ink` (stats, points), `navy`/`red` (OFFICIAL, LIVE, errata), `outline` (Draft, awards), `success` (Published), `onField`/`onFieldOutline` (on team-color fields), `custom` (team-colored, pass `style`; on cards the year/team plate takes the primary color and the points plate the secondary). Replaces rounded pills |
| `Eyebrow` | Spaced small caps above a title or labeling a group ("WHIP Leaders", "Step 1") |
| `buttonStyles.ts` → `buttonClass(variant, size)` | Buttons and button-styled links: `primary` (navy, `shadow-raised`), `secondary` (bordered surface), `ghost`, `danger` (red, destructive confirms only; adding, drafting or starting something is `primary`). Works on `<button>`, `<Link>` and `<a>`. `buttonVariantClass(variant)` is just the colors and states, for buttons that size themselves (`GameDetail`'s top bar, a card's corner action) |
| `choiceStyles.ts` → `choiceClass(selected, size)` | Choice chips: a row of options where one is picked (numbering mode, algorithm templates, a chart subset, a scoring filter). Bordered surface; the picked one gets the navy selection outline. Switching between views is a tab strip, not choice chips |
| `CornerCount` | The small navy count plate pinned to a button's corner (active filters, new sims) |
| Card action button | `CardItemActionButton` (`cards/CardItemCompact`). `emphasis: 'primary'` makes a card's corner action the navy raised button (Add, Draft from a search); pass that instead of color classes |
| `NewBadge` / `BetaBadge` | Red `New` and outline `Beta` plates |
| `SearchFrame` / `searchFrameClass()` | A 2px navy-to-red gradient border, the only gradient in the system. Every search field and search button. The framed child paints its own background with a 3px corner |
| `Heading` (+ `headingStyles.ts` → `headingClass(level)`) | Every title. `page` (one per screen, display italic), `section` (a standalone block or modal title, display italic), `panel` (a title inline with counts, chips or controls, or naming a list item, upright condensed). Never a raw `<h1>`–`<h6>` or large bold body text |
| `fieldStyles.ts` → `fieldClass(size)` / `FIELD_FRAME_CLASS` | The one look for inputs and selects: flat surface, hairline that darkens on hover and turns navy on focus, 4px corner. `sm` (filter rows), `md` (forms), `lg` (the card search toolbar). `FormInput`, `CustomSelect`, the search toolbar triggers and the sort control all use it |
| `FormEnabler` (`customs/`) | The one boolean toggle: a field-height row with a square checklist box, empty when off, navy with a white check when on (the row's border turns navy too). `md` in form grids, `sm` in toolbars; `description` adds a helper line. Never a sliding switch or a raw checkbox |
| `CustomSelect` | Dropdowns. Pick a `size`; don't restyle the button. The menu is a card with an overlay shadow, a red bar and navy check on the selected row, and eyebrow-style group headers. `buttonClassName` is only for selects that aren't fields (the set-logo pickers), marked `design-ok` |
| `tabStyles.ts` / `Tabs` | Display-face tab labels over a hairline with a red bar under the active tab. `Tabs` for controlled tabs, `tabListClass` + `radixTabTriggerClass` on Radix `Tabs.Root`. `radixVerticalTabTriggerClass` is the vertical nav list (the Seasons sidebar): the same red bar on the left edge. Never a segmented control with a filled active tab |
| `GameStatePlate` (`games/`) | A game's status: red LIVE plate with the pulse dot (plus the inning), ink Final, outline for scheduled, Postponed and the rest. Used by the schedule list and the game header |
| `CardCommand` (`cards/card_elements/`) | The home plate (On-Base) and baseball (Control) art with the number in the team color |
| `CardChart` (`cards/card_elements/`) | Chart box: hairline `--divider` border, team-color outs, compact ranges |
| `bg-pinstripe` (utility) | Card-back pinstripes. Headers, hero bands and card fields only |
| `PinstripeBackdrop` | Pinstripes behind the top of a page, fading out into the content (Home uses it). Inside a `relative isolate` page container |
| `InlineError` | Small red notice inline with a form or panel (validation, failed upload, a sim that couldn't start). `sm` in forms, `md` in modals; `icon` adds a warning triangle for field validation |

Reference implementations: `CardItem`, `CardItemCompact`, `TeamPreviewCard`, `ReleaseItem`.

### Team-color fields

The team preview tile gets the full card-front look, because the team is the subject: the team color as the background under the faded ballpark art (`/images/teams/Field.png`) with a team-color wash at the top and a dark scrim under the roster, a white card edge (`--card-edge`) instead of a gradient border, `onField` plates, and the abbreviation in `font-display` with `text-outline-double`. Don't use this look on panels that aren't about one team.

### Frames

The 2001 card-back double rule (outer `--rule-strong` border, a gap, inner `--divider` hairline) marks feature tiles like a release tile or a finished card. It isn't for ordinary panels.

### Loading

Skeletons use the silver surface (`--background-tertiary`) and match the dimensions of the content they stand in for, plates included.

### Empty states (planned)

Screens with nothing to show yet will borrow the voice of the 2000 print ads: a short, confident slab-serif caps headline ("NO RELEASES YET."), one plain line under it, and a primary action. The `EmptyState` component and slab face aren't built yet; add them here when they are.

## Copy

Write like the cards and the ads: short, confident, plain. Use baseball terms the way the cards print them (PT., ON-BASE, CONTROL, IP 7, SPEED B (15)). Buttons say exactly what happens ("Run algorithm", "Publish").

## Set themes (future)

The app ships one theme. Components are built so a future theme for a specific set (2004, say) can restyle only these slots, keyed off the user's set preference or the set of what's on screen:

- Command badge
- Name and stat line
- Chart shape
- Background texture
- Set-number format

Layout, controls, body type, the palette and the display face never change between themes. Until a theme exists, keep set-specific styling out of components.

## Do and don't

**Do**
- Use tokens and the shared components above.
- Set aligned numbers in `tabular-nums`.
- Keep one headline number per screen in the command badge or a large plate.
- Give loading content a skeleton shaped like the result.
- Use `cursor-pointer` on everything clickable.

**Don't**
- Use raw Tailwind palette colors or hex values in components.
- Add decorative gradients, glows, glassmorphism or purple accents. That includes the legacy `animated-showdown-gradient` / `animated-team-gradient` CTA classes: primary actions use `buttonClass('primary')`.
- Use `rounded-md`/`rounded-lg` (between the control and card corners), `rounded-xl` or larger, or pills for status and counts.
- Write a raw `<h1>`–`<h6>`, or style a title with large bold body text. Use `<Heading>`.
- Restyle a `CustomSelect` with `buttonClassName`. Use its `size`.
- Hand-style a field label or build a switch or checkbox. Use `FIELD_LABEL_CLASS` and `FormEnabler`.
- Use soft shadows on anything that isn't an overlay.
- Set body copy or long text in the display face.
- Branch on `isDark` for colors. Tokens already switch with the theme.
- Build class names from variables (`` `border-(${tone})/30` ``). Tailwind can't see them, so they never render. Map each state to a full class string instead (see `OUTCOME_TONE_CLASSES` in `SimResult`).

## Enforcement

`npm run lint:design` checks the mechanical rules on lines changed since `master`: raw palette colors, hex in classes, large and in-between corner radii, arbitrary or Tailwind-scale radii in place of `rounded-plate`/`rounded-control`, pills, raw heading tags, large bold body text used as a title, hand-styled field labels and caps labels, extrabold and black weights, hand-built tabs and filled buttons, hand-built toggles, restyled selects, soft shadows and decorative gradients. `-- --base HEAD` checks only uncommitted work, `-- --all` prints a full audit of `src/`, and `-- --all --list` adds every location. The lint can't judge everything (whether a title picked the right level, whether a new control matches its neighbors), so compare new UI against an already converted screen too. The Tailwind CSS IntelliSense extension separately suggests canonical forms for arbitrary values (`p-[3px]` → `p-0.75`); take those suggestions, except for corner radii, which use the `rounded-*` tokens above rather than Tailwind's `rounded-xs`/`rounded-sm` scale. If a line genuinely needs an exception, add a `design-ok: <reason>` comment on it or the line above. For a block (e.g. the edition and expansion identity colors in `customs/cardStyle.ts`, or the Google and Discord sign-in buttons in `LoginModal`, which follow those brands' own button colors), wrap it in `design-ok-start: <reason>` / `design-ok-end` comments. Reuse `cardStyle.ts`'s `expansionOptions` / `editionOptions` wherever expansions or editions are listed rather than copying their colors.

Run it alongside `npm run lint` and `npm run type-check` before finishing frontend work.

## Migration status

Done: tokens and fonts, tabs, search frame, buttons, `NewBadge`/`BetaBadge`, `CardItem`, `CardItemCompact`, `CardChart`, `CardCommand`, `TeamPreviewCard`, `ReleaseItem`, the Home page (`Home.tsx`, a full-screen reference: section headers, panels, the navy ticker band, eyebrows, plates for status), and everything it renders: the game reel and field (`games/`), `CardDetail` and `card_detail/`, and the shared `Modal`, `CustomSelect`, `InfoTooltip`, `TeamChip`, `FormSection` and `FormEnabler`. The Custom Card Builder (`CustomCardBuilder.tsx`) and everything it renders: form primitives (`FormInput`, `FormSection`, `FormSectionSummary`), the gallery tab, `LoginModal`, `SignInPrompt`, `WhatsNewBanner`, `ToastMessage` and the builder notices. The team page (`TeamDetail.tsx`) and everything it renders: `TeamSettingsForm`, `AutofillPanel`, `GuidedDraftPanel`, `PlayModal`, `SimSeasonRow`, `LineupPanel`, `FieldView`, `TeamLogo`, and the shared search pieces (`ShowdownCardSearch`, `QuickFiltersDropdown`, `SetMultiSelect`, `SortButton`, `MultiSelect`, `SlideOver`, `LoadingStatusToast`). The Account page (`AccountPage.tsx`) and everything it renders: `AccountSection`, `ImageLibrarySettings`, `DriveLibrarySetupModal`, `AvatarCropModal`, `AccountIcon`. The Seasons page (`Seasons.tsx`) and everything it renders: `SeasonLeaders`, `AwardWinners`, `Standings`, `SidebarPanel`, Gameday (`GameDetail`, `GameSchedule`, `GameSimSetupModal`, `PlayByPlayLog`, `games/detail/`), and the season sim setup (`simulate/`). The sim result (`SimResult.tsx`) and its panels (`SectionCard`, `KpiTile`, `SimAwardsList`, `SimBracket`, `SimStatsTable`, `SimRecordComparison`, `SimWinPctChart`). The Release Builder (`releases/`: `Releases`, `ReleaseDetail`, `EditionBuilder`, `EditionImages`, `AlgorithmBuilder`, `NewReleaseModal`, `SummaryCharts` and their parts) and the auth pages (`ResetPasswordPage`, `UsernamePrompt`). Team-color CTAs (the team page's Sim button) are a flat team primary with `shadow-raised`, never `animated-team-gradient`.

Known leftovers inside converted screens: the team-color glow pulse around the card image in `CardDetail` (a glow, kept for now as a signature effect) and the large clip radius on rendered card art, which matches the art's own corners.

Every screen in `src/` is converted: `npm run lint:design -- --all` reports zero issues, and that should stay true. New work must pass `npm run lint:design` on its changed lines. Anything that has to break a rule (a brand color, a scroll fade) needs a `design-ok:` note saying why.
