import { useState, useEffect, useRef, useMemo } from 'react';
import * as Tabs from '@radix-ui/react-tabs';

import type { Team, TeamUpdatePayload, LineupSlot, PitcherAssignment, TeamRosterSlot } from '../../api/userTeams';
import { fetchTeam } from '../../api/userTeams';
import type { ShowdownBotCardCompact } from '../../api/showdownBotCard';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import type { CardSource as CardSourceType } from '../../types/cardSource';
import { CardSource } from '../../types/cardSource';

import { FieldView } from './FieldView';
import { DepthChartPanel } from './DepthChartPanel';
import { TeamSettingsForm } from './TeamSettingsForm';
import { BottomSheet } from '../shared/BottomSheet';
import ShowdownCardSearch from '../cards/ShowdownCardSearch';
import { fetchCardData } from '../../api/card_db/cardDatabase';
import { FaSpinner, FaArrowLeft, FaPlus, FaXmark } from 'react-icons/fa6';
import { CardItemFromCardDatabaseRecord } from '../cards/CardItem';

type PendingSlot =
    | { kind: 'field'; position: string; current: LineupSlot | null }
    | { kind: 'rotation'; role: string; current: PitcherAssignment | null }
    | { kind: 'roster' };

type TeamDetailProps = {
    team: Team;
    onSave: (updates: TeamUpdatePayload) => Promise<void>;
    onBack: () => void;
    onReload?: () => void;
    token?: string;
    readOnly?: boolean;
};

const ROTATION_ROLES = ['SP1', 'SP2', 'SP3', 'SP4', 'SP5'] as const;
const BULLPEN_ROLES  = ['RP', 'CL'] as const;

const CARD_SOURCES = [
    { key: CardSource.BOT,  label: 'Bot' },
    { key: CardSource.WOTC, label: 'WOTC' },
    { key: CardSource.WBC,  label: 'WBC' },
] as const;

function getSearchFiltersForSlot(slot: PendingSlot | null): Record<string, string[]> {
    if (!slot) return {};
    if (slot.kind === 'field') {
        if (slot.position === 'SP') return { positions: ['STARTER'], player_type: ['PITCHER'] };
        const posMap: Record<string, string[]> = {
            C: ['C'], '1B': ['1B'], '2B': ['2B'], '3B': ['3B'],
            SS: ['SS'], LF: ['LF/RF'], RF: ['LF/RF'], CF: ['CF'], DH: ['DH'],
        };
        const positions = posMap[slot.position];
        return { ...(positions ? { positions } : {}), player_type: ['HITTER'] };
    }
    if (slot.kind === 'rotation') {
        if (slot.role.startsWith('SP')) return { positions: ['STARTER'], player_type: ['PITCHER'] };
        return { positions: ['RELIEVER', 'STARTER'], player_type: ['PITCHER'] };
    }
    return {};
}

function getEligiblePositions(card: CardDatabaseRecord): string[] {
    if (card.is_pitcher) {
        if ('STARTER' in card.positions_and_defense) return [...ROTATION_ROLES];
        return [...BULLPEN_ROLES];
    }
    const positions = Object.keys(card.positions_and_defense);
    const expanded = positions.flatMap(pos => {
        if (pos === 'LF/RF') return ['LF', 'RF'];
        if (pos === 'IF') return ['1B', '2B', '3B', 'SS'];
        if (pos === 'OF') return ['LF', 'CF', 'RF'];
        return [pos];
    });
    return [...new Set([...expanded, 'DH', 'BENCH'])];
}

export function TeamDetail({ team, onSave, onBack, onReload, token, readOnly = false }: TeamDetailProps) {
    const [draft, setDraft] = useState<Team>(team);
    const [cardMap, setCardMap] = useState<Record<string, ShowdownBotCardCompact | null>>({});
    const [pendingSlot, setPendingSlot] = useState<PendingSlot | null>(null);
    const [confirmCard, setConfirmCard] = useState<CardDatabaseRecord | null>(null);
    const [dirty, setDirty] = useState(false);
    const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
    const [stale, setStale] = useState(false);
    const [draftSource, setDraftSource] = useState<CardSourceType>(CardSource.BOT);
    const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => { setDraft(team); setDirty(false); setSaveStatus('idle'); }, [team]);

    // Stale check: on mount, compare local updated_at against server
    useEffect(() => {
        if (!team.team_id || !team.updated_at) return;
        fetchTeam(team.team_id, token).then(serverTeam => {
            if (serverTeam.updated_at && team.updated_at && serverTeam.updated_at > team.updated_at) {
                setStale(true);
            }
        }).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Auto-save: debounce 1.5s after any dirty change
    useEffect(() => {
        if (!dirty || readOnly) return;
        if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
        saveTimerRef.current = setTimeout(async () => {
            setSaveStatus('saving');
            try {
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
                const { team_id, user_id, created_at, updated_at, total_points, ...payload } = draft;
                await onSave(payload);
                setDirty(false);
                setSaveStatus('saved');
                setTimeout(() => setSaveStatus(s => s === 'saved' ? 'idle' : s), 2000);
            } catch {
                setSaveStatus('error');
            }
        }, 1500);
        return () => { if (saveTimerRef.current) clearTimeout(saveTimerRef.current); };
    }, [draft, dirty]);

    useEffect(() => {
        const ids = new Set<string>();
        draft.roster.forEach(s => ids.add(s.card_id));
        draft.lineups.forEach(ln => ln.slots.forEach(s => ids.add(s.card_id)));
        draft.rotation.forEach(r => ids.add(r.card_id));

        if (ids.size === 0) return;
        const missing = [...ids].filter(id => !(id in cardMap));
        if (missing.length === 0) return;

        (async () => {
            try {
                const cards = await fetchCardData(CardSource.BOT as any, { id: missing, limit: missing.length });
                const newEntries = Object.fromEntries(
                    cards.map(c => [c.id, {
                        id: c.id,
                        name: c.name,
                        year: String(c.year),
                        set: c.showdown_set,
                        team: c.team_id,
                        points: c.points,
                        command: c.command,
                        is_pitcher: c.is_pitcher,
                        color_primary: c.color_primary ?? null,
                        color_secondary: c.color_secondary ?? null,
                        positions_and_defense_string: c.positions_and_defense_string ?? null,
                        ip: c.ip ?? null,
                    } as ShowdownBotCardCompact])
                );
                setCardMap(prev => ({ ...prev, ...newEntries }));
            } catch { /* silent */ }
        })();
    }, [draft]);

    const searchFilters = useMemo(() => getSearchFiltersForSlot(pendingSlot), [pendingSlot]);

    function update(updates: TeamUpdatePayload) {
        setDraft(prev => ({ ...prev, ...updates } as Team));
        setDirty(true);
    }


    function handleCardPicked(card: CardDatabaseRecord) {
        setConfirmCard(card);
    }

    function handleConfirmPosition(position: string) {
        if (!confirmCard) return;

        const compact: ShowdownBotCardCompact = {
            id: confirmCard.id,
            name: confirmCard.name,
            year: String(confirmCard.year),
            set: confirmCard.showdown_set,
            team: confirmCard.team_id,
            points: confirmCard.points,
            command: confirmCard.command,
            is_pitcher: confirmCard.is_pitcher,
            color_primary: confirmCard.color_primary ?? null,
            color_secondary: confirmCard.color_secondary ?? null,
            positions_and_defense_string: confirmCard.positions_and_defense_string ?? null,
            ip: confirmCard.ip ?? null,
        };
        setCardMap(prev => ({ ...prev, [confirmCard.id]: compact }));

        const pitcherSlots = [...ROTATION_ROLES, ...BULLPEN_ROLES] as string[];
        if (pitcherSlots.includes(position)) {
            const rotation = draft.rotation.filter(r => r.role !== position);
            rotation.push({ card_id: confirmCard.id, card_source: draftSource, role: position });
            update({ rotation });
        } else if (position === 'BENCH') {
            const slot: TeamRosterSlot = {
                card_id: confirmCard.id,
                card_source: draftSource,
                roster_position: 'BENCH',
                draft_order: null,
            };
            update({ roster: [...draft.roster, slot] });
        } else {
            const lineups = draft.lineups.length > 0 ? [...draft.lineups] : [{ name: 'Default', slots: [] }];
            const slots = lineups[0].slots.filter(s => s.field_position !== position);
            slots.push({ card_id: confirmCard.id, card_source: draftSource, field_position: position, batting_order: null });
            lineups[0] = { ...lineups[0], slots };
            update({ lineups });
        }

        setConfirmCard(null);
        setPendingSlot(null);
    }

    const defaultLineup = draft.lineups[0] ?? { name: 'Default', slots: [] };
    const primary = draft.primary_color || 'rgb(0,0,0)';

    const activeFieldPosition = pendingSlot?.kind === 'field' ? pendingSlot.position : null;
    const activeRole = pendingSlot?.kind === 'rotation' ? pendingSlot.role : null;

    const pendingLabel = pendingSlot
        ? pendingSlot.kind === 'field'    ? `Filter: ${pendingSlot.position}`
        : pendingSlot.kind === 'rotation' ? `Filter: ${pendingSlot.role}`
        : 'Adding to roster'
        : null;

    const tabTriggerClass =
        'relative flex items-center px-4 py-2 text-sm rounded-lg transition-colors ' +
        'data-[state=active]:bg-(--background-quaternary) data-[state=active]:font-bold data-[state=active]:text-(--showdown-blue) ' +
        'data-[state=inactive]:text-(--text-tertiary) data-[state=inactive]:font-medium data-[state=inactive]:hover:bg-(--divider)';

    const draftPanel = (
        <div className="flex flex-col h-full min-h-0">
            <div className="flex items-center gap-1 px-3 pt-2 pb-1 shrink-0 border-b border-(--divider)">
                {CARD_SOURCES.map(s => (
                    <button
                        key={s.key}
                        type="button"
                        onClick={() => setDraftSource(s.key)}
                        className={`text-[11px] font-semibold px-2.5 py-1 rounded border transition-colors
                            ${draftSource === s.key
                                ? 'border-(--secondary) text-(--secondary)'
                                : 'border-(--divider) text-(--text-secondary) hover:border-(--secondary)/50'
                            }`}
                    >
                        {s.label}
                    </button>
                ))}
                {pendingLabel && (
                    <span className="ml-auto text-[11px] text-(--secondary) font-semibold truncate pl-2">
                        {pendingLabel}
                    </span>
                )}
            </div>

            {CARD_SOURCES.map(s => (
                <div key={s.key} className={`flex-1 min-h-0 ${draftSource === s.key ? 'flex flex-col' : 'hidden'}`}>
                    <ShowdownCardSearch
                        source={s.key}
                        compact={true}
                        disableLocalStorage={true}
                        verticalOffset="36"
                        defaultFilters={searchFilters}
                        actionButton={{
                            icon: <FaPlus />,
                            label: 'Select',
                            bgColorClass: 'bg-(--showdown-red) opacity-95 border p-2 md:p-1 text-white shadow-sm rounded-full',
                            onClick: handleCardPicked,
                        }}
                    />
                </div>
            ))}
        </div>
    );

    // Eligible positions split into groups for the confirmation modal
    const confirmPositions = confirmCard ? getEligiblePositions(confirmCard) : [];
    const confirmFieldPositions   = confirmPositions.filter(p => !([...ROTATION_ROLES, ...BULLPEN_ROLES] as string[]).includes(p));
    const confirmRotationPositions = confirmPositions.filter(p => (ROTATION_ROLES as readonly string[]).includes(p));
    const confirmBullpenPositions  = confirmPositions.filter(p => (BULLPEN_ROLES as readonly string[]).includes(p));

    return (
        <div className="flex flex-col min-h-0 flex-1">
            <div
                className="flex items-center gap-3 px-4 py-3 border-b border-(--divider) shrink-0"
                style={{ borderLeftWidth: 4, borderLeftColor: primary }}
            >
                <button type="button" onClick={onBack} className="text-(--text-tertiary) hover:text-(--text-primary) transition-colors">
                    <FaArrowLeft />
                </button>
                <div className="flex-1 min-w-0">
                    <div className="text-[15px] font-black text-(--text-primary) truncate">{draft.name || 'Untitled Team'}</div>
                    <div className="text-[11px] text-(--text-secondary)">{draft.abbreviation} · {draft.showdown_set}</div>
                </div>
                {!readOnly && (
                    <div className="flex items-center gap-1 text-[11px] font-semibold min-w-13 justify-end">
                        {saveStatus === 'saving' && (
                            <span className="flex items-center gap-1 text-(--text-tertiary)">
                                <FaSpinner className="animate-spin text-[10px]" /> Saving
                            </span>
                        )}
                        {saveStatus === 'saved' && <span className="text-green-500">Saved</span>}
                        {saveStatus === 'error' && <span className="text-red-500">Error</span>}
                        {saveStatus === 'idle' && dirty && <span className="text-(--text-tertiary) opacity-60">Unsaved</span>}
                    </div>
                )}
            </div>

            {stale && (
                <div className="flex items-center gap-2 px-4 py-2 border-b border-amber-500/30 bg-amber-500/10 text-[12px] shrink-0">
                    <span className="flex-1 text-amber-700 dark:text-amber-400">This team was updated on another device.</span>
                    {onReload && (
                        <button type="button" onClick={onReload} className="font-bold text-amber-700 dark:text-amber-400 underline underline-offset-2">
                            Reload
                        </button>
                    )}
                </div>
            )}

            <div className="flex flex-1 min-h-0 overflow-hidden">
                <Tabs.Root 
                    defaultValue="field" 
                    className="
                        flex flex-col shrink-0 
                        min-h-0 min-w-0 overflow-hidden 
                        w-full sm:w-80 md:w-108 lg:w-124 xl:w-136
                    "
                >
                    <Tabs.List className="flex px-3 border-b border-(--divider) gap-x-1 shrink-0 py-1">
                        <Tabs.Trigger value="field"    className={tabTriggerClass}>Field View</Tabs.Trigger>
                        <Tabs.Trigger value="depth"    className={tabTriggerClass}>Depth Chart</Tabs.Trigger>
                        <Tabs.Trigger value="settings" className={tabTriggerClass}>Settings</Tabs.Trigger>
                    </Tabs.List>

                    <Tabs.Content value="field" className="flex-1 overflow-auto focus:outline-none ">
                        <FieldView
                            lineup={defaultLineup}
                            cardMap={cardMap}
                            onSlotClick={(pos, slot) => {
                                if (readOnly) return;
                                setPendingSlot({ kind: 'field', position: pos, current: slot });
                            }}
                            readOnly={readOnly}
                            activePosition={activeFieldPosition}
                        />
                    </Tabs.Content>

                    <Tabs.Content value="depth" className="flex-1 min-h-0 overflow-y-auto focus:outline-none">
                        <DepthChartPanel
                            team={draft}
                            cardMap={cardMap}
                            onSlotClick={(pos, slot) => {
                                if (readOnly) return;
                                setPendingSlot({ kind: 'field', position: pos, current: slot });
                            }}
                            onRoleClick={(role, current) => {
                                if (readOnly) return;
                                setPendingSlot({ kind: 'rotation', role, current });
                            }}
                            readOnly={readOnly}
                            activePosition={activeFieldPosition}
                            activeRole={activeRole}
                        />
                    </Tabs.Content>

                    <Tabs.Content value="settings" className="flex-1 overflow-auto focus:outline-none">
                        <TeamSettingsForm team={draft} onChange={updates => update(updates)} />
                    </Tabs.Content>
                </Tabs.Root>

                {!readOnly && (
                    <div className="hidden md:flex flex-col flex-1 min-w-0 min-h-0 border-l border-(--divider)">
                        {draftPanel}
                    </div>
                )}
            </div>

            {!readOnly && (
                <BottomSheet
                    isOpen={true}
                    onClose={() => setPendingSlot(null)}
                    title={pendingLabel ?? undefined}
                    dismissible={false}
                >
                    {draftPanel}
                </BottomSheet>
            )}

            {/* Confirmation modal: choose which position to assign the picked card */}
            {confirmCard && (
                <div
                    className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm p-4"
                    onClick={() => setConfirmCard(null)}
                >
                    <div
                        className="bg-(--background-primary) rounded-2xl w-full max-w-sm shadow-2xl border border-(--divider) overflow-hidden"
                        onClick={e => e.stopPropagation()}
                    >
                        {/* Header */}
                        <div className="flex items-start justify-between px-4 pt-4 pb-3 border-b border-(--divider)">
                            <div>
                                <div className="text-[13px] font-bold text-(--text-primary)">Choose a position</div>
                                <div className="text-[11px] text-(--text-secondary) mt-0.5">Where should this card be placed?</div>
                            </div>
                            <button
                                type="button"
                                onClick={() => setConfirmCard(null)}
                                className="text-(--text-tertiary) hover:text-(--text-primary) transition-colors mt-0.5"
                            >
                                <FaXmark className="text-[13px]" />
                            </button>
                        </div>

                        {/* Card preview */}
                        <div className="px-4 py-3 border-b border-(--divider)">
                            <CardItemFromCardDatabaseRecord card={confirmCard} />
                        </div>

                        {/* Position buttons */}
                        <div className="px-4 py-3 flex flex-col gap-2">
                            {confirmFieldPositions.length > 0 && (
                                <div className="flex flex-wrap gap-1.5">
                                    {confirmFieldPositions.map(pos => (
                                        <PositionButton key={pos} label={pos} onClick={() => handleConfirmPosition(pos)} />
                                    ))}
                                </div>
                            )}
                            {confirmRotationPositions.length > 0 && (
                                <>
                                    <div className="text-[10px] font-semibold text-(--text-tertiary) uppercase tracking-wide">Rotation</div>
                                    <div className="flex flex-wrap gap-1.5">
                                        {confirmRotationPositions.map(pos => (
                                            <PositionButton key={pos} label={pos} onClick={() => handleConfirmPosition(pos)} />
                                        ))}
                                    </div>
                                </>
                            )}
                            {confirmBullpenPositions.length > 0 && (
                                <>
                                    <div className="text-[10px] font-semibold text-(--text-tertiary) uppercase tracking-wide">Bullpen</div>
                                    <div className="flex flex-wrap gap-1.5">
                                        {confirmBullpenPositions.map(pos => (
                                            <PositionButton key={pos} label={pos} onClick={() => handleConfirmPosition(pos)} />
                                        ))}
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function PositionButton({ label, onClick }: { label: string; onClick: () => void }) {
    return (
        <button
            type="button"
            onClick={onClick}
            className="px-3 py-1.5 rounded-lg text-[12px] font-bold
                bg-(--background-secondary) border border-(--divider)
                text-(--text-primary) hover:border-(--secondary) hover:text-(--secondary)
                transition-colors"
        >
            {label}
        </button>
    );
}
