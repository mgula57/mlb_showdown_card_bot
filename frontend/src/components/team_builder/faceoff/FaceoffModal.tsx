import { useEffect, useMemo, useState } from 'react';
import { FaSpinner } from 'react-icons/fa6';

import { startFaceoff } from '../../../api/faceoff';
import { NEUTRAL_MANAGER, managerPayload, type ManagerPreference } from '../../../api/manager';
import { fetchPublicTeams, fetchTeam, fetchUserTeams, ROTATION_ROLES, type Team, type TeamSummary } from '../../../api/userTeams';
import { useCardMap } from '../../../hooks/useCardMap';
import FormDropdown from '../../customs/FormDropdown';
import { EmptyState } from '../../shared/EmptyState';
import { InlineError } from '../../shared/InlineError';
import { Modal } from '../../shared/Modal';
import { Tabs, type TabItem } from '../../shared/Tabs';
import { buttonClass } from '../../shared/buttonStyles';
import ManagerStyleFields from '../../simulate/ManagerStyleFields';
import { TeamCard } from '../TeamCard';
import { TeamSearchInput } from '../TeamSearchInput';

type PickerTab = 'mine' | 'public';
const PICKER_TABS: TabItem<PickerTab>[] = [
    { id: 'mine', label: 'My Teams' },
    { id: 'public', label: 'Public Teams' },
];
const PUBLIC_RESULT_LIMIT = 30;
const SEARCH_DEBOUNCE_MS = 300;
const MANAGER_DESCRIPTION = 'Sets how this club manages for this Faceoff.';

const isPlayable = (team: TeamSummary) => !team.is_drafting && !team.is_archived && (team.source === 'user' || team.source === 'official');

const rotationOf = (team: Team | null) => (team?.rotation ?? []).filter(r => (ROTATION_ROLES as readonly string[]).includes(r.role));

const hasSameSets = (a: Team, b: Team) => {
    const key = (team: Team) => [...(team.allowed_sets ?? [])].sort().join(',');
    return key(a) === key(b);
};

type Props = {
    /** The team whose page this opened from. */
    team: Team;
    isOwnTeam: boolean;
    token: string;
    /** A Faceoff plays the saved roster, so the page saves any pending edit first. */
    onBeforeStart: () => Promise<void>;
    onClose: () => void;
    onStarted: (faceoffId: string) => void;
};

/** Starts a Faceoff from a team's page. From your own team you choose who to face; from someone
 *  else's you choose which of your teams faces it. When you own both, you manage both sides. */
export function FaceoffModal({ team, isOwnTeam, token, onBeforeStart, onClose, onStarted }: Props) {
    const [myTeams, setMyTeams] = useState<TeamSummary[] | null>(null);
    const [publicTeams, setPublicTeams] = useState<TeamSummary[] | null>(null);
    const [tab, setTab] = useState<PickerTab>('mine');
    const [query, setQuery] = useState('');
    const [picked, setPicked] = useState<Team | null>(null);
    const [starters, setStarters] = useState<{ challenger?: string; opponent?: string }>({});
    const [manager, setManager] = useState<ManagerPreference>(NEUTRAL_MANAGER);
    const [opponentManager, setOpponentManager] = useState<ManagerPreference>(NEUTRAL_MANAGER);
    const [error, setError] = useState<string | null>(null);
    const [isStarting, setIsStarting] = useState(false);

    useEffect(() => {
        let stale = false;
        fetchUserTeams(token)
            .then(teams => { if (!stale) setMyTeams(teams.filter(t => isPlayable(t) && t.team_id !== team.team_id)); })
            .catch(() => { if (!stale) setMyTeams([]); });
        return () => { stale = true; };
    }, [token, team.team_id]);

    useEffect(() => {
        if (tab !== 'public') return;
        let stale = false;
        const timer = setTimeout(() => {
            fetchPublicTeams(['user', 'official'], PUBLIC_RESULT_LIMIT, 0, query.trim() || undefined)
                .then(teams => { if (!stale) setPublicTeams(teams.filter(t => isPlayable(t) && t.user_id !== team.user_id)); })
                .catch(() => { if (!stale) setPublicTeams([]); });
        }, SEARCH_DEBOUNCE_MS);
        return () => { stale = true; clearTimeout(timer); };
    }, [tab, query, team.user_id]);

    const challenger = isOwnTeam ? team : picked;
    const opponent = isOwnTeam ? picked : team;
    const isOwnMatchup = !!challenger && !!opponent && challenger.user_id === opponent.user_id;

    const rotationSlots = useMemo(
        () => [...rotationOf(challenger), ...rotationOf(opponent)],
        [challenger, opponent],
    );
    const { cardMap } = useCardMap(rotationSlots, token);
    const starterOptions = (side: Team) => rotationOf(side).map(r => ({
        value: r.card_id,
        label: `${r.role} · ${cardMap[r.card_id]?.name ?? 'Loading…'}`,
    }));

    async function pickTeam(summary: TeamSummary) {
        setError(null);
        setStarters({});
        try {
            setPicked(await fetchTeam(summary.team_id, token));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load that team.');
        }
    }

    async function start() {
        if (!challenger || !opponent) return;
        setIsStarting(true);
        setError(null);
        try {
            await onBeforeStart();
            onStarted(await startFaceoff({
                team_id: challenger.team_id,
                opponent_team_id: opponent.team_id,
                starter_card_id: starters.challenger,
                manager: managerPayload(manager),
                ...(isOwnMatchup ? {
                    opponent_starter_card_id: starters.opponent,
                    opponent_manager: managerPayload(opponentManager),
                } : {}),
            }, token));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to start Faceoff.');
            setIsStarting(false);
        }
    }

    const showPublicTab = isOwnTeam && tab === 'public';
    const pickerTeams = showPublicTab ? publicTeams : myTeams;

    return (
        <Modal
            title="Faceoff"
            subtitle={isOwnTeam ? `Pick a team for ${team.name} to face.` : `Pick one of your teams to face ${team.name}.`}
            size="lg"
            onClose={onClose}
            footer={
                <div className="flex flex-col gap-2 p-3">
                    {error && <InlineError>{error}</InlineError>}
                    <button
                        type="button"
                        onClick={start}
                        disabled={!challenger || !opponent || isStarting}
                        className={buttonClass('primary', 'md', 'w-full')}
                    >
                        {isStarting && <FaSpinner className="animate-spin" />} Play Faceoff
                    </button>
                </div>
            }
        >
            <div className="flex flex-col gap-4 p-4 pb-32">
                {isOwnTeam && <Tabs tabs={PICKER_TABS} value={tab} onChange={setTab} fullWidth />}
                {showPublicTab && <TeamSearchInput value={query} onChange={setQuery} placeholder="Search public teams…" />}

                {pickerTeams === null ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 animate-pulse" aria-label="Loading teams">
                        {Array.from({ length: 4 }, (_, i) => <div key={i} className="h-16 rounded-control bg-(--background-tertiary)" />)}
                    </div>
                ) : pickerTeams.length === 0 ? (
                    <EmptyState size="inline">
                        {showPublicTab ? 'No public teams found.' : 'You need another finished team first.'}
                    </EmptyState>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-72 overflow-y-auto scrollbar-hide">
                        {pickerTeams.map(summary => (
                            <TeamCard
                                key={summary.team_id}
                                team={summary}
                                isSelected={summary.team_id === picked?.team_id}
                                onClick={() => pickTeam(summary)}
                            />
                        ))}
                    </div>
                )}

                {challenger && opponent && (
                    <>
                        <p className="text-[12px] text-(--text-secondary)">
                            {challenger.name} ({challenger.total_points.toLocaleString()} pts) at {opponent.name} ({opponent.total_points.toLocaleString()} pts)
                        </p>
                        {!hasSameSets(challenger, opponent) && (
                            <p className="text-[12px] text-(--text-secondary)">
                                These teams use different card sets, so the matchup may not be even.
                            </p>
                        )}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <FormDropdown
                                label={`${challenger.abbreviation} starter`}
                                options={starterOptions(challenger)}
                                selectedOption={starters.challenger ?? rotationOf(challenger)[0]?.card_id ?? ''}
                                onChange={value => setStarters(prev => ({ ...prev, challenger: value }))}
                            />
                            {isOwnMatchup && (
                                <FormDropdown
                                    label={`${opponent.abbreviation} starter`}
                                    options={starterOptions(opponent)}
                                    selectedOption={starters.opponent ?? rotationOf(opponent)[0]?.card_id ?? ''}
                                    onChange={value => setStarters(prev => ({ ...prev, opponent: value }))}
                                />
                            )}
                        </div>
                        <ManagerStyleFields title={`${challenger.abbreviation} manager`} description={MANAGER_DESCRIPTION} value={manager} onChange={setManager} />
                        {isOwnMatchup && (
                            <ManagerStyleFields title={`${opponent.abbreviation} manager`} description={MANAGER_DESCRIPTION} value={opponentManager} onChange={setOpponentManager} />
                        )}
                    </>
                )}
            </div>
        </Modal>
    );
}
