import { useState } from 'react';
import { FaClipboardList, FaRing } from 'react-icons/fa6';
import CustomSelect from '../../shared/CustomSelect';
import { Tabs } from '../../shared/Tabs';
import { DepthChartPanel } from '../../team_builder/DepthChartPanel';
import { FieldView } from '../../team_builder/FieldView';
import { type PendingSlot, pendingSlotHighlight } from '../../team_builder/draftSlot';
import type { CardDatabaseRecord } from '../../../api/card_db/cardDatabase';
import type { DraftState, LeagueSettings } from '../../../api/leagues';
import { fieldRosterData, teamRoster } from './draftView';

type Props = {
    draft: DraftState;
    settings: LeagueSettings;
    myMemberId: string | null;
    /** Drafted cards by release card id (`useCardMap`). */
    cards: Record<string, CardDatabaseRecord | null>;
    isLoadingCards: boolean;
    /** The slot being filled, highlighted on my roster. */
    pendingSlot: PendingSlot | null;
    /** Clicking an empty slot on my own roster starts filling it. Omit to keep the roster display only. */
    onFillSlot?: (slot: PendingSlot) => void;
};

type RosterView = 'field' | 'depth';

/** A team's roster as drafted so far, as the team builder's field view or depth chart, with what
 *  it still needs. Defaults to the viewer's team; any team can be picked to scout. */
export function DraftTeamPanel({ draft, settings, myMemberId, cards, isLoadingCards, pendingSlot, onFillSlot }: Props) {
    const [memberId, setMemberId] = useState<string>(myMemberId ?? draft.teams[0]?.member_id ?? '');
    const [rosterView, setRosterView] = useState<RosterView>('field');
    const team = draft.teams.find(t => t.member_id === memberId) ?? draft.teams[0];
    if (!team) return null;
    const roster = teamRoster(draft.picks, team, settings);
    const { depthChart } = roster;
    const lineup = depthChart.lineups[0];

    // My own roster's empty slots can be clicked to search for a fit, like the team builder.
    // Picks are final, so a filled slot is never offered for replacing.
    const fill = team.member_id === myMemberId ? onFillSlot : undefined;
    const canFill = !!fill;
    const highlight = canFill ? pendingSlotHighlight(pendingSlot) : { activePosition: null, activeRole: null };
    const slotHandlers = {
        onSlotClick: (position: string, current: unknown) => { if (fill && !current) fill({ kind: 'field', position, current: null }); },
        onRoleClick: (role: string, current: unknown) => { if (fill && !current) fill({ kind: 'rotation', role, current: null }); },
        onBullpenClick: (current: unknown) => { if (fill && !current) fill({ kind: 'bullpen', current: null }); },
        onBenchClick: (current: unknown) => { if (fill && !current) fill({ kind: 'bench', current: null }); },
    };

    const fieldRoster = fieldRosterData(depthChart);

    return (
        <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between gap-2">
                <CustomSelect
                    value={team.member_id}
                    onChange={setMemberId}
                    options={draft.teams.map(t => ({ value: t.member_id, label: t.member_id === myMemberId ? `${t.name} (you)` : t.name }))}
                    buttonClassName="text-[12px] py-1 px-2 rounded-md bg-(--background-tertiary) text-(--text-primary) cursor-pointer"
                />
                {roster.required > 0 ? (
                    <span className="shrink-0 rounded-full bg-(--secondary)/15 text-(--secondary) px-2 py-0.5 text-[10px] font-black uppercase tracking-wide">
                        {roster.required} more needed
                    </span>
                ) : (
                    <span className="shrink-0 text-[10px] font-bold text-(--success) uppercase tracking-wide">Required spots filled</span>
                )}
            </div>
            <div className="flex items-center justify-between gap-2">
                <span className="text-[11px] text-(--text-tertiary)">
                    {roster.picksMade}/{settings.roster_size} picks · {roster.points} pts{settings.pts_cap ? ` of ${settings.pts_cap}` : ''}
                </span>
                <Tabs<RosterView>
                    tabs={[
                        { id: 'field', label: 'Field', icon: <FaRing /> },
                        { id: 'depth', label: 'Depth Chart', icon: <FaClipboardList /> },
                    ]}
                    value={rosterView}
                    onChange={setRosterView}
                    size="sm"
                />
            </div>

            {/* Empty rows stay visible so the open spots read at a glance; they're clickable only on my own roster. */}
            {rosterView === 'field' ? (
                <FieldView
                    key={team.member_id}
                    lineup={lineup}
                    cardMap={cards}
                    rosterData={fieldRoster}
                    isLoadingCards={isLoadingCards}
                    readOnly={!canFill}
                    emptySlotsOnly
                    {...highlight}
                    {...slotHandlers}
                />
            ) : (
                <div className="-mx-4">
                    <DepthChartPanel
                        key={team.member_id}
                        team={depthChart}
                        cardMap={cards}
                        isLoadingCards={isLoadingCards}
                        slotPickingDisabled={!canFill}
                        emptySlotsOnly
                        {...highlight}
                        {...slotHandlers}
                    />
                </div>
            )}
        </div>
    );
}
