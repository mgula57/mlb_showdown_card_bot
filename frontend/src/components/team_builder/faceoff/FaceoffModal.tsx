import { useMemo, useState } from 'react';
import { FaSpinner } from 'react-icons/fa6';

import { startFaceoff, startLiveFaceoff } from '../../../api/faceoff';
import { LIVE_GAMES_ENABLED } from '../../../api/liveGame';
import { NEUTRAL_MANAGER, managerPayload, type ManagerPreference } from '../../../api/manager';
import { fetchTeam, type Team, type TeamSummary } from '../../../api/userTeams';
import { rotationOf } from './teamPicking';
import { TeamPicker } from '../TeamPicker';
import { useCardMap } from '../../../hooks/useCardMap';
import FormDropdown from '../../customs/FormDropdown';
import { InlineError } from '../../shared/InlineError';
import { Modal } from '../../shared/Modal';
import { buttonClass } from '../../shared/buttonStyles';
import ManagerStyleFields from '../../simulate/ManagerStyleFields';

const MANAGER_DESCRIPTION = 'Sets how this club manages for this Faceoff.';

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
    /** A Faceoff the user chose to play by hand opens as a live game. */
    onStartedLive: (liveGameId: string) => void;
};

/** Starts a Faceoff from a team's page. From your own team you choose who to face; from someone
 *  else's you choose which of your teams faces it. When you own both, you manage both sides. */
export function FaceoffModal({ team, isOwnTeam, token, onBeforeStart, onClose, onStarted, onStartedLive }: Props) {
    const [picked, setPicked] = useState<Team | null>(null);
    const [starters, setStarters] = useState<{ challenger?: string; opponent?: string }>({});
    const [manager, setManager] = useState<ManagerPreference>(NEUTRAL_MANAGER);
    const [opponentManager, setOpponentManager] = useState<ManagerPreference>(NEUTRAL_MANAGER);
    const [error, setError] = useState<string | null>(null);
    const [isStarting, setIsStarting] = useState(false);

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

    async function start(playLive: boolean) {
        if (!challenger || !opponent) return;
        setIsStarting(true);
        setError(null);
        try {
            await onBeforeStart();
            const payload = {
                team_id: challenger.team_id,
                opponent_team_id: opponent.team_id,
                starter_card_id: starters.challenger,
                manager: managerPayload(manager),
                ...(isOwnMatchup ? {
                    opponent_starter_card_id: starters.opponent,
                    opponent_manager: managerPayload(opponentManager),
                } : {}),
            };
            if (playLive) onStartedLive(await startLiveFaceoff(payload, token));
            else onStarted(await startFaceoff(payload, token));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to start Faceoff.');
            setIsStarting(false);
        }
    }


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
                        onClick={() => start(false)}
                        disabled={!challenger || !opponent || isStarting}
                        className={buttonClass('primary', 'md', 'w-full')}
                    >
                        {isStarting && <FaSpinner className="animate-spin" />} Play Faceoff
                    </button>
                    {/* The same Faceoff, played a turn at a time: your dice, your moves. */}
                    {LIVE_GAMES_ENABLED && (
                        <button
                            type="button"
                            onClick={() => start(true)}
                            disabled={!challenger || !opponent || isStarting}
                            className={buttonClass('secondary', 'md', 'w-full')}
                        >
                            Play it live
                        </button>
                    )}
                </div>
            }
        >
            <div className="flex flex-col gap-4 p-4 pb-32">
                <TeamPicker
                    token={token}
                    selectedTeamId={picked?.team_id}
                    onPick={pickTeam}
                    allowPublic={isOwnTeam}
                    excludeTeamId={team.team_id}
                    excludePublicUserId={team.user_id}
                    emptyMessage="You need another finished team first."
                />

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
