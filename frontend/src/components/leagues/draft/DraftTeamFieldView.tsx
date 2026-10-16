import { FieldView } from '../../team_builder/FieldView';
import type { CardDatabaseRecord } from '../../../api/card_db/cardDatabase';
import type { DraftPick, LeagueSettings, LeagueTeam } from '../../../api/leagues';
import { DraftTeamSummary } from './DraftTeamSummary';
import { fieldRosterData, teamRoster } from './draftView';

type Props = {
    team: LeagueTeam;
    picks: DraftPick[];
    settings: LeagueSettings;
    /** Drafted cards by release card id (`useCardMap`). */
    cards: Record<string, CardDatabaseRecord | null>;
    isLoadingCards: boolean;
    isOnTheClock?: boolean;
};

const noop = () => {};

/** One team's draft so far as a read-only tile: a summary header over the field, with the
 *  rotation, bullpen and bench in a column beside it. */
export function DraftTeamFieldView({ team, picks, settings, cards, isLoadingCards, isOnTheClock = false }: Props) {
    const roster = teamRoster(picks, team, settings);
    const { depthChart } = roster;

    return (
        <div className={`flex flex-col rounded-xl border overflow-hidden bg-(--background-secondary) ${isOnTheClock ? 'border-(--secondary) ring-2 ring-(--secondary)' : 'border-(--divider)'}`}>
            <div className="px-3 py-2 border-b border-(--divider) bg-(--background-tertiary)">
                <DraftTeamSummary
                    team={team}
                    points={roster.points}
                    picksMade={roster.picksMade}
                    settings={settings}
                    size="lg"
                    isOnTheClock={isOnTheClock}
                />
            </div>
            <FieldView
                lineup={depthChart.lineups[0]}
                cardMap={cards}
                rosterData={fieldRosterData(depthChart)}
                isLoadingCards={isLoadingCards}
                onSlotClick={noop}
                readOnly
                layout="side"
            />
        </div>
    );
}

/** Same shape as a team tile while the draft loads. */
export function DraftTeamFieldViewSkeleton() {
    return (
        <div className="flex flex-col rounded-xl border border-(--divider) overflow-hidden animate-pulse">
            <div className="h-16 bg-(--background-tertiary)" />
            <div className="flex">
                <div className="flex-1 aspect-square bg-(--background-secondary)" />
                <div className="w-[28%] bg-(--background-primary)" />
            </div>
        </div>
    );
}
