import { useEffect, useState } from 'react';
import { FaDice } from 'react-icons/fa6';

// PLAIN-LANGUAGE FACTS ABOUT THE SIMULATION ENGINE, SHOWN AT RANDOM WHILE THE USER WAITS FOR A
// RUN TO FINISH. KEPT SEPARATE FROM `core/simulation/README.md` (DEVELOPER-FACING, FILE/CLASS-
// LEVEL) SINCE THIS COPY IS FOR PLAYERS, NOT ENGINEERS — IT'S ABOUT WHAT THE SIM ASSUMES AND CAN
// DO, NOT HOW IT'S BUILT.
const TIPS = [
    // THE CORE AT-BAT MECHANIC
    "Every at-bat is two dice rolls: one decides whether the pitcher or the hitter has the advantage, the second is matched against that player's chart to get the result.",
    "Both rolls get a small random wobble baked in, so the same matchup never plays out exactly the same way twice — even a stacked chart doesn't guarantee the same result on repeat at-bats.",
    "If a swing roll lands past the top of a player's chart, it doesn't miss — it resolves to the best result printed on the card.",
    'A batter only takes the pitcher\'s card into account for who\'s "in control" of the at-bat — the printed chart itself belongs to whoever wins that roll, hitter or pitcher.',

    // BASERUNNING
    'Steals, extra-base advances, and double plays each get their own roll — weighted by the runner\'s speed against the fielder\'s arm or defense rating.',
    'Stealing third is riskier than stealing second in the model — the sim quietly docks the success odds for runners trying to take third.',
    'A runner on third with two outs gets an extra push to try for home on a fly ball or base hit — the sim knows two-out, station-to-station baseball is a losing strategy.',
    'The sim won\'t send a runner into a jam on purpose — if the next base is occupied, there\'s no steal or advance attempt, no matter how fast the runner is.',
    'Even an elite base stealer won\'t attempt every single time — the model always leaves some chance he holds, and never boosts a steal attempt above a 90% call rate.',
    'A stolen base attempt is less likely to happen with two outs and a runner already on second — no point risking the inning just to get into scoring position when you\'re already there.',

    // PITCHING AND FATIGUE
    'A starter doesn\'t get pulled by pitch count — the engine tracks innings actually thrown against the pitcher\'s own printed IP rating, and every 3 runs allowed effectively "costs" an extra inning of stamina.',
    'A dominant start can go long — a pitcher who hasn\'t allowed a run and is still within his printed innings limit isn\'t flagged as tired, even if he\'s worked deep into the game.',
    'Relievers aren\'t just picked by who\'s "best" — the sim scores each available arm on how well the situation fits them: score tightness, how late it is, and how much they\'ve thrown in the last few days.',
    'A closer mostly only closes — the model actively avoids using him outside of a save situation, so he won\'t get burned in a random 6th inning.',
    'A pitcher who threw multiple innings in the last couple of days becomes less appealing to call on — recent workload directly lowers his fit score for the next outing.',
    'The bullpen has no idea who\'s "hot" or "cold" beyond what the numbers say — there\'s no momentum or gut-feeling factor, just workload, leverage, and matchup fit.',

    // LINEUPS, ROSTERS, AND REST
    'Rosters are built like a real front office would build them: your best 13 position players, 5 starters, and 8 relievers make the active roster, with the rest waiting in reserve.',
    'Every defensive position gets covered before the roster is topped off by raw value — a team won\'t end up stacked at one spot while thin at another just because the best players available happen to play the same position.',
    'A backup catcher is treated as a hard requirement when building a 40-man roster, even if it means passing on a more valuable player at another position.',
    'Star players get more starts between rest days than everyday role players — the engine assigns a personal "expected rest" gap scaled to a player\'s value, so your best hitter doesn\'t sit as often as your 25th man.',
    'Catchers are rested more often than any other position by design — the model treats the position itself as more physically demanding, independent of how good the catcher is.',
    'If a team\'s roster gets thin enough — injuries, a short bench — the sim will start an out-of-position player, call up a reserve, or even activate an injured player early rather than ever leave a lineup spot empty.',
    'A user-built team\'s lineup and rotation are followed exactly as set — the sim never auto-swaps or rests a player on a builder team the way it will for a real-season roster.',

    // INJURIES
    'Turn on injuries and players can land on the IL mid-season — the more a player actually played in real life, the healthier the sim assumes he is.',
    'A bench bat with a light real-life workload isn\'t assumed to be secretly injured — the model only reads "missed time" as an injury signal once a player has enough real playing time to make that comparison meaningful.',
    'Injury risk is capped every single game — even the most injury-prone player profile can never exceed a 1-in-4 chance of landing on the IL on any given day.',
    'Most simulated injuries are short — the model leans toward quick IL stints, with longer, season-altering injuries being the rare exception rather than the norm.',
    'The postseason never rolls new injuries — players can still return from the IL in October, but nobody gets hurt for the first time once the regular season ends.',

    // TEAMS AND SEASON STRUCTURE
    'Each team manages its own bullpen — closers get save chances, and every other reliever is picked by matchup leverage and how much they\'ve pitched recently.',
    'Standings, divisions, and the postseason format all mirror what was actually used that season — Wild Card, LCS, or straight to the World Series, depending on the year.',
    'Taking over a season swaps your team directly into a real club\'s spot — you inherit their exact schedule, division, and opponents for the year.',
    'By default, a season takeover offers you the worst team in baseball that year first — turning the season around is meant to be the challenge.',
    'MVP, Cy Young, Rookie of the Year, and Silver Slugger awards are handed out at the end of the season based on how it actually played out.',
    'The simulated MVP race isn\'t just about hitting — a small bump is baked in for defensive value and net stolen bases on top of the core offensive number.',
    'Cy Young voting in the sim weighs innings pitched alongside ERA, so a reliever with a tiny, sparkling sample can\'t outscore a true workhorse season.',
    'Silver Sluggers at left and right field are awarded based on which position a player actually logged more innings at that season — not just whatever position is printed on the card.',

    // WHAT THE SIM DOESN'T MODEL
    'The engine doesn\'t know what a groundout or flyout actually looked like — no batted-ball type, no fielder gets credited, so the play-by-play only ever says what genuinely happened, never invented detail.',
    'A player\'s handedness is on the card, but the sim doesn\'t play matchups off of it — there\'s no separate lineup logic for facing a lefty versus a righty.',
    'There\'s no weather, no park factors, and no crowd or travel fatigue applied during a game — every matchup comes down to what\'s printed on the two cards in play.',
    'Double plays are only ever turned on a ground ball with a runner on first — no line-drive double plays, no double plays started any other way.',
] as const;

const ROTATE_INTERVAL_MS = 5000;

/** Rotating "how the simulation works" facts, shown alongside `SimProgress` while a run is in flight. */
export function SimEngineExplainer() {
    const [index, setIndex] = useState(() => Math.floor(Math.random() * TIPS.length));

    useEffect(() => {
        const id = setInterval(() => {
            setIndex(prev => {
                if (TIPS.length <= 1) return prev;
                let next = Math.floor(Math.random() * TIPS.length);
                while (next === prev) next = Math.floor(Math.random() * TIPS.length);
                return next;
            });
        }, ROTATE_INTERVAL_MS);
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
