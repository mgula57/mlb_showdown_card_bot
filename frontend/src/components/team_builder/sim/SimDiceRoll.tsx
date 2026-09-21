import { useEffect, useId, useState } from 'react';
import { usePrefersReducedMotion } from '../../../hooks/usePrefersReducedMotion';

// An MLB Showdown at-bat is two twenty-sided rolls - the pitch roll decides who has the
// advantage, the swing roll is read off that player's chart - so this is a pair of d20s rather
// than the six-sided dice a generic "rolling" flourish would use.
const SIDES = 20;

// TOSS_MS MUST MATCH the `sim-die-toss` / `sim-die-shadow` durations in index.css. The face value
// is scrambled from here while the CSS motion runs and set one final time when it ends, so a
// mismatch shows up as a die that visibly changes number after it has already landed.
const TOSS_MS = 900;
/** How long a landed die holds its result before the next toss. */
const HOLD_MS = 1300;
/** Face-change cadence mid-air. Fast enough to read as a tumble, slow enough not to strobe. */
const SCRAMBLE_MS = 70;
/** The swing die lags the pitch die so the pair reads as two throws, not one mirrored animation. */
const STAGGER_MS = 170;

const rollFace = () => 1 + Math.floor(Math.random() * SIDES);

// Face-on icosahedron: a hexagonal silhouette (circumradius 46) around an upward centre face
// (circumradius 26), with the remaining nine visible faces filling the ring between them. Drawn
// once at these coordinates rather than computed, since the geometry is fixed.
const HEX_POINTS = '0,-46 39.84,-23 39.84,23 0,46 -39.84,23 -39.84,-23';
const CENTER_FACE_POINTS = '0,-26 22.52,13 -22.52,13';
const FACET_LINES = [
    'M 0,-26 L 22.52,13 L -22.52,13 Z',   // centre face
    'M 0,-46 L 0,-26',                    // spokes out to the three aligned hex corners
    'M 39.84,23 L 22.52,13',
    'M -39.84,23 L -22.52,13',
    'M 39.84,-23 L 0,-26',                // each in-between hex corner back to two centre corners
    'M 39.84,-23 L 22.52,13',
    'M 0,46 L 22.52,13',
    'M 0,46 L -22.52,13',
    'M -39.84,-23 L -22.52,13',
    'M -39.84,-23 L 0,-26',
].join(' ');

/** The die itself. Rounded corners come from stroking the silhouette with its own fill and a
 *  round line join, which keeps the shape a single shape (no separate outline to fall out of
 *  sync with the gradient). */
function D20Face({ value, accent }: { value: number; accent: string }) {
    // `useId` output contains colons, which are legal in an id but awkward inside `url(#…)`.
    const gradientId = `d20-${useId().replace(/:/g, '')}`;
    return (
        <svg viewBox="-50 -50 100 100" className="h-full w-full" aria-hidden>
            <defs>
                <linearGradient id={gradientId} x1="0.15" y1="0" x2="0.75" y2="1">
                    <stop offset="0%" stopColor={accent} stopOpacity="1" />
                    <stop offset="100%" stopColor={accent} stopOpacity="0.6" />
                </linearGradient>
            </defs>
            <polygon
                points={HEX_POINTS}
                fill={`url(#${gradientId})`}
                stroke={`url(#${gradientId})`}
                strokeWidth="7"
                strokeLinejoin="round"
            />
            <polygon points={CENTER_FACE_POINTS} fill="#ffffff" fillOpacity="0.16" />
            <path
                d={FACET_LINES}
                fill="none"
                stroke="#ffffff"
                strokeOpacity="0.3"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
            <text
                x="0"
                y="0"
                textAnchor="middle"
                dominantBaseline="central"
                fontSize="22"
                fontWeight="800"
                letterSpacing="-0.5"
                fill="#ffffff"
            >
                {value}
            </text>
        </svg>
    );
}

/** One die running its own toss/hold loop. Timing is owned per-die rather than by the parent so
 *  `startDelayMs` offsets the whole cycle, not just the first throw. */
function RollingDie({ accent, label, startDelayMs }: { accent: string; label: string; startDelayMs: number }) {
    const prefersReduced = usePrefersReducedMotion();
    const [face, setFace] = useState(rollFace);
    // Bumped once per toss and used as the animation element's `key`: remounting is what restarts
    // a `forwards` CSS animation. 0 means "not thrown yet", so nothing animates on mount and the
    // stagger below is actually visible on the first throw.
    const [tossCount, setTossCount] = useState(0);

    useEffect(() => {
        if (prefersReduced) return;

        let scramble: number | undefined;
        let settle: number | undefined;
        let nextToss: number | undefined;

        const toss = () => {
            setTossCount(n => n + 1);
            scramble = window.setInterval(() => setFace(rollFace()), SCRAMBLE_MS);
            settle = window.setTimeout(() => {
                window.clearInterval(scramble);
                setFace(rollFace());
                nextToss = window.setTimeout(toss, HOLD_MS);
            }, TOSS_MS);
        };

        const start = window.setTimeout(toss, startDelayMs);
        return () => {
            window.clearTimeout(start);
            window.clearTimeout(settle);
            window.clearTimeout(nextToss);
            window.clearInterval(scramble);
        };
    }, [prefersReduced, startDelayMs]);

    const rolling = tossCount > 0 && !prefersReduced;

    return (
        <div className="flex flex-col items-center gap-3">
            <div className="relative h-14 w-14 sm:h-16 sm:w-16">
                <span
                    key={`shadow-${tossCount}`}
                    aria-hidden
                    className={`absolute -bottom-2 left-1/2 -ml-5 h-[5px] w-10 rounded-[50%] bg-black/25 opacity-25 blur-[3px] ${rolling ? 'sim-die-shadow' : ''}`}
                />
                <div
                    key={tossCount}
                    className={`absolute inset-0 drop-shadow-sm ${rolling ? 'sim-die-toss' : ''}`}
                >
                    <D20Face value={face} accent={accent} />
                </div>
            </div>
            <span className="text-[9px] font-bold uppercase tracking-[0.12em] text-tertiary">{label}</span>
        </div>
    );
}

/**
 * Ambient pair of tumbling d20s shown while a season simulates. Decorative only — the faces are
 * random, not the sim's actual rolls — so the whole thing is hidden from assistive tech.
 */
export function SimDiceRoll() {
    return (
        <div className="flex items-start justify-center gap-6 sm:gap-8" aria-hidden>
            <RollingDie accent="var(--showdown-blue)" label="Pitch" startDelayMs={0} />
            <RollingDie accent="var(--showdown-red)" label="Swing" startDelayMs={STAGGER_MS} />
        </div>
    );
}
