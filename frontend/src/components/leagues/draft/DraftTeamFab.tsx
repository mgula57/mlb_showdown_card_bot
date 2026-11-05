import { FaUsers } from 'react-icons/fa6';
import type { DraftState, LeagueSettings } from '../../../api/leagues';
import { FloatingActionButton } from '../../shared/FloatingActionButton';
import { ProgressRing } from '../../team_builder/ProgressRing';
import { teamRoster } from './draftView';
import { CAPS_LABEL_CLASS } from '../../shared/fieldStyles';

type Props = {
    draft: DraftState;
    settings: LeagueSettings;
    myMemberId: string | null;
    isMyTurn: boolean;
    onClick: () => void;
};

const BUTTON_CLASS = `
    pointer-events-auto w-12 h-12 rounded-full flex flex-col items-center justify-center
    bg-(--background-secondary) text-(--text-primary) shadow-overlay
    cursor-pointer hover:opacity-90 transition-opacity
`;

/** Phone-only button that opens the teams sheet. Sits bottom-left, clear of the Draft / Queue
 *  buttons down the right edge of the pool's cards. For a drafter it wears a ring of picks made out
 *  of the roster size, with what's left under the cap (and whether they're up) beside it;
 *  spectators get a plain teams button. */
export function DraftTeamFab({ draft, settings, myMemberId, isMyTurn, onClick }: Props) {
    const myTeam = myMemberId ? draft.teams.find(team => team.member_id === myMemberId) : undefined;

    if (!myTeam) {
        return (
            <FloatingActionButton side="left">
                <button type="button" onClick={onClick} aria-label="Show teams" className={BUTTON_CLASS}>
                    <FaUsers className="text-[16px]" />
                </button>
            </FloatingActionButton>
        );
    }

    const roster = teamRoster(draft.picks, myTeam, settings);
    const cap = settings.pts_cap;
    const left = cap ? cap - roster.points : null;
    const isOverCap = left !== null && left < 0;

    return (
        <>
            {/* Quick info, centered on the button just right of its ring */}
            <div className="lg:hidden fixed z-50 left-21 bottom-9 h-6 px-2 rounded-control flex items-center gap-1 pointer-events-none border border-(--divider) bg-(--background-secondary) shadow-overlay text-[11px] font-bold tabular-nums whitespace-nowrap">
                {isMyTurn && <span className={`${CAPS_LABEL_CLASS} text-(--showdown-red)`}>Your pick ·</span>}
                {left !== null ? (
                    <span className={isOverCap ? 'text-(--red)' : 'text-(--green)'}>{left} <span className="text-(--text-tertiary)">left</span></span>
                ) : (
                    <span className="text-(--text-primary)">{roster.points} <span className="text-(--text-tertiary)">pts</span></span>
                )}
            </div>
            <FloatingActionButton side="left">
                <span className={isMyTurn ? 'text-(--showdown-red)' : 'text-(--green)'}>
                    <ProgressRing
                        filled={roster.picksMade}
                        target={settings.roster_size}
                        size={60}
                        stroke={3}
                        label={
                            <button
                                type="button"
                                onClick={onClick}
                                aria-label={`Show teams - ${roster.picksMade} of ${settings.roster_size} picks made`}
                                className={BUTTON_CLASS}
                            >
                                <FaUsers className="text-[11px] text-(--text-secondary)" />
                                <span className="font-display-upright text-[15px] leading-none tabular-nums">{roster.picksMade}</span>
                            </button>
                        }
                    />
                </span>
            </FloatingActionButton>
        </>
    );
}
