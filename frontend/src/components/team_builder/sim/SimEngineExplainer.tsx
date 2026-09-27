import { useEffect, useState } from 'react';
import { FaDice } from 'react-icons/fa6';

// PLAIN-LANGUAGE FACTS ABOUT THE SIMULATION ENGINE, SHOWN AT RANDOM WHILE THE USER WAITS FOR A
// RUN TO FINISH. THE LONG-FORM VERSION OF THESE LIVES IN
// `core/simulation/SIMULATION_GUIDE.md` (ALSO PLAYER-FACING). `core/simulation/README.md` IS THE
// SEPARATE DEVELOPER-FACING, FILE/CLASS-LEVEL DOC — NEITHER OF THOSE IS ABOUT HOW THIS COMPONENT
// IS BUILT, ONLY WHAT THE SIM ASSUMES AND CAN DO.
const TIPS = [
    // BUILDING THE SEASON, BEFORE A PITCH IS THROWN
    'Every player\'s card comes from an archive of historical MLB Showdown cards — the same one behind the Explore page — snapshotted daily if you\'re simming a season that\'s still in progress.',
    'You can optionally regress small-sample cards toward replacement level — blending a card\'s actual stats with an average replacement-level line so a tiny sample doesn\'t overperform all season.',
    'The schedule is pulled straight from the real MLB Stats API — same matchups, same days, same home/away splits as the year actually played out.',
    'Running a rest-of-season projection loads each club\'s real record as of the date you pick as its starting point, and only the games still left on the calendar actually get simulated.',
    'Trade-deadline moves only fire for players who were really traded that year, and only if they logged more than about 10 real games on each side of the deal — a September call-up or a paper spring-training move doesn\'t count as a real mid-season trade.',
    'A scheduled trade can still get cancelled mid-run — if the simulated standings have a "selling" club sitting within about 8 games of a playoff spot when the deadline hits, the deal is called off, because a club that close wouldn\'t really be selling.',
    'Rosters aren\'t built by just grabbing whoever\'s most valuable — every card is bucketed into a preferred tier (real playing time above a minimum) and a fallback tier, and the preferred tier always gets exhausted first.',
    'The active roster fills one position at a time, taking the most valuable eligible player left for that specific spot — eligibility comes from wherever a player actually earned real playing time that season, not anything the roster step re-measures.',
    'A backup catcher is a non-negotiable roster requirement — no team\'s roster ever quietly skips carrying one, no matter how the value math shakes out elsewhere.',
    'A season takeover drops your team directly into a real club\'s schedule, division, and opponents for the year — and skips the 40-man/injury system entirely, so your lineup, rotation, and bullpen play exactly as built, with no auto-resting or auto-swapping.',
    'Turn on injuries and every player gets a personalized profile — tuned so a guy who played almost every game is modeled as durable, and one who missed half the season is modeled as fragile, discounted until there\'s enough playing time to trust the comparison.',
    'However fragile a player\'s injury profile is, the odds of landing on the IL in any single game are capped at 25% — and most injuries that do happen are short, 3-10 day stints, with season-wrecking ones the rare exception on purpose.',

    // DAILY REST, LINEUPS, AND ROSTERS
    'There\'s no concept of a scheduled day off — every eligible player gets a rest score each game, and the highest score starts. An elite everyday player can go about 13 games between rest days; an equally valuable catcher tops out around 6-7, because the model treats the position itself as more physically demanding.',
    'That catcher rest discount follows a player around — someone eligible at catcher and another position still gets the catcher-sized rest gap every day, not just the days he actually catches.',
    'If a roster gets thin enough — injuries stacking up, a short bench — the sim will start someone out of position, call up a reserve, or even activate an injured player early rather than ever leave a lineup spot empty.',
    'Batting orders for real-season teams are built by need, not front-to-back: the 3-hole gets the best remaining OPS first, then cleanup gets the best remaining home-run rate, then leadoff gets the fastest remaining runner, and so on down the lineup.',
    'A builder team\'s explicit lineup order is used as-is — if one of those hitters gets bumped by the daily rest system, the leftover spots fill with the best remaining OPS, lowest open spot first.',
    'A starter\'s turn in the rotation is a fixed round robin all regular season long — whoever\'s next simply starts, with no rest check at all.',
    'Relievers work differently from starters — anyone who threw 2+ innings in the last 2 days is pulled from consideration entirely, and everyone else takes a fit-score penalty scaled to how much they\'ve thrown in the last 3 days.',
    'A closer\'s fit score gets cut in half outside of a 9th-inning-or-later save situation, so he naturally stays fresh for when a real save chance shows up.',
    'A builder team\'s designated starters get a large flat bonus to their daily rest score — big enough to almost always win the job, but not infinite. Enough games in a row without a break, and a fresher bench player can still out-score them for that day\'s start.',

    // THE AT-BAT ITSELF
    'Every plate appearance is two rolls: the pitch roll decides who\'s "in control" of the at-bat, and the swing roll — read against whoever won control\'s own chart — decides the result.',
    'If a swing roll lands above the top of a player\'s chart, it doesn\'t miss or reroll — it just resolves to the single best result printed on that chart.',
    'Both rolls sometimes get a small random wobble added on top — about 15% of pitch rolls and 35% of swing rolls — and bigger nudges get rarer the bigger they are.',
    'Handedness is off by default — a card performs identically against a lefty or a righty — but turning it on adds a fixed one-pip nudge toward whoever has the platoon advantage, on both the pitch roll and the swing roll.',
    'A switch hitter always counts as having the platoon advantage when handedness is turned on, no matter which arm is on the mound.',

    // BASERUNNING
    'On a single, double, or triple, every runner moves up exactly as many bases as the batter did. A 1B+ is a single where the batter also takes second automatically afterward — no throw, no roll — and it counts as that at-bat\'s one steal.',
    'A ground ball with a runner on first is always a force at second, and then a separate roll decides whether the batter\'s out at first too — a fast batter beats out a lot of double plays, and a slow one hits into a lot of them.',
    'If a double play is the third out of the inning, any run that crossed the plate on that same play gets wiped off the board.',
    'Steals, extra-base advances, and double plays are all pure dice — a defender\'s rating plus a d20 roll has to beat the runner\'s speed, so a runner\'s odds of being safe are roughly (his speed minus the defense\'s rating) divided by 20.',
    'Stealing third, or trying to take an extra base into it, gets a 5-point speed penalty for the added risk — while a runner sent home gets a +5 bonus, and +10 with two outs, since he was already off on contact.',
    'A team\'s real season stolen-base rate scales how often steals get attempted that year — a high-steal era plays out with visibly more attempts than a low-steal one.',
    'Even the fastest runner against the weakest arm tops out at roughly an 85% chance to even attempt a steal — nobody is ever a guaranteed green light, and a runner needs about an 8-point speed edge just to consider going at all.',
    'Sending a runner for an extra base isn\'t a random call like a steal — at a neutral manager setting, he\'s sent whenever his speed beats the outfield\'s defense by 10 or more, and only then does the actual safe-or-out roll happen.',

    // PITCHING FATIGUE AND THE BULLPEN
    'A pitcher\'s fatigue is purely innings actually thrown against his own card\'s printed innings rating — no pitch count at all — and every 3 runs he\'s allowed adds roughly another inning\'s worth of tiredness on top.',
    'A starter who\'s still under his printed innings limit is never pulled for fatigue, no matter how deep he\'s gone — but once he hits that limit, a start where he\'s allowed 1 run or fewer gets a fresh 35% chance every remaining plate appearance to stay in anyway.',
    'A pitcher getting hammered comes out early regardless of his innings rating — 5+ runs allowed, or 1.5+ runs per inning after at least a full inning of work, pulls him immediately.',
    'Bullpen selection scores every available reliever on how well the situation fits him — score margin, inning, and leverage — discounted by how much he\'s already thrown recently; it never reads whether he\'s been hot or cold, only workload.',
    'A "save situation" in the sim means the 9th inning or later with the pitching team ahead by any margin or tied — looser than the official rule — and a rested closer who hasn\'t pitched yet today comes in automatically when one comes up.',
    'Once a pitcher leaves a game he can\'t come back, and an empty bullpen means no relief at all — if every reliever is already unavailable, whoever\'s on the mound stays out there no matter how tired he is.',

    // KEEPING SCORE
    'Runs are charged to whoever actually put the runner on base, not whoever\'s on the mound when he scores — a reliever who inherits a runner and gives up a sac fly isn\'t charged with that run.',
    'The sim doesn\'t model errors at all, so every run in the box score is earned, and there\'s never an RBI credited on a double play.',
    'A live real-game takeover freezes the actual game where it stands — inning, outs, runners, score, and every pitcher\'s innings and runs allowed so far all carry over — and plays out the rest under the exact same rules.',

    // MANAGER STYLE AND THE POSTSEASON
    'Each club can optionally get its own manager, dialed 1-to-5 on steal aggression, baserunning aggression, bullpen hook, and closer usage — leaving every team at the neutral middle setting is a total no-op that plays exactly like a run with no manager dial at all.',
    'The manager dial only ever changes whether a team tries something — stealing, sending a runner, pulling a pitcher, using the closer — never the underlying odds that the attempt actually succeeds.',
    'October has one big rule change: injuries stop happening for the first time (players can still return from the IL), and the fixed rotation gives way to genuine rest — the best-ranked starter with at least 4 days off gets the ball instead of just whoever\'s next in line.',

    // AWARDS
    'MVP leans on overall offensive value scaled by playing time, with a small bonus for defensive value and net stolen bases — not just raw counting stats.',
    'Cy Young is built around runs saved versus a league-average pitcher, scaled by innings pitched — specifically so a reliever who was brilliant in a tiny sample can\'t outrank a true workhorse starter\'s full season.',
    'Silver Sluggers at the outfield corners go by whichever position — left or right — a player actually logged more playing time at that specific season, not whatever\'s printed on his card.',
    'Rookie of the Year has no formula of its own — it reuses the MVP score for rookie hitters and the Cy Young score for rookie pitchers, then ranks each rookie by percentile against the entire qualified league at his own type.',

    // WHAT THE SIM DELIBERATELY DOESN'T MODEL
    'The engine doesn\'t model errors, so the box score always shows zero — and there are no in-game position-player substitutions: no pinch hitters, pinch runners, or defensive replacements.',
    'There are no matchup-based pitching changes in the sim — a pitcher only ever leaves because he\'s tired or getting hit hard, never because of who\'s coming up to bat.',
    'There\'s no weather, no park factors, and no sacrifice bunts, intentional walks, hit-and-runs, or pickoffs — every matchup comes down to what\'s printed on the two cards in play plus the dice.',
    'There\'s no automatic runner on second in extra innings, and no tie games, whatever era is being played — extras go as long as they need to.',
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
        <div className="w-full max-w-lg flex items-start gap-2.5 px-3.5 py-3 rounded-lg border border-(--divider) bg-(--background-secondary)">
            <FaDice className="text-tertiary text-sm mt-0.5 shrink-0" />
            {/* Keyed so each rotation remounts the paragraph and replays the fade, rather than
                the text swapping in place mid-read. */}
            <p key={index} className="fade-in text-[12px] leading-relaxed text-secondary">
                {TIPS[index]}
            </p>
        </div>
    );
}
