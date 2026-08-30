import { useEffect, useMemo, useState } from 'react';
import { FaSpinner, FaTriangleExclamation, FaTerminal } from 'react-icons/fa6';
import { Modal } from '../shared/Modal';
import FormDropdown from '../customs/FormDropdown';
import ManagerStyleFields from '../simulate/ManagerStyleFields';
import { NEUTRAL_MANAGER, managerPayload, type ManagerPreference } from '../../api/manager';
import { ordinal } from '../../functions/formatters';
import {
    fetchGameSimSetup,
    type SimGameLineupSlot,
    type SimGamePlayerOption,
    type SimGameSetup,
    type SimGameTeamSetup,
    type StartGameSimPayload,
} from '../../api/simGame';

function errorMessage(err: unknown): string {
    return err instanceof Error ? err.message : String(err);
}

/** Human summary of the state a takeover picks up from, e.g. "Bot 5th, 2 out, runners on 1st and 3rd". */
function takeoverSummary(setup: SimGameSetup): string | null {
    const state = setup.start_state;
    if (!state) return null;

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

/** A batting-order row: one dropdown over every eligible position player on that side. */
function LineupRow({
    slot, options, onChange,
}: {
    slot: SimGameLineupSlot;
    options: SimGamePlayerOption[];
    onChange: (playerId: string) => void;
}) {
    const selected = options.find((option) => option.player_id === slot.player_id);
    return (
        <div className="flex items-center gap-2">
            <span className="w-5 shrink-0 text-right text-xs font-bold text-(--secondary)">{slot.batting_order}</span>
            <FormDropdown
                label=""
                className="flex-1 min-w-0"
                options={options.map((option) => ({
                    label: `${option.name} · ${option.position || '—'} · ${option.points} pts`,
                    value: option.player_id,
                }))}
                selectedOption={slot.player_id}
                onChange={onChange}
            />
            <span className="w-10 shrink-0 text-xs font-semibold text-(--secondary)">{slot.position || '—'}</span>
            {selected?.card_origin === 'REPLACEMENT' && (
                <span title="No Showdown card exists for this player — a replacement-level card is used.">
                    <FaTriangleExclamation className="text-(--warning)" />
                </span>
            )}
        </div>
    );
}

function TeamPanel({
    team, manager, onLineupChange, onStarterChange, onManagerChange,
}: {
    team: SimGameTeamSetup;
    manager: ManagerPreference;
    onLineupChange: (battingOrder: number, playerId: string) => void;
    onStarterChange: (playerId: string) => void;
    onManagerChange: (next: ManagerPreference) => void;
}) {
    // A player already in the order can't also fill another spot, so each dropdown offers the
    // unused pool plus whoever currently holds that spot.
    const takenIds = useMemo(() => new Set(team.lineup.map((slot) => slot.player_id)), [team.lineup]);
    const available = team.position_players.filter((option) => !option.is_unavailable);

    return (
        <div className="flex-1 min-w-0 space-y-3">
            <div className="flex items-center gap-2">
                <span
                    className="h-3 w-3 rounded-full border border-(--divider)"
                    style={{ backgroundColor: team.identity.primary_color ?? undefined }}
                />
                <span className="text-sm font-bold text-(--primary)">{team.identity.name}</span>
            </div>

            <FormDropdown
                label="Starting Pitcher"
                options={team.bullpen.map((option) => ({
                    label: `${option.name} · ${option.points} pts${option.ip ? ` · ${option.ip} IP` : ''}`,
                    value: option.player_id,
                }))}
                selectedOption={team.starting_pitcher_id}
                onChange={onStarterChange}
            />

            {team.lineup.length > 0 ? (
                <div className="space-y-1.5">
                    <div className="text-xs font-bold uppercase tracking-wide text-(--secondary)">Lineup</div>
                    {team.lineup.map((slot) => (
                        <LineupRow
                            key={slot.batting_order}
                            slot={slot}
                            options={available.filter(
                                (option) => option.player_id === slot.player_id || !takenIds.has(option.player_id),
                            )}
                            onChange={(playerId) => onLineupChange(slot.batting_order, playerId)}
                        />
                    ))}
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
 * Reviews (and optionally edits) the lineups a game will be simulated with, then starts it.
 *
 * Handles both entry points: a game that hasn't started plays all nine innings, and one already
 * in progress is taken over from the state shown in the banner. The distinction comes from the
 * setup's `is_takeover`, not from the caller.
 */
export default function GameSimSetupModal({ gamePk, showdownSet, onCancel, onStart }: Props) {
    const [setup, setSetup] = useState<SimGameSetup | null>(null);
    // Starts true rather than being flipped inside the effect: the fetch is keyed on props that
    // never change while the modal is mounted, so there is only ever one load.
    const [loading, setLoading] = useState(true);
    const [starting, setStarting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [managers, setManagers] = useState<{ away: ManagerPreference; home: ManagerPreference }>({
        away: NEUTRAL_MANAGER, home: NEUTRAL_MANAGER,
    });

    useEffect(() => {
        const controller = new AbortController();
        fetchGameSimSetup(gamePk, showdownSet, controller.signal)
            .then(setSetup)
            .catch((err) => { if (!controller.signal.aborted) setError(errorMessage(err)); })
            .finally(() => { if (!controller.signal.aborted) setLoading(false); });
        return () => controller.abort();
    }, [gamePk, showdownSet]);

    /** Swap a batting-order spot. The position follows the player, so the defense stays coherent. */
    function changeLineup(side: 'away' | 'home', battingOrder: number, playerId: string) {
        setSetup((current) => {
            if (!current) return current;
            const team = current[side];
            const option = team.position_players.find((candidate) => candidate.player_id === playerId);
            return {
                ...current,
                [side]: {
                    ...team,
                    lineup: team.lineup.map((slot) =>
                        slot.batting_order === battingOrder
                            ? { ...slot, player_id: playerId, name: option?.name ?? '', position: option?.position ?? slot.position }
                            : slot,
                    ),
                },
            };
        });
    }

    function changeStarter(side: 'away' | 'home', playerId: string) {
        setSetup((current) => (current ? { ...current, [side]: { ...current[side], starting_pitcher_id: playerId } } : current));
    }

    async function handleStart() {
        if (!setup) return;
        setStarting(true);
        setError(null);
        try {
            await onStart({
                set: setup.showdown_set,
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

    const summary = setup ? takeoverSummary(setup) : null;
    const title = setup?.is_takeover ? 'Take Over This Game' : 'Simulate This Game';

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
                            className="flex cursor-pointer items-center gap-1.5 rounded-lg bg-(--secondary) px-3 py-2 text-[12px] font-bold text-(--background-primary) transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                        >
                            {starting ? <FaSpinner className="animate-spin text-[10px]" /> : <FaTerminal className="text-[15px]" />}
                            {starting ? 'Simulating…' : setup?.is_takeover ? 'Take Over' : 'Simulate'}
                        </button>
                    </div>
                </div>
            )}
        >
            <div className="p-4 space-y-4">
                {loading && (
                    <div className="flex items-center justify-center gap-2 py-10 text-(--secondary)">
                        <FaSpinner className="animate-spin" /> Loading lineups…
                    </div>
                )}

                {setup && (
                    <>
                        {summary && (
                            <div className="rounded-xl border border-(--divider) bg-(--background-secondary) p-3">
                                <div className="text-xs font-bold uppercase tracking-wide text-(--secondary)">Taking over from</div>
                                <div className="text-sm font-semibold text-(--primary)">
                                    {summary}
                                    {' · '}
                                    {setup.away.identity.abbreviation} {setup.start_state?.away.runs_scored}
                                    {' – '}
                                    {setup.home.identity.abbreviation} {setup.start_state?.home.runs_scored}
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
                                onLineupChange={(order, id) => changeLineup('away', order, id)}
                                onStarterChange={(id) => changeStarter('away', id)}
                                onManagerChange={(next) => setManagers((m) => ({ ...m, away: next }))}
                            />
                            <TeamPanel
                                team={setup.home}
                                manager={managers.home}
                                onLineupChange={(order, id) => changeLineup('home', order, id)}
                                onStarterChange={(id) => changeStarter('home', id)}
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
                    </>
                )}

                
            </div>
        </Modal>
    );
}
