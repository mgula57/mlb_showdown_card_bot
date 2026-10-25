#!/usr/bin/env node
/**
 * Design-language lint (see frontend/DESIGN.md). Flags the mechanical rules on lines you added or
 * changed relative to master, so legacy code doesn't block new work:
 *
 *   npm run lint:design                   # lines changed since master; exits 1 on violations
 *   npm run lint:design -- --base HEAD    # only uncommitted changes (or any other git ref)
 *   npm run lint:design -- --all          # audit every file under src/, prints counts, exits 0
 *   npm run lint:design -- --all --list   # same, plus every violation's location
 *
 * A line can opt out with a `design-ok: <reason>` comment on that line or the line above; a block
 * opts out between `design-ok-start: <reason>` and `design-ok-end` comments.
 */
import { execSync } from 'node:child_process';
import { readFileSync } from 'node:fs';

const PALETTE = 'slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose';

const RULES = [
    {
        id: 'raw-palette-color',
        pattern: new RegExp(`\\b(?:bg|text|border|ring|from|via|to|fill|stroke|outline|divide|decoration|accent|caret|shadow|placeholder)-(?:${PALETTE})-\\d{2,3}\\b`),
        message: 'Raw Tailwind palette color. Use a theme token, e.g. text-(--text-secondary) or bg-(--showdown-blue).',
    },
    {
        id: 'arbitrary-hex',
        pattern: /-\[#[0-9a-fA-F]{3,8}\]/,
        message: 'Hex value in a class. Add or reuse a token in index.css instead.',
    },
    {
        id: 'large-radius',
        pattern: /\brounded(?:-[tblrsexy]{1,2})?-(?:xl|2xl|3xl)\b/,
        message: 'Corner radius above the system. Use rounded-card (panels, tiles) or rounded-control (buttons, inputs).',
    },
    {
        id: 'mid-radius',
        pattern: /(?<![\w-])rounded(?:-[tblrsexy]{1,2})?-(?:md|lg)\b/,
        message: 'In-between corner radius. Use rounded-control (4px: buttons, inputs, chips) or rounded-card (5px: panels, tiles, menus).',
    },
    {
        id: 'plate-radius',
        pattern: /(?<![\w-])rounded(?:-[tblrsexy]{1,2})?-(?:\[2px\]|xs)(?![\w-])/,
        message: 'Use rounded-plate for the 2px plate, badge and skeleton-bar corner.',
    },
    {
        id: 'control-radius',
        pattern: /(?<![\w-])rounded(?:-[tblrsexy]{1,2})?-(?:\[4px\]|sm)(?![\w-])/,
        message: 'Use rounded-control for the 4px corner.',
    },
    {
        id: 'pill',
        pattern: /\brounded-full\b(?=[^"'`]*\bpx-[\d.]+)|\bpx-[\d.]+\b(?=[^"'`]*\brounded-full\b)/,
        unless: /\b(?:w-\d+ h-\d+|h-[\d.]+ w-[\d.]+|size-\d)/,
        message: 'Pill-shaped tag or chip. Status and counts are plates (<Plate>, 2px corner); clickable chips use rounded-control. Circles are only for avatars, dots and icon buttons.',
    },
    {
        id: 'plain-heading',
        pattern: /<h[1-6]\b/,
        unless: /font-display/,
        message: 'Raw heading tag. Use <Heading level="page|section|panel"> (or <Eyebrow> for a small group label) from shared/Heading.',
    },
    {
        id: 'plain-headline',
        pattern: /\b(?:text-(?:lg|xl|[2-9]xl)|text-\[(?:1[6-9]|[2-9]\d)px\])\b[^"'`]*\bfont-(?:semibold|bold|extrabold|black)\b|\bfont-(?:semibold|bold|extrabold|black)\b[^"'`]*\b(?:text-(?:lg|xl|[2-9]xl)|text-\[(?:1[6-9]|[2-9]\d)px\])/,
        unless: /font-display/,
        message: 'Large bold body text reads as a title. Use <Heading>, or the display face for a standalone number.',
    },
    {
        id: 'plain-label',
        pattern: /<label\b[^>]*className="[^"]*\btext-(?:xs|sm|\[1[0-3]px\])\b/,
        message: 'Hand-styled field label. Use FIELD_LABEL_CLASS from shared/fieldStyles (the card-stat caps).',
    },
    {
        id: 'plain-caps-label',
        pattern: /["'`](?=[^"'`]*\buppercase\b)(?=[^"'`]*\btracking-(?:wide|wider|widest)\b)(?=[^"'`]*\bfont-(?:semibold|bold|extrabold|black)\b)/,
        // 7-9px caps are card-stat micro labels inside plates and chart visuals, below the field-label size.
        unless: /<th\b|font-display|\btext-\[[789]px\]/,
        message: 'Hand-styled caps label. Use FIELD_LABEL_CLASS (a label over a field or group; CAPS_LABEL_CLASS when it needs its own color), <Eyebrow> (above a title) or <Plate> (a status or stat).',
    },
    {
        id: 'heavy-weight',
        pattern: /\bfont-(?:extrabold|black)\b/,
        unless: /font-display/,
        message: 'Heavy body weight. Titles use <Heading>; standalone numbers (scores, totals) use font-display-upright with tabular-nums.',
    },
    {
        id: 'custom-tab',
        pattern: /data-\[state=active\]:bg-|data-\[state=active\]:font-bold/,
        message: 'Hand-built tab. Use tabListClass / radixTabTriggerClass from shared/tabStyles, or <Tabs>.',
    },
    {
        id: 'custom-button',
        pattern: /["'`](?=[^"'`]*\bbg-\(--(?:showdown-blue|showdown-red|secondary)\)(?![\w/-]))(?=[^"'`]*\btext-(?:white|\(--background-primary\))(?![\w/-]))(?=[^"'`]*\b(?:cursor-pointer|hover:))/,
        message: 'Hand-built filled button. Use buttonClass("primary" | "danger") from shared/buttonStyles.',
    },
    {
        id: 'clipped-display',
        pattern: /(?:\bfont-display(?![\w-])|<Heading[^>]*level="(?:page|section)")[^>]*\b(?:truncate|line-clamp-\d)\b|\b(?:truncate|line-clamp-\d)\b[^>]*\bfont-display(?![\w-])/,
        unless: /SLANT_ROOM_CLASS/,
        message: 'Truncated display face. The italic leans past its box, so the clip shaves names and the last letter. Use <Heading fit> or FitText for one line; add SLANT_ROOM_CLASS to a multi-line clamp.',
    },
    {
        id: 'custom-toggle',
        pattern: /role="switch"|type="checkbox"/,
        message: 'Hand-built toggle. Use FormEnabler (the checklist box) so every boolean looks the same.',
    },
    {
        id: 'restyled-select',
        pattern: /\bbuttonClassName=/,
        message: 'CustomSelect restyled by hand. Pick a size ("sm" | "md" | "lg") so every field matches shared/fieldStyles; keep buttonClassName for non-field selects and mark it design-ok.',
    },
    {
        id: 'soft-shadow',
        pattern: /\bshadow-(?:sm|md|lg|xl|2xl)\b/,
        message: 'Soft drop shadow. Use shadow-raised, or shadow-overlay for modals, menus and sheets only.',
    },
    {
        id: 'decorative-gradient',
        pattern: /\bbg-(?:linear|gradient|radial|conic)-|\banimated-(?:showdown|team)-gradient\b/,
        message: 'Decorative gradient. Surfaces are flat; see DESIGN.md for the few allowed textures.',
    },
];

const SOURCE = /\.(tsx|ts)$/;
const isComment = (line) => /^\s*(\/\/|\*|\/\*)/.test(line);
// The note can sit on the line, the line above, or above a multi-line className opener (`className={\``).
const optedOut = (lines, i) => lines[i]?.includes('design-ok') || lines[i - 1]?.includes('design-ok')
    || (/className=\{?`\s*$/.test(lines[i - 1] ?? '') && lines[i - 2]?.includes('design-ok'));

function sh(cmd) {
    // The branch diff against master can run to many MB; the default 1MB buffer kills the process.
    return execSync(cmd, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], maxBuffer: 256 * 1024 * 1024 }).trim();
}

function mergeBase() {
    const baseFlag = process.argv.indexOf('--base');
    if (baseFlag !== -1) return sh(`git rev-parse ${process.argv[baseFlag + 1]}`);
    for (const ref of ['origin/master', 'master']) {
        try { return sh(`git merge-base HEAD ${ref}`); } catch { /* try the next ref */ }
    }
    throw new Error('Could not find a merge base with master.');
}

/** Map of file -> set of 1-based line numbers added or changed since the merge base. */
function changedLines() {
    const changed = new Map();
    const diff = sh(`git diff -U0 --no-color --relative ${mergeBase()} -- src`);
    let file = null;
    for (const line of diff.split('\n')) {
        if (line.startsWith('+++ ')) {
            file = line.slice(4).replace(/^b\//, '');
            if (file === '/dev/null' || !SOURCE.test(file)) file = null;
            else if (!changed.has(file)) changed.set(file, new Set());
            continue;
        }
        const hunk = line.match(/^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@/);
        if (hunk && file) {
            const start = Number(hunk[1]);
            const count = hunk[2] === undefined ? 1 : Number(hunk[2]);
            for (let n = start; n < start + count; n++) changed.get(file).add(n);
        }
    }
    const untracked = sh('git ls-files --others --exclude-standard src').split('\n').filter((f) => SOURCE.test(f));
    for (const f of untracked) changed.set(f, null); // null = every line
    return changed;
}

function allFiles() {
    const files = sh('git ls-files --cached --others --exclude-standard src').split('\n').filter((f) => SOURCE.test(f));
    return new Map(files.map((f) => [f, null]));
}

function lint(targets) {
    const violations = [];
    for (const [file, lineSet] of targets) {
        let lines;
        try { lines = readFileSync(file, 'utf8').split('\n'); } catch { continue; } // deleted
        let inOptOutBlock = false;
        lines.forEach((text, i) => {
            if (text.includes('design-ok-start')) inOptOutBlock = true;
            if (text.includes('design-ok-end')) { inOptOutBlock = false; return; }
            if (inOptOutBlock || (lineSet && !lineSet.has(i + 1)) || isComment(text) || optedOut(lines, i)) return;
            for (const rule of RULES) {
                const match = text.match(rule.pattern);
                if (match && !(rule.unless && rule.unless.test(text))) violations.push({ file, line: i + 1, rule, match: match[0] });
            }
        });
    }
    return violations;
}

const auditAll = process.argv.includes('--all');
const violations = lint(auditAll ? allFiles() : changedLines());

if (auditAll) {
    const counts = Object.fromEntries(RULES.map((r) => [r.id, 0]));
    const byFile = new Map();
    for (const v of violations) {
        counts[v.rule.id]++;
        byFile.set(v.file, (byFile.get(v.file) ?? 0) + 1);
    }
    console.log('Design-language audit (all of src/):\n');
    for (const [id, n] of Object.entries(counts)) console.log(`  ${id.padEnd(22)} ${n}`);
    console.log(`\nAffected files (${byFile.size}):`);
    [...byFile].sort((a, b) => b[1] - a[1]).forEach(([f, n]) => console.log(`  ${String(n).padStart(4)}  ${f}`));
    if (process.argv.includes('--list')) {
        console.log('');
        for (const v of violations) console.log(`${v.file}:${v.line}  ${v.rule.id}  "${v.match.slice(0, 60)}"`);
    }
    process.exit(0);
}

if (violations.length === 0) {
    console.log('Design lint: no issues on changed lines.');
    process.exit(0);
}
for (const v of violations) console.log(`${v.file}:${v.line}  ${v.rule.id}  "${v.match}"\n    ${v.rule.message}`);
console.log(`\n${violations.length} design-language issue(s) on changed lines. See frontend/DESIGN.md.`);
process.exit(1);
