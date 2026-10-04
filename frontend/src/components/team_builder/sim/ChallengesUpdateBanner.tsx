import { useState } from 'react';
import { FaXmark } from 'react-icons/fa6';
import { FaChessKnight } from 'react-icons/fa';

const STORAGE_KEY = 'mlb.challenges.updateBanner.v4.4.dismissed';

const DISCORD_URL = 'https://discord.com/channels/669174897939054602/1555417587293098034';

const UPDATES = [
    'Guided Draft: build your roster one round at a time — lock in an Ace, a Star and a Closer first, then pick between 4 similarly priced cards for each open slot.',
    'Narrower player pools: challenges now pull from tighter pools, so every pick has a trade-off and a cheap auto-fill won\'t cut it.',
    'No WOTC cards in sims: original Wizards of the Coast cards are now restricted from sim rosters.',
];

/** Dismissable "what changed" callout at the top of the Challenges tab. Dismissal is remembered per browser. */
export function ChallengesUpdateBanner() {
    const [visible, setVisible] = useState(() => {
        try { return localStorage.getItem(STORAGE_KEY) !== 'true'; } catch { return true; }
    });

    if (!visible) return null;

    const dismiss = () => {
        try { localStorage.setItem(STORAGE_KEY, 'true'); } catch { /* storage unavailable — dismiss for this session only */ }
        setVisible(false);
    };

    return (
        <div className="relative rounded-xl border border-(--showdown-blue)/30 bg-(--showdown-blue)/5 px-4 py-3 flex flex-col gap-2">
            <button
                type="button"
                onClick={dismiss}
                aria-label="Dismiss"
                className="absolute top-2.5 right-2.5 text-(--text-tertiary) hover:text-(--text-primary) transition-colors cursor-pointer"
            >
                <FaXmark size={14} />
            </button>

            <div className="flex items-center gap-2 pr-6">
                <FaChessKnight className="text-(--showdown-blue) shrink-0" />
                <h4 className="text-[14px] font-black text-(--text-primary)">Challenges just got more strategic</h4>
            </div>

            <ul className="flex flex-col gap-1 list-disc pl-5 text-[12px] leading-snug text-(--text-secondary)">
                {UPDATES.map(text => <li key={text}>{text}</li>)}
            </ul>

            <p className="text-[12px] text-(--text-tertiary)">
                I'm gathering feedback during the first few weeks — tell me what feels good, what's too tight, and what's broken.{' '}
                <a
                    href={DISCORD_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-bold text-(--showdown-blue) hover:underline cursor-pointer"
                >
                    Share feedback on Discord
                </a>
            </p>
        </div>
    );
}
