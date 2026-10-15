import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaArrowRotateRight, FaForward, FaPenToSquare, FaPlay, FaShuffle, FaSpinner, FaTrophy } from 'react-icons/fa6';
import { SimResult } from '../../team_builder/sim/SimResult';
import { TeamChip } from '../../shared/TeamChip';
import {
    fetchSeason, runItBack, simSeason, startDraft, startSeason,
    type League, type SeasonPayload, type SimTarget,
} from '../../../api/leagues';
import { usePolling } from '../../../hooks/usePolling';
import {
    ERROR_BOX_CLASS, PRIMARY_BUTTON_CLASS, SECONDARY_BUTTON_CLASS, SECTION_LABEL_CLASS, errorMessage, leagueTeamIdentity,
} from '../leagueUi';
import { SeasonConfigForm } from './SeasonConfigForm';

const RUNNING_POLL_MS = 1500;
const IDLE_POLL_MS = 15000;

const SIM_BUTTONS: Record<'regular' | 'postseason', { target: SimTarget; label: string }[]> = {
    regular: [
        { target: 'day', label: 'Sim day' },
        { target: 'week', label: 'Sim week' },
        { target: 'regular_end', label: 'To end of season' },
        { target: 'postseason_end', label: 'To a champion' },
    ],
    postseason: [
        { target: 'day', label: 'Sim day' },
        { target: 'round', label: 'Finish round' },
        { target: 'postseason_end', label: 'To a champion' },
    ],
};

type Props = {
    league: League;
    seasonNumber: number;
    token: string;
    myMemberId: string | null;
    isCommissioner: boolean;
    /** True for a past season opened from History - no setup or sim controls. */
    readOnly?: boolean;
    /** The season moved on (started, new season created) - the league page refetches. */
    onLeagueChange: () => void;
};

/** One season: setup before it starts, then sim controls over the standard season result view. */
export function LeagueSeasonTab({ league, seasonNumber, token, myMemberId, isCommissioner, readOnly = false, onLeagueChange }: Props) {
    const navigate = useNavigate();
    const [busy, setBusy] = useState<string | null>(null);
    const [actionError, setActionError] = useState<string | null>(null);
    const [isRunning, setIsRunning] = useState(false);

    const { data, setData, error, refresh } = usePolling<SeasonPayload>(
        () => fetchSeason(token, league.league_id, seasonNumber),
        readOnly ? null : isRunning ? RUNNING_POLL_MS : IDLE_POLL_MS,
        [league.league_id, seasonNumber, token],
    );
    const season = data?.season ?? null;
    const teams = data?.teams ?? [];
    const running = season?.job_status === 'running';
    if (running !== isRunning) setIsRunning(running);
    const [focusAbbr, setFocusAbbr] = useState<string | undefined>();

    // A chunk just finished: the league page's status/tabs may need to catch up (e.g. complete)
    const wasRunning = useRef(false);
    useEffect(() => {
        if (wasRunning.current && !running) onLeagueChange();
        wasRunning.current = running;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [running]);

    const myTeam = teams.find(t => t.member_id === myMemberId) ?? null;
    const canManage = isCommissioner && !readOnly;

    const inProgressLabel = useMemo(() => {
        if (!season || season.status === 'complete') return undefined;
        if (season.status === 'postseason') return 'Postseason in progress';
        const records = Object.values(season.summary?.standings.divisions ?? {}).flat();
        const played = Math.max(0, ...records.map(r => r.wins + r.losses));
        return `Regular season · ${played} of ${season.config.games_per_team ?? '?'} games`;
    }, [season]);

    async function act(key: string, action: () => Promise<void>) {
        setBusy(key);
        setActionError(null);
        try {
            await action();
        } catch (err) {
            setActionError(errorMessage(err));
        } finally {
            setBusy(null);
        }
    }

    const sim = (target: SimTarget) => act(`sim-${target}`, async () => {
        setData(await simSeason(token, league.league_id, seasonNumber, target));
        setIsRunning(true);
    });

    if (!season) {
        return error ? <div className={ERROR_BOX_CLASS}>{error}</div> : <SeasonSkeleton />;
    }

    const champion = season.champion_team_id ? teams.find(t => t.team_id === season.champion_team_id) : null;
    const mvp = season.awards?.mvp?.[0]?.player.name;

    return (
        <div className="flex flex-col gap-5">
            {/* BEFORE THE SEASON: SETTINGS, LINEUPS, START */}
            {(season.status === 'drafting' || season.status === 'setup') && (
                <>
                    {season.status === 'drafting' && (
                        <p className="text-[13px] text-(--text-secondary)">The season can start once the draft is done. The commissioner can set the schedule now.</p>
                    )}
                    <SeasonConfigForm
                        token={token}
                        leagueId={league.league_id}
                        seasonNumber={seasonNumber}
                        initial={season.config}
                        teamCount={teams.length}
                        canEdit={canManage}
                        onSaved={refresh}
                    />
                    {season.status === 'setup' && (
                        <section className="flex flex-col gap-2">
                            <div className={SECTION_LABEL_CLASS}>Teams</div>
                            <p className="text-[12px] text-(--text-secondary)">
                                Set your lineup, rotation and team name before the season starts. Your abbreviation is locked once it does.
                            </p>
                            <div className="flex flex-col rounded-xl border border-(--divider) divide-y divide-(--divider) overflow-hidden">
                                {teams.map(team => (
                                    <div key={team.team_id} className="flex items-center gap-3 px-3 py-2 bg-(--background-secondary)">
                                        <TeamChip team={leagueTeamIdentity(team)} />
                                        <div className="flex-1 min-w-0">
                                            <div className="text-[13px] font-bold text-(--text-primary) truncate">{team.name}</div>
                                            <div className="text-[11px] text-(--text-tertiary)">{team.display_name}</div>
                                        </div>
                                        {team.member_id === myMemberId && (
                                            <button type="button" onClick={() => navigate(`/teams/${team.team_id}`)} className={SECONDARY_BUTTON_CLASS}>
                                                <FaPenToSquare /> Edit lineup
                                            </button>
                                        )}
                                    </div>
                                ))}
                            </div>
                            {canManage && (
                                <div className="flex flex-col items-start gap-1 pt-1">
                                    <button type="button" onClick={() => act('start', async () => { await startSeason(token, league.league_id, seasonNumber); await refresh(); onLeagueChange(); })} disabled={busy !== null} className={PRIMARY_BUTTON_CLASS}>
                                        {busy === 'start' ? <FaSpinner className="animate-spin" /> : <FaPlay className="text-[10px]" />}
                                        Start Season
                                    </button>
                                    <span className="text-[11px] text-(--text-tertiary)">Writes the schedule. Settings above lock once the season starts.</span>
                                </div>
                            )}
                        </section>
                    )}
                </>
            )}

            {/* CHAMPION */}
            {season.status === 'complete' && champion && (
                <div className="flex items-center gap-3 rounded-2xl border border-(--success)/30 bg-linear-to-b from-(--success)/20 to-(--success)/5 px-4 py-3">
                    <FaTrophy className="text-[28px] text-(--secondary) shrink-0" />
                    <div className="flex-1 min-w-0">
                        <div className="text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary)">Season {season.season_number} champion</div>
                        <div className="flex items-center gap-2">
                            <TeamChip team={leagueTeamIdentity(champion)} />
                            <span className="text-[18px] font-black text-(--text-primary) truncate">{champion.name}</span>
                        </div>
                        <div className="text-[11px] text-(--text-secondary)">{champion.display_name}{mvp ? ` · MVP ${mvp}` : ''}</div>
                    </div>
                </div>
            )}

            {/* NEXT SEASON */}
            {season.status === 'complete' && canManage && (
                <section className="flex flex-col gap-2">
                    <div className={SECTION_LABEL_CLASS}>Next season</div>
                    <div className="flex flex-wrap gap-2">
                        <button type="button" onClick={() => act('again', async () => { await runItBack(token, league.league_id); onLeagueChange(); })} disabled={busy !== null} className={PRIMARY_BUTTON_CLASS}>
                            {busy === 'again' ? <FaSpinner className="animate-spin" /> : <FaArrowRotateRight />}
                            Run it back
                        </button>
                        <button type="button" onClick={() => act('redraft', async () => { await startDraft(token, league.league_id, seasonNumber + 1); onLeagueChange(); })} disabled={busy !== null} className={SECONDARY_BUTTON_CLASS}>
                            {busy === 'redraft' ? <FaSpinner className="animate-spin" /> : <FaShuffle />}
                            Redraft
                        </button>
                    </div>
                    <span className="text-[11px] text-(--text-tertiary)">Run it back keeps every team's roster. Redraft starts a new draft from empty teams.</span>
                </section>
            )}

            {/* SIM CONTROLS */}
            {(season.status === 'regular' || season.status === 'postseason') && !readOnly && (
                <section className="flex flex-col gap-2">
                    {canManage && (
                        <div className="flex flex-wrap gap-2">
                            {SIM_BUTTONS[season.status].map(({ target, label }, i) => (
                                <button key={target} type="button" onClick={() => sim(target)} disabled={running || busy !== null} className={i === 0 ? PRIMARY_BUTTON_CLASS : SECONDARY_BUTTON_CLASS}>
                                    {busy === `sim-${target}` ? <FaSpinner className="animate-spin" /> : <FaForward className="text-[10px]" />}
                                    {label}
                                </button>
                            ))}
                        </div>
                    )}
                    {running && (
                        <div className="flex flex-col gap-1">
                            <div className="h-2 rounded-full bg-(--background-tertiary) overflow-hidden">
                                <div
                                    className="h-full bg-(--secondary) transition-[width] duration-500"
                                    style={{ width: `${season.job_total ? Math.min(100, (season.job_progress / season.job_total) * 100) : 5}%` }}
                                />
                            </div>
                            <span className="text-[11px] text-(--text-tertiary)">Simulating games…</span>
                        </div>
                    )}
                    {season.job_status === 'failed' && season.job_error && <div className={ERROR_BOX_CLASS}>{season.job_error}</div>}
                    {!canManage && !running && <p className="text-[11px] text-(--text-tertiary)">The commissioner sims the games. You can change your lineup between sims.</p>}
                    {myTeam && !running && (
                        <div>
                            <button type="button" onClick={() => navigate(`/teams/${myTeam.team_id}`)} className={SECONDARY_BUTTON_CLASS}>
                                <FaPenToSquare /> Edit my lineup
                            </button>
                        </div>
                    )}
                </section>
            )}

            {actionError && <div className={ERROR_BOX_CLASS}>{actionError}</div>}

            {/* RESULTS SO FAR */}
            {season.summary ? (
                <div className="-mx-4 md:-mx-8">
                    <SimResult
                        summary={season.summary}
                        focusAbbr={focusAbbr ?? myTeam?.abbreviation}
                        onFocusChange={setFocusAbbr}
                        inProgressLabel={inProgressLabel}
                    />
                </div>
            ) : (season.status === 'regular' && (
                <p className="text-[13px] text-(--text-tertiary) py-6 text-center">No games played yet.</p>
            ))}
        </div>
    );
}

function SeasonSkeleton() {
    return (
        <div className="flex flex-col gap-3 animate-pulse">
            <div className="h-10 w-72 rounded-lg bg-(--background-secondary)" />
            <div className="h-24 rounded-xl bg-(--background-secondary)" />
            <div className="h-64 rounded-xl bg-(--background-secondary)" />
        </div>
    );
}
