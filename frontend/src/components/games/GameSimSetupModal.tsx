import { useEffect, useState } from 'react';
import { FaSpinner, FaTriangleExclamation, FaTerminal } from 'react-icons/fa6';
import { Modal } from '../shared/Modal';
import ManagerStyleFields from '../simulate/ManagerStyleFields';
import { NEUTRAL_MANAGER, managerPayload, type ManagerPreference } from '../../api/manager';
import { ordinal } from '../../functions/formatters';
import {
    fetchGameSimSetup,
    type SimGameLineupSlot,
    type SimGameSetup,
    type SimGameStartState,
    type SimGameTeamSetup,
    type StartGameSimPayload,
} from '../../api/simGame';

function errorMessage(err: unknown): string {
    return err instanceof Error ? err.message : String(err);
}

/**
 * Human summary of the state a simulation picks up from, e.g. "Bot 5th, 2 out, runners on 1st
 * and 3rd". A missing state means the beginning of the game rather than nothing to show - a
 * preview game and a "from beginning" takeover both start at the first pitch.
 */
function startStateSummary(state: SimGameStartState | null | undefined): string {
    if (!state) return 'Top 1st, 0 outs, bases empty';

    const half = `${state.is_top ? 'Top' : 'Bot'} ${ordinal(state.inning)}`;
    const outs = `${state.outs} out${state.outs === 1 ? '' : 's'}`;

    const bases = state.runners.runners
        .map((runner) => runner.base)
        .sort((a, b) => a - b)
        .map((base) => ordinal(base));
    let onBase = 'bases empty';
    if (bases.length === 3) onBase = 'bases loaded';
    else if (bases.length === 2) onBase = `runners on ${bases[0]} and ${bases[1]}`;
    else if (bases.length === 1) onBase = `runner on ${bases[0]}`;

    return `${half}, ${outs}, ${onBase}`;
}

/** A read-only batting-order row: number, player, position, card points, and a replacement-card flag. */
function LineupRow({ slot, points, isReplacement }: { slot: SimGameLineupSlot; points: number | null; isReplacement: boolean }) {
    return (
        <div className="flex items-center gap-2 text-xs">
            <span className="w-5 shrink-0 text-right font-bold text-(--secondary)">{slot.batting_order}</span>
            <span className="flex-1 min-w-0 truncate font-semibold text-(--primary)">{slot.name || '—'}</span>
            <span className="w-10 shrink-0 font-semibold text-(--secondary)">{slot.position || '—'}</span>
            <span className="w-14 shrink-0 text-right font-semibold text-(--secondary)">{points != null ? `${points} pts` : '—'}</span>
            {isReplacement && (
                <span title="No Showdown card exists for this player — a replacement-level card is used.">
                    <FaTriangleExclamation className="text-(--warning)" />
                </span>
            )}
        </div>
    );
}

function TeamPanel({
    team, manager, onManagerChange,
}: {
    team: SimGameTeamSetup;
    manager: ManagerPreference;
    onManagerChange: (next: ManagerPreference) => void;
}) {
    const optionsById = new Map(team.position_players.map((option) => [option.player_id, option]));
    const starter = team.bullpen.find((option) => option.player_id === team.starting_pitcher_id);

    return (
        <div className="flex-1 min-w-0 space-y-3">
            <div className="flex items-center gap-2">
                <span
                    className="h-3 w-3 rounded-full border border-(--divider)"
                    style={{ backgroundColor: team.identity.primary_color ?? undefined }}
                />
                <span className="text-sm font-bold text-(--primary)">{team.identity.name}</span>
            </div>

            <div className="space-y-1">
                <div className="text-xs font-bold uppercase tracking-wide text-(--secondary)">Starting Pitcher</div>
                <div className="text-xs font-semibold text-(--primary)">
                    {starter ? `${starter.name} · ${starter.points} pts${starter.ip ? ` · ${starter.ip} IP` : ''}` : '—'}
                </div>
            </div>

            {team.lineup.length > 0 ? (
                <div className="space-y-1.5">
                    <div className="text-xs font-bold uppercase tracking-wide text-(--secondary)">Lineup</div>
                    {team.lineup.map((slot) => {
                        const option = optionsById.get(slot.player_id);
                        return (
                            <LineupRow
                                key={slot.batting_order}
                                slot={slot}
                                points={option?.points ?? null}
                                isReplacement={option?.card_origin === 'REPLACEMENT'}
                            />
                        );
                    })}
                </div>
            ) : (
                <div className="rounded-lg border border-(--divider) p-3 text-xs text-(--secondary)">
                    No lineup has been posted yet. The simulation will pick one from the active roster.
                </div>
            )}

            <ManagerStyleFields title="Manager style" value={manager} onChange={onManagerChange} />
        </div>
    );
}

type Props = {
    gamePk: number;
    /** The card set the game page is already displaying — the sim uses the same one. */
    showdownSet: string;
    onCancel: () => void;
    onStart: (payload: StartGameSimPayload) => Promise<void>;
};

/**
 * Reviews the lineups a game will be simulated with, then starts it.
 *
 * Handles both entry points: a game that hasn't started plays all nine innings, and one already
 * in progress defaults to a takeover from the state shown in the banner - though `fromBeginning`
 * lets the user opt a live game back into a full nine-inning replay with the original starters.
 */
export default function GameSimSetupModal({ gamePk, showdownSet, onCancel, onStart }: Props) {
    const [setup, setSetup] = useState<SimGameSetup | null>(null);
    const [loading, setLoading] = useState(true);
    const [starting, setStarting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [managers, setManagers] = useState<{ away: ManagerPreference; home: ManagerPreference }>({
        away: NEUTRAL_MANAGER, home: NEUTRAL_MANAGER,
    });
    // Only meaningful once `setup` comes back and shows the game is actually in progress - a
    // preview game has nothing to take over from, so this stays false and unused for it.
    const [fromBeginning, setFromBeginning] = useState(false);

    useEffect(() => {
        const controller = new AbortController();
        setLoading(true);
        setError(null);
        fetchGameSimSetup(gamePk, showdownSet, { fromBeginning, signal: controller.signal })
            .then(setSetup)
            .catch((err) => { if (!controller.signal.aborted) setError(errorMessage(err)); })
            .finally(() => { if (!controller.signal.aborted) setLoading(false); });
        return () => controller.abort();
    }, [gamePk, showdownSet, fromBeginning]);

    async function handleStart() {
        if (!setup) return;
        setStarting(true);
        setError(null);
        try {
            await onStart({
                set: setup.showdown_set,
                from_beginning: fromBeginning,
                away: {
                    lineup: setup.away.lineup.map((slot) => ({ player_id: slot.player_id, position: slot.position })),
                    starting_pitcher_id: setup.away.starting_pitcher_id,
                    manager: managerPayload(managers.away),
                },
                home: {
                    lineup: setup.home.lineup.map((slot) => ({ player_id: slot.player_id, position: slot.position })),
                    starting_pitcher_id: setup.home.starting_pitcher_id,
                    manager: managerPayload(managers.home),
                },
            });
        } catch (err: unknown) {
            setError(errorMessage(err));
            setStarting(false);
        }
    }

    const title = setup?.is_takeover ? 'Take Over This Game' : 'Simulate This Game';
    // `is_final` never flips back once the game hasn't started, and a preview game can't offer a
    // takeover, so the toggle only needs to show once we've seen a live/takeover-capable setup.
    const canOfferTakeover = setup ? setup.is_takeover || fromBeginning : false;

    return (
        <Modal 
            title={title} 
            size="xl" 
            onClose={onCancel}
            footer={(
                <div className="space-y-1">
                    {error && (
                        <div className="rounded-lg border border-(--red)/30 bg-(--red)/5 px-3 py-2 text-[12px] text-(--red)">
                            {error}
                        </div>
                    )}

                    <div className="flex justify-end gap-2">
                        <button
                            type="button"
                            onClick={onCancel}
                            className="cursor-pointer rounded-lg bg-tertiary px-3 py-2 text-[12px] font-semibold text-(--secondary) transition-colors hover:text-(--primary)"
                        >
                            Cancel
                        </button>
                        <button
                            type="button"
                            onClick={handleStart}
                            disabled={!setup || starting || setup.is_final}
                            className="flex cursor-pointer items-center gap-1.5 rounded-lg animated-showdown-gradient px-3 py-2 text-[12px] font-bold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                        >
                            {starting ? <FaSpinner className="animate-spin text-[10px]" /> : <FaTerminal className="text-[15px]" />}
                            {starting ? 'Simulating…' : setup?.is_takeover ? 'Take Over' : 'Simulate'}
                        </button>
                    </div>
                </div>
            )}
        >
            <div className="p-4 space-y-4">
                {canOfferTakeover && (
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-bold uppercase tracking-wide text-(--secondary)">Start from</span>
                        <div className="inline-flex rounded-lg border border-(--divider) bg-(--background-secondary) p-0.5">
                            <button
                                type="button"
                                onClick={() => setFromBeginning(false)}
                                disabled={loading}
                                className={`cursor-pointer rounded-md px-3 py-1 text-[12px] font-semibold transition-colors disabled:cursor-not-allowed ${
                                    !fromBeginning ? 'animated-showdown-gradient text-white' : 'text-(--secondary) hover:text-(--primary)'
                                }`}
                            >
                                Current State
                            </button>
                            <button
                                type="button"
                                onClick={() => setFromBeginning(true)}
                                disabled={loading}
                                className={`cursor-pointer rounded-md px-3 py-1 text-[12px] font-semibold transition-colors disabled:cursor-not-allowed ${
                                    fromBeginning ? 'animated-showdown-gradient text-white' : 'text-(--secondary) hover:text-(--primary)'
                                }`}
                            >
                                Beginning of Game
                            </button>
                        </div>
                        {loading && <FaSpinner className="animate-spin text-xs text-(--secondary)" />}
                    </div>
                )}

                {loading && !setup && (
                    <div className="flex items-center justify-center gap-2 py-10 text-(--secondary)">
                        <FaSpinner className="animate-spin" /> Loading lineups…
                    </div>
                )}

                {setup && (
                    <div className={loading ? 'space-y-4 opacity-50' : 'space-y-4'}>
                        {canOfferTakeover && (
                            <div className="rounded-xl border border-(--divider) bg-(--background-secondary) p-3">
                                <div className="text-xs font-bold uppercase tracking-wide text-(--secondary)">
                                    {setup.is_takeover ? 'Taking over from' : 'Starting from'}
                                </div>
                                <div className="text-sm font-semibold text-(--primary)">
                                    {startStateSummary(setup.start_state)}
                                    {' · '}
                                    {setup.away.identity.abbreviation} {setup.start_state?.away.runs_scored ?? 0}
                                    {' – '}
                                    {setup.home.identity.abbreviation} {setup.start_state?.home.runs_scored ?? 0}
                                </div>
                            </div>
                        )}

                        {setup.lineup_source === 'AUTO' && !setup.is_takeover && (
                            <div className="rounded-xl border border-(--divider) p-3 text-xs text-(--secondary)">
                                Lineups have not been posted for this game yet. Starting pitchers are the announced
                                probables; the batting orders will be chosen from each active roster.
                            </div>
                        )}

                        <div className="flex flex-col gap-6 md:flex-row">
                            <TeamPanel
                                team={setup.away}
                                manager={managers.away}
                                onManagerChange={(next) => setManagers((m) => ({ ...m, away: next }))}
                            />
                            <TeamPanel
                                team={setup.home}
                                manager={managers.home}
                                onManagerChange={(next) => setManagers((m) => ({ ...m, home: next }))}
                            />
                        </div>

                        {setup.warnings.length > 0 && (
                            <ul className="space-y-1 text-xs text-(--secondary)">
                                {setup.warnings.map((warning) => (
                                    <li key={warning} className="flex items-start gap-2">
                                        <FaTriangleExclamation className="mt-0.5 shrink-0 text-(--warning)" />
                                        <span>{warning}</span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                )}
            </div>
        </Modal>
    );
}
