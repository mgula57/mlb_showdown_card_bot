import { useEffect, useState } from 'react';
import { FaDice } from 'react-icons/fa6';

// PLAIN-LANGUAGE FACTS ABOUT THE SIMULATION ENGINE, ROTATED WHILE THE USER WAITS FOR A RUN TO
// FINISH. KEPT SEPARATE FROM `core/simulation/README.md` (DEVELOPER-FACING, FILE/CLASS-LEVEL)
// SINCE THIS COPY IS FOR PLAYERS, NOT ENGINEERS.
const TIPS = [
    "Every at-bat is two dice rolls: one decides whether the pitcher or the hitter is in control, the second is matched against that player's card to get the result.",
    'Steals, extra-base advances, and double plays each get their own roll — weighted by the runner\'s speed against the fielder\'s arm or defense rating.',
    'Rosters are built like a real front office would build them: your best 13 position players, 5 starters, and 8 relievers make the active roster, with the rest waiting in reserve.',
    'Turn on injuries and players can land on the IL mid-season — the more a player actually played in real life, the healthier the sim assumes he is.',
    'Each team manages its own bullpen — closers get save chances, and every other reliever is picked by matchup leverage and how much they\'ve pitched recently.',
    'Standings, divisions, and the postseason format all mirror what was actually used that season — Wild Card, LCS, or straight to the World Series, depending on the year.',
    'MVP, Cy Young, Rookie of the Year, and Silver Slugger awards are handed out at the end of the season based on how it actually played out.',
] as const;

const ROTATE_INTERVAL_MS = 5000;

/** Rotating "how the simulation works" facts, shown alongside `SimProgress` while a run is in flight. */
export function SimEngineExplainer() {
    const [index, setIndex] = useState(0);

    useEffect(() => {
        const id = setInterval(() => setIndex(prev => (prev + 1) % TIPS.length), ROTATE_INTERVAL_MS);
        return () => clearInterval(id);
    }, []);

    return (
        <div className="w-full max-w-sm flex items-start gap-2.5 px-3.5 py-3 rounded-lg border border-(--border-secondary) bg-(--background-secondary)">
            <FaDice className="text-(--text-tertiary) text-sm mt-0.5 shrink-0" />
            <p key={index} className="text-[12px] leading-relaxed text-(--text-secondary)">
                {TIPS[index]}
            </p>
        </div>
    );
}
