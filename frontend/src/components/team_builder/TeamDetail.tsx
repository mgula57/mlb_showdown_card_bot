import { useState, useEffect, useRef, useMemo, useCallback, memo } from 'react';
import * as Tabs from '@radix-ui/react-tabs';

import type { Team, TeamUpdatePayload, LineupSlot, PitcherAssignment, TeamRosterSlot, AutofillStrategy } from '../../api/userTeams';
import { fetchTeam, autofillTeam, isTeamDrafting } from '../../api/userTeams';
import { AutofillPanel } from './AutofillPanel';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import type { CardSource as CardSourceType } from '../../types/cardSource';
import { CardSource } from '../../types/cardSource';
import { useCardMap } from '../../hooks/useCardMap';
import { getContrastColor } from "../shared/Color";
import { FieldView } from './FieldView';
import type { FieldViewRosterData } from './FieldView';
import { DepthChartPanel } from './DepthChartPanel';
import { TeamSettingsForm } from './TeamSettingsForm';
import { BottomSheet } from '../shared/BottomSheet';
import ShowdownCardSearch from '../cards/ShowdownCardSearch';
import {
    FaSpinner, FaArrowLeft, FaPlus, FaXmark, FaCircleCheck, FaWandMagicSparkles,
    FaShuffle, FaPenToSquare, FaStar, FaRegStar
} from 'react-icons/fa6';
import { CardItemFromCardDatabaseRecord } from '../cards/CardItem';
import { CardItemCompactFromCardDatabaseRecord } from '../cards/CardItemCompact';
import { imageForSet } from '../shared/SiteSettingsContext';
import { ToastMessage } from '../shared/ToastMessage';

type PendingSlot =
    | { kind: 'field'; position: string; current: LineupSlot | null }
    | { kind: 'rotation'; role: string; current: PitcherAssignment | null }
    | { kind: 'bench'; role: string; current: TeamRosterSlot | null }
    | { kind: 'roster' };

type TeamDetailProps = {
    team: Team;
    onSave: (updates: TeamUpdatePayload) => Promise<void>;
    onBack?: () => void;
    onReload?: () => void;
    token?: string;
    readOnly?: boolean;
    /** When true, don't cap the root to the viewport height — let the page scroll instead of an inner region. Used when embedding a read-only team view inside another screen. */
    embedded?: boolean;
    isStarred?: boolean;
    onToggleStar?: () => void;
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
    if (slot.kind === 'bench') {
        return { player_type: ['HITTER'] };
    }
    return {};
}

function getSettingsChanges(original: Team, pending: TeamUpdatePayload): string[] {
    const lines: string[] = [];
    if ('pts_limit' in pending && pending.pts_limit !== original.pts_limit)
        lines.push(`PTS limit: ${original.pts_limit ?? 'none'} → ${pending.pts_limit ?? 'none'}`);
    if ('roster_size' in pending && pending.roster_size !== original.roster_size)
        lines.push(`Roster size: ${original.roster_size} → ${pending.roster_size}`);
    if ('num_starters' in pending && pending.num_starters !== original.num_starters)
        lines.push(`Starting pitchers: ${original.num_starters} → ${pending.num_starters}`);
    if ('min_bullpen' in pending && pending.min_bullpen !== original.min_bullpen)
        lines.push(`Min bullpen: ${original.min_bullpen} → ${pending.min_bullpen}`);
    if ('min_bench' in pending && pending.min_bench !== original.min_bench)
        lines.push(`Min bench: ${original.min_bench} → ${pending.min_bench}`);
    if ('bench_pts_multiplier' in pending && pending.bench_pts_multiplier !== original.bench_pts_multiplier)
        lines.push(`Bench PTS multiplier: ${original.bench_pts_multiplier}× → ${pending.bench_pts_multiplier}×`);
    if ('allowed_sets' in pending) {
        const orig = (original.allowed_sets ?? []).sort().join(', ') || 'all';
        const next = (pending.allowed_sets ?? []).sort().join(', ') || 'all';
        if (orig !== next) lines.push(`Allowed sets: ${orig} → ${next}`);
    }
    if ('allowed_card_sources' in pending) {
        const orig = (original.allowed_card_sources ?? []).sort().join(', ') || 'all';
        const next = (pending.allowed_card_sources ?? []).sort().join(', ') || 'all';
        if (orig !== next) lines.push(`Card sources: ${orig} → ${next}`);
    }
    if ('player_filters' in pending)
        lines.push('Player filters updated');
    return lines;
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
    return [...new Set([...expanded, 'DH', 'BE'])];
}

export function TeamDetail({ team, onSave, onBack, onReload, token, readOnly = false, embedded = false, isStarred = false, onToggleStar }: TeamDetailProps) {
    const [draft, setDraft] = useState<Team>(team);

    const rosterSlots = useMemo(
        () => draft.roster.map(s => ({ card_id: s.card_id, card_source: s.card_source })),
        [draft.roster],
    );
    const { cardMap, addCard } = useCardMap(rosterSlots);
    const [pendingSlot, setPendingSlot] = useState<PendingSlot | null>(null);
    const [confirmCard, setConfirmCard] = useState<CardDatabaseRecord | null>(null);
    const [dirty, setDirty] = useState(false);
    const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
    const [stale, setStale] = useState(false);
    const [draftSource, setDraftSource] = useState<CardSourceType>(CardSource.BOT);
    const [draftToast, setDraftToast] = useState<{ name: string; position: string } | null>(null);
    const [draftToastExiting, setDraftToastExiting] = useState(false);
    const [showAutofill, setShowAutofill] = useState(false);
    const [lastAutofillStrategy, setLastAutofillStrategy] = useState<AutofillStrategy | null>(null);
    const [reshuffling, setReshuffling] = useState(false);
    const [editMode, setEditMode] = useState(false);
    const [pendingSettings, setPendingSettings] = useState<TeamUpdatePayload | null>(null);
    const [hoveredCardId, setHoveredCardId] = useState<string | null>(null);
    const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const [isLg, setIsLg] = useState(() => window.matchMedia('(min-width: 1024px)').matches);

    useEffect(() => {
        const mq = window.matchMedia('(min-width: 1024px)');
        const handler = (e: MediaQueryListEvent) => setIsLg(e.matches);
        mq.addEventListener('change', handler);
        return () => mq.removeEventListener('change', handler);
    }, []);

    // Reset draft source if the current one becomes disallowed
    useEffect(() => {
        const allowed = draft.allowed_card_sources ?? [];
        if (allowed.length > 0 && !allowed.includes(draftSource)) {
            setDraftSource(allowed[0] as CardSourceType);
        }
    }, [draft.allowed_card_sources]);

    useEffect(() => { setDraft(team); setDirty(false); setSaveStatus('idle'); setEditMode(false); setPendingSettings(null); }, [team]);

    useEffect(() => {
        if (!draftToast) return;
        if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
        toastTimerRef.current = setTimeout(() => {
            setDraftToastExiting(true);
            toastTimerRef.current = setTimeout(() => {
                setDraftToast(null);
                setDraftToastExiting(false);
            }, 300);
        }, 2500);
        return () => { if (toastTimerRef.current) clearTimeout(toastTimerRef.current); };
    }, [draftToast]);

    // Stale check: on mount, compare local updated_at against server
    useEffect(() => {
        if (!team.team_id || !team.updated_at) return;
        fetchTeam(team.team_id, token).then(serverTeam => {
            if (serverTeam.updated_at && team.updated_at && serverTeam.updated_at > team.updated_at) {
                setStale(true);
            }
            console.log('Team Loaded:', serverTeam);
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


    const searchFilters = useMemo(() => ({
        ...(draft.player_filters ?? {}),
        ...getSearchFiltersForSlot(pendingSlot),
        ...(draft.allowed_sets?.length ? { showdown_set: draft.allowed_sets } : {}),
    }), [pendingSlot, draft.allowed_sets, draft.player_filters]);

    function update(updates: TeamUpdatePayload) {
        setDraft(prev => ({ ...prev, ...updates } as Team));
        setDirty(true);
    }

    async function handleAutofill(strategy: AutofillStrategy) {
        if (!token || !draft.team_id) return;
        const activeFilters: Record<string, unknown> = {};
        if (draft.allowed_sets?.length) activeFilters['showdown_set'] = draft.allowed_sets;
        // Pass single allowed source so autofill fetches from the correct table
        if (draft.allowed_card_sources?.length === 1) activeFilters['source'] = draft.allowed_card_sources[0];
        const result = await autofillTeam(draft.team_id, strategy, token, activeFilters);
        update({ roster: result.roster, lineups: result.lineups, rotation: result.rotation });
        const added = result.roster.length - draft.roster.length;
        setLastAutofillStrategy(strategy);
        setDraftToast({ name: 'Roster Autofilled', position: `${added} player${added !== 1 ? 's' : ''} added` });
    }

    async function handleReshuffle() {
        if (!lastAutofillStrategy || reshuffling) return;
        setReshuffling(true);
        try {
            await handleAutofill(lastAutofillStrategy);
        } finally {
            setReshuffling(false);
        }
    }

    const handleCardPicked = useCallback((card: CardDatabaseRecord) => {
        if (pendingSlot?.kind === 'bench') {
            handleConfirmPosition(pendingSlot.role, card);
            return;
        }
        setConfirmCard(card);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [pendingSlot]);

    function handleConfirmPosition(position: string, card: CardDatabaseRecord = confirmCard!) {
        if (!card) return;

        addCard(card);

        const nextDraftOrder = Math.max(0, ...draft.roster.map(s => s.draft_order ?? 0)) + 1;
        const rosterSlot: TeamRosterSlot = {
            card_id: card.card_id,
            card_source: draftSource,
            roster_position: position,
            draft_order: nextDraftOrder,
            pick_source: 'MANUAL',
        };

        const pitcherSlots = [...ROTATION_ROLES, ...BULLPEN_ROLES] as string[];
        if (pitcherSlots.includes(position)) {
            const rotation = draft.rotation.filter(r => r.role !== position);
            rotation.push({ card_id: card.card_id, card_source: draftSource, role: position });
            const roster = [...draft.roster.filter(s => s.roster_position !== position), rosterSlot];
            update({ rotation, roster });
        } else if (/^BE\d+$/.test(position)) {
            const roster = [...draft.roster.filter(s => s.roster_position !== position), rosterSlot];
            update({ roster });
        } else if (position === 'BE') {
            update({ roster: [...draft.roster, rosterSlot] });
        } else {
            const lineups = draft.lineups.length > 0 ? [...draft.lineups] : [{ name: 'Default', slots: [] }];
            const slots = lineups[0].slots.filter(s => s.field_position !== position);
            slots.push({ card_id: card.card_id, card_source: draftSource, field_position: position, batting_order: null });
            lineups[0] = { ...lineups[0], slots };
            const roster = [...draft.roster.filter(s => s.roster_position !== position), rosterSlot];
            update({ lineups, roster });
        }

        setDraftToast({ name: card.name, position });
        setConfirmCard(null);
        setPendingSlot(null);
    }

    const isDrafting = isTeamDrafting(draft);
    const teamMode: 'drafting' | 'editing' | 'complete' = readOnly ? 'complete' : isDrafting ? 'drafting' : editMode ? 'editing' : 'complete';
    const showEditControls = !readOnly && teamMode !== 'complete';
    // Real MLB/WBC rosters are synthesized read-only from the card archive — there's no draft history or editable settings to show
    const isMlbTeam = team.source === 'mlb';

    const settingsDraft = useMemo(
        () => pendingSettings ? { ...draft, ...pendingSettings } as Team : draft,
        [draft, pendingSettings],
    );

    const defaultLineup = draft.lineups[0] ?? { name: 'Default', slots: [] };
    const primary = draft.primary_color || 'rgb(0,0,0)';
    const secondary = draft.secondary_color || 'rgb(100,100,100)';

    // Banner color tokens derived from team colors (shared by drafting + editing banners)
    const bannerContrastColor = getContrastColor(primary);
    const bannerIsLight = bannerContrastColor === '#000' || bannerContrastColor === 'black';
    const bannerFillColor  = bannerIsLight ? 'rgba(0,0,0,0.80)'  : 'rgba(255,255,255,0.92)';
    const bannerTrackColor = bannerIsLight ? 'rgba(0,0,0,0.15)'  : 'rgba(255,255,255,0.25)';
    const bannerDotColor   = bannerIsLight ? 'rgba(0,0,0,0.45)'  : 'rgba(255,255,255,0.55)';
    const bannerStyle      = { background: `linear-gradient(to right, ${primary}, ${secondary})` };
    const bannerBtnClass   = bannerIsLight
        ? 'bg-black/10 hover:bg-black/20 border border-black/20 text-black/80'
        : 'bg-white/15 hover:bg-white/25 border border-white/30 text-white';

    const rosterProgress = useMemo(() => {
        const filledLineup = (draft.lineups[0]?.slots ?? []).length;
        const filledStarters = draft.rotation.filter(r => (ROTATION_ROLES as readonly string[]).includes(r.role)).length;
        const filledBench = draft.roster.filter(s => s.roster_position === 'BE').length;
        const filledBullpen = draft.rotation.filter(r => !(ROTATION_ROLES as readonly string[]).includes(r.role)).length;
        const filled = filledLineup + Math.min(filledStarters, draft.num_starters) + Math.min(filledBench, draft.min_bench) + Math.min(filledBullpen, draft.min_bullpen);
        const total = 9 + draft.num_starters + draft.min_bench + draft.min_bullpen;
        return { filled, total };
    }, [draft]);

    const activeFieldPosition = pendingSlot?.kind === 'field' ? pendingSlot.position : null;
    const activeRole = (pendingSlot?.kind === 'rotation' || pendingSlot?.kind === 'bench') ? pendingSlot.role : null;

    const pointsBreakdown = useMemo(() => {
        const pts = (id: string) => cardMap[id]?.points ?? 0;
        const lineup = defaultLineup.slots.reduce((sum, s) => sum + pts(s.card_id), 0);
        const bench  = draft.roster
            .filter(s => s.roster_position === 'BE')
            .reduce((sum, s) => sum + Math.round(pts(s.card_id) * draft.bench_pts_multiplier), 0);
        const rotation = draft.rotation
            .filter(r => (ROTATION_ROLES as readonly string[]).includes(r.role))
            .reduce((sum, r) => sum + pts(r.card_id), 0);
        const bullpen  = draft.rotation
            .filter(r => !(ROTATION_ROLES as readonly string[]).includes(r.role))
            .reduce((sum, r) => sum + pts(r.card_id), 0);
        return { lineup, bench, rotation, bullpen, total: lineup + bench + rotation + bullpen };
    }, [draft, cardMap, defaultLineup]);

    const draftHistory = useMemo(() =>
        [...draft.roster]
            .filter(s => s.draft_order !== null)
            .sort((a, b) => (a.draft_order ?? 0) - (b.draft_order ?? 0)),
        [draft.roster]
    );

    const rosterData: FieldViewRosterData = useMemo(() => ({
        roster: draft.roster,
        rotation: draft.rotation,
        benchPtsMultiplier: draft.bench_pts_multiplier,
        minBench: draft.min_bench,
        minBullpen: draft.min_bullpen,
        maxRotation: draft.num_starters,
    }), [draft.roster, draft.rotation, draft.bench_pts_multiplier, draft.min_bench, draft.min_bullpen, draft.num_starters]);

    const draftedCardIds = useMemo(() => {
        const ids = new Set<string>();
        draft.roster.forEach(s => ids.add(s.card_id));
        draft.lineups.forEach(ln => ln.slots.forEach(s => ids.add(s.card_id)));
        draft.rotation.forEach(r => ids.add(r.card_id));
        return [...ids];
    }, [draft.roster, draft.lineups, draft.rotation]);

    const pendingLabel = pendingSlot
        ? pendingSlot.kind === 'field'    ? `Filling: ${pendingSlot.position}`
        : pendingSlot.kind === 'rotation' ? `Filling: ${pendingSlot.role}`
        : pendingSlot.kind === 'bench'    ? `Filling: ${pendingSlot.role}`
        : 'Adding to roster'
        : null;

    const allowedSources = useMemo(() => {
        const restricted = draft.allowed_card_sources ?? [];
        return restricted.length > 0
            ? CARD_SOURCES.filter(s => restricted.includes(s.key))
            : [...CARD_SOURCES];
    }, [draft.allowed_card_sources]);

    const draftPanel = (
        <DraftPanel
            draftSource={draftSource}
            onSourceChange={setDraftSource}
            allowedSources={allowedSources}
            pendingLabel={pendingLabel}
            searchFilters={searchFilters}
            draftedCardIds={draftedCardIds}
            onCardPicked={handleCardPicked}
        />
    );

    const fieldViewContent = (
        <FieldView
            lineup={defaultLineup}
            cardMap={cardMap}
            onSlotClick={(pos, slot) => {
                if (!showEditControls) return;
                setPendingSlot({ kind: 'field', position: pos, current: slot });
            }}
            onBenchClick={(role, current) => {
                if (!showEditControls) return;
                setPendingSlot({ kind: 'bench', role, current });
            }}
            onRoleClick={(role, current) => {
                if (!showEditControls) return;
                setPendingSlot({ kind: 'rotation', role, current });
            }}
            readOnly={!showEditControls}
            activePosition={activeFieldPosition}
            rosterData={rosterData}
            hoveredCardId={hoveredCardId}
            onCardHover={setHoveredCardId}
        />
    );

    const depthChartContent = (
        <DepthChartPanel
            team={draft}
            cardMap={cardMap}
            onSlotClick={(pos, slot) => {
                if (!showEditControls) return;
                setPendingSlot({ kind: 'field', position: pos, current: slot });
            }}
            onRoleClick={(role, current) => {
                if (!showEditControls) return;
                setPendingSlot({ kind: 'rotation', role, current });
            }}
            onBenchClick={(role, current) => {
                if (!showEditControls) return;
                setPendingSlot({ kind: 'bench', role, current });
            }}
            readOnly={!showEditControls}
            activePosition={activeFieldPosition}
            activeRole={activeRole}
            hoveredCardId={hoveredCardId}
            onCardHover={setHoveredCardId}
        />
    );

    const draftHistoryContent = (
        <div className="flex flex-col gap-0.5 p-4">
            {draftHistory.length === 0 ? (
                <p className="text-[12px] text-(--text-tertiary) py-4 text-center">No draft history yet.</p>
            ) : draftHistory.map((slot, i) => {
                const card = cardMap[slot.card_id];
                return (
                    <div key={i} className="flex items-center gap-3 min-h-9">
                        <span className="text-[11px] font-bold w-6 shrink-0 text-right text-(--text-tertiary)">
                            {slot.draft_order ?? i + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                            {card
                                ? <CardItemCompactFromCardDatabaseRecord card={card} />
                                : <span className="text-[11px] text-(--text-tertiary)">{slot.card_id}</span>
                            }
                        </div>
                    </div>
                );
            })}
        </div>
    );

    const settingsChanges = pendingSettings ? getSettingsChanges(draft, pendingSettings) : [];

    const settingsTabContent = (
        <div className="relative flex flex-col">
            <TeamSettingsForm
                team={settingsDraft}
                onChange={updates => setPendingSettings(prev => ({ ...(prev ?? {}), ...updates }))}
            />
            {pendingSettings && (
                <div className="sticky bottom-0 border-t border-(--divider) bg-(--background-primary) px-4 py-3 flex flex-col gap-2">
                    {settingsChanges.length > 0 && (
                        <ul className="flex flex-col gap-0.5">
                            {settingsChanges.map(line => (
                                <li key={line} className="text-[11px] text-(--text-secondary) flex items-start gap-1.5">
                                    <span className="text-amber-500 mt-px shrink-0">→</span>
                                    {line}
                                </li>
                            ))}
                        </ul>
                    )}
                    <div className="flex gap-2">
                        <button
                            type="button"
                            onClick={() => { update(pendingSettings); setPendingSettings(null); }}
                            className="flex-1 px-3 py-4 rounded-lg text-[12px] font-bold bg-(--showdown-red) text-white hover:opacity-90 cursor-pointer transition-opacity"
                        >
                            Apply Changes
                        </button>
                        <button
                            type="button"
                            onClick={() => setPendingSettings(null)}
                            className="px-3 py-4 rounded-lg text-[12px] font-bold border border-(--divider) text-(--text-secondary) hover:text-(--text-primary) cursor-pointer transition-colors"
                        >
                            Discard
                        </button>
                    </div>
                </div>
            )}
        </div>
    );

    // Eligible positions split into groups for the confirmation modal
    const confirmPositions = confirmCard ? getEligiblePositions(confirmCard) : [];
    const confirmFieldPositions   = confirmPositions.filter(p => !([...ROTATION_ROLES, ...BULLPEN_ROLES] as string[]).includes(p));
    const confirmRotationPositions = confirmPositions.filter(p => (ROTATION_ROLES as readonly string[]).includes(p));
    const confirmBullpenPositions  = confirmPositions.filter(p => (BULLPEN_ROLES as readonly string[]).includes(p));

    return (
        <div className={`flex flex-col ${embedded ? '' : 'h-[calc(100dvh-2.5rem)] overflow-hidden'}`}>
            <div
                className="flex items-start gap-3 px-4 py-2.5 border-b border-(--divider) shrink-0"
            >
                {onBack && (
                    <button type="button" onClick={onBack} className="text-(--text-tertiary) opacity-70 hover:text-(--text-primary) transition-colors shrink-0 mt-0.5 h-full">
                        <FaArrowLeft />
                    </button>
                )}

                {/* Team Header */}
                <div className="flex-1 min-w-0 space-y-1">
                    {/* Name + total pts */}
                    <div className="flex items-center gap-2 min-w-0">
                        <div className="text-xl font-black text-(--text-primary) truncate uppercase">{draft.name || 'Untitled Team'}</div>
                        {isTeamDrafting(draft) && (
                            <span className="text-[9px] font-black rounded px-1.5 py-0.5 leading-none shrink-0 bg-amber-500/20 text-amber-600 dark:text-amber-400">
                                DRAFTING
                            </span>
                        )}
                        
                        {/* Showdown Sets */}
                        <div className="flex items-center gap-0.5 flex-wrap">
                            {(draft.allowed_sets ?? [])
                            .sort((a, b) => a.localeCompare(b))
                                .map(s => {
                                    const img = imageForSet(s);
                                    return (
                                        <span key={s} className="flex items-center">
                                            {img && <img src={img} alt={s} className="h-4.5 w-auto object-fill" />}
                                        </span>
                                    );
                                })
                            }
                        </div>
                    </div>
                    {/* Subtitle row: PTS Breakdown */}
                    <div className="flex flex-wrap items-center gap-x-1.5 gap-y-1 mt-0.5">
                        <span className={`text-[12px] font-bold shrink-0 rounded-xl px-1.5`} style={{ backgroundColor: primary, color: getContrastColor(primary) }}>
                            {pointsBreakdown.total}{draft.pts_limit != null ? `/${draft.pts_limit}` : ''} pts
                        </span>
                        {([
                            { label: 'LINEUP', value: pointsBreakdown.lineup },
                            { label: 'BENCH', value: pointsBreakdown.bench },
                            { label: 'ROTATION', value: pointsBreakdown.rotation },
                            { label: 'BULLPEN', value: pointsBreakdown.bullpen },
                        ] as const).map(({ label, value }) => (
                            <span key={label} className="text-[10px] text-(--text-tertiary) px-2 py-0.5 rounded-lg font-bold" style={{ backgroundColor: team.secondary_color, color: getContrastColor(team.secondary_color) }}>
                                {label} <span className="font-semibold text-(--text-secondary)">{value}</span>
                            </span>
                        ))}
                        
                    </div>
                </div>
                {onToggleStar && (
                    <button
                        type="button"
                        onClick={onToggleStar}
                        className="flex items-center gap-1 rounded-md px-1.5 py-1 mt-0.5 text-[11px] font-semibold text-(--text-secondary) hover:bg-(--divider) cursor-pointer shrink-0"
                        aria-label={isStarred ? `Unstar ${draft.name}` : `Star ${draft.name}`}
                    >
                        {isStarred ? (
                            <FaStar className="h-3.5 w-3.5 text-yellow-300" />
                        ) : (
                            <FaRegStar className="h-3.5 w-3.5" />
                        )}
                        {isStarred ? "Starred" : "Star"}
                    </button>
                )}
                {!readOnly && (
                    <div className="flex items-center h-full gap-2 text-[11px] font-semibold shrink-0 mt-0.5">
                        {saveStatus === 'saving' && (
                            <span className="flex items-center gap-1 text-(--text-tertiary)">
                                <FaSpinner className="animate-spin text-[10px]" /> Saving
                            </span>
                        )}
                        {saveStatus === 'saved' && <span className="text-green-500">Saved</span>}
                        {saveStatus === 'error' && <span className="text-red-500">Error</span>}
                        {saveStatus === 'idle' && dirty && <span className="text-(--text-tertiary) opacity-60">Unsaved</span>}
                        {teamMode === 'complete' && (
                            <button
                                type="button"
                                onClick={() => setEditMode(true)}
                                className="flex items-center gap-1 px-2 py-1 h-8 text-md rounded-lg border border-(--divider) text-(--text-secondary) font-bold hover:text-(--text-primary) hover:border-(--text-tertiary) cursor-pointer transition-colors"
                            >
                                <FaPenToSquare /> Edit
                            </button>
                        )}
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

            {teamMode !== 'complete' && (
                <div className="flex items-center gap-3 px-4 py-2 shrink-0" style={bannerStyle}>
                    <span className={`w-2 h-2 rounded-full shrink-0 ${teamMode === 'drafting' ? 'animate-pulse' : ''}`} style={{ backgroundColor: bannerDotColor }} />
                    <span className="text-[11px] font-bold flex-1 drop-shadow-sm" style={{ color: bannerFillColor }}>
                        {teamMode === 'drafting'
                            ? 'DRAFTING — fill all required positions to complete your team'
                            : 'EDITING — changes are saved automatically'}
                    </span>
                    <div className="flex items-center gap-2 shrink-0">
                        {teamMode === 'drafting' && (
                            <>
                                <div className="w-24 h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: bannerTrackColor }}>
                                    <div
                                        className="h-full rounded-full transition-all"
                                        style={{ width: `${Math.min(100, (rosterProgress.filled / rosterProgress.total) * 100)}%`, backgroundColor: bannerFillColor }}
                                    />
                                </div>
                                <span className="text-[11px] font-black" style={{ color: bannerFillColor }}>
                                    {rosterProgress.filled}/{rosterProgress.total}
                                    {draft.pts_limit != null && ` • ${pointsBreakdown.total}/${draft.pts_limit} pts`}
                                </span>
                            </>
                        )}
                        {draft.pts_limit != null && token && (
                            <>
                                {lastAutofillStrategy && (
                                    <button
                                        type="button"
                                        onClick={handleReshuffle}
                                        disabled={reshuffling}
                                        className={`flex items-center gap-1 px-2 py-1 h-7 rounded-lg text-[11px] font-bold disabled:opacity-50 cursor-pointer transition-colors ${bannerBtnClass}`}
                                        title="Reshuffle with same strategy"
                                    >
                                        <FaShuffle className={reshuffling ? 'animate-spin' : ''} />
                                    </button>
                                )}
                                <button
                                    type="button"
                                    onClick={() => setShowAutofill(true)}
                                    className={`flex items-center gap-1 px-2 py-1 h-7 rounded-lg text-[11px] font-bold cursor-pointer transition-colors ${bannerBtnClass}`}
                                >
                                    <FaWandMagicSparkles className="text-[9px]" /> Autofill
                                </button>
                            </>
                        )}
                        {teamMode === 'editing' && (
                            <button
                                type="button"
                                onClick={() => setEditMode(false)}
                                className={`flex items-center gap-1 px-2 py-1 h-7 rounded-lg text-[11px] font-bold cursor-pointer transition-colors ${bannerBtnClass}`}
                            >
                                <FaCircleCheck className="text-[9px]" /> Done
                            </button>
                        )}
                    </div>
                </div>
            )}

            {/* Team Roster Content */}
            <div className={`flex flex-1 ${embedded ? '' : 'min-h-0 overflow-hidden'}`}>
                {isLg && teamMode === 'complete' ? (
                    /* Filled + large screen: FieldView fixed on left, Depth/Draft/Settings tabs on right */
                    <>
                        <div className="flex flex-col shrink-0 overflow-y-auto w-80 md:w-108 lg:w-124 xl:w-148 border-r border-(--divider)" onClick={() => setPendingSlot(null)}>
                            {fieldViewContent}
                        </div>
                        <Tabs.Root
                            defaultValue="depth"
                            className={`flex flex-col flex-1 min-w-0 ${embedded ? '' : 'min-h-0 overflow-hidden'}`}
                        >
                            {!isMlbTeam && (
                                <Tabs.List className="flex px-3 border-b border-(--divider) gap-x-1 py-1 shrink-0">
                                    <Tabs.Trigger value="depth"    className={TAB_TRIGGER_CLASS}>Depth Chart</Tabs.Trigger>
                                    <Tabs.Trigger value="draft"    className={TAB_TRIGGER_CLASS}>Draft</Tabs.Trigger>
                                    <Tabs.Trigger value="settings" className={TAB_TRIGGER_CLASS}>Settings</Tabs.Trigger>
                                </Tabs.List>
                            )}
                            <Tabs.Content value="depth" className="focus:outline-none flex-1 overflow-y-auto" onClick={() => setPendingSlot(null)}>
                                {depthChartContent}
                            </Tabs.Content>
                            {!isMlbTeam && (
                                <>
                                    <Tabs.Content value="draft" className="focus:outline-none flex-1 overflow-y-auto">
                                        {draftHistoryContent}
                                    </Tabs.Content>
                                    <Tabs.Content value="settings" className="focus:outline-none flex-1 overflow-y-auto">
                                        {settingsTabContent}
                                    </Tabs.Content>
                                </>
                            )}
                        </Tabs.Root>
                    </>
                ) : (
                    /* Drafting or small screen: tabbed left panel + DraftPanel on right (large screen) */
                    <>
                        <Tabs.Root
                            defaultValue="field"
                            className="
                                @container
                                flex flex-col shrink-0
                                overflow-y-auto
                                w-full lg:w-124 xl:w-148 2xl:w-190 3xl:w-256
                            "
                        >
                            <Tabs.List className="flex px-3 border-b border-(--divider) gap-x-1 py-1 sticky top-0 z-10 bg-(--background-primary) shrink-0">
                                <Tabs.Trigger value="field"    className={TAB_TRIGGER_CLASS}>Field View</Tabs.Trigger>
                                <Tabs.Trigger value="depth"    className={TAB_TRIGGER_CLASS}>Depth Chart</Tabs.Trigger>
                                {!isMlbTeam && <Tabs.Trigger value="draft"    className={TAB_TRIGGER_CLASS}>Draft</Tabs.Trigger>}
                                {!isMlbTeam && <Tabs.Trigger value="settings" className={TAB_TRIGGER_CLASS}>Settings</Tabs.Trigger>}
                            </Tabs.List>

                            <Tabs.Content value="field" className="focus:outline-none" onClick={() => setPendingSlot(null)}>
                                {fieldViewContent}
                            </Tabs.Content>

                            <Tabs.Content value="depth" className="focus:outline-none" onClick={() => setPendingSlot(null)}>
                                {depthChartContent}
                            </Tabs.Content>

                            {!isMlbTeam && (
                                <>
                                    <Tabs.Content value="draft" className="focus:outline-none">
                                        {draftHistoryContent}
                                    </Tabs.Content>

                                    <Tabs.Content value="settings" className="focus:outline-none">
                                        {settingsTabContent}
                                    </Tabs.Content>
                                </>
                            )}
                        </Tabs.Root>

                        {showEditControls && isLg && (
                            <div className="hidden md:flex flex-col flex-1 min-w-0 min-h-0 border-l border-(--divider)">
                                {draftPanel}
                            </div>
                        )}
                    </>
                )}
            </div>

            {showEditControls && !isLg && (
                <BottomSheet
                    isOpen={true}
                    onClose={() => setPendingSlot(null)}
                    title={pendingLabel ?? undefined}
                    dismissible={false}
                >
                    {draftPanel}
                </BottomSheet>
            )}

            <ToastMessage
                loadingStatus={draftToast ? {
                    message: draftToast.name,
                    subMessage: draftToast.position,
                    icon: <FaCircleCheck />,
                    backgroundColor: 'rgb(34, 197, 94)',
                } : null}
                isExiting={draftToastExiting}
            />

            {/* Confirmation modal: choose which position to assign the picked card */}
            {confirmCard && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
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

            {showAutofill && draft.pts_limit != null && (
                <AutofillPanel
                    ptsLimit={draft.pts_limit}
                    bucketSizes={{
                        offense: 9,
                        rotation: draft.num_starters,
                        bench: draft.min_bench,
                        bullpen: draft.min_bullpen,
                    }}
                    onConfirm={handleAutofill}
                    onClose={() => setShowAutofill(false)}
                />
            )}
        </div>
    );
}

const TAB_TRIGGER_CLASS =
    'relative flex items-center px-4 py-2 text-sm rounded-lg transition-colors ' +
    'data-[state=active]:bg-(--background-quaternary) data-[state=active]:font-bold ' +
    'data-[state=inactive]:text-(--text-tertiary) data-[state=inactive]:font-medium data-[state=inactive]:hover:bg-(--divider)';

type DraftPanelProps = {
    draftSource: CardSourceType;
    onSourceChange: (source: CardSourceType) => void;
    allowedSources: readonly { key: CardSourceType; label: string }[];
    pendingLabel: string | null;
    searchFilters: Record<string, string[]>;
    draftedCardIds: string[];
    onCardPicked: (card: CardDatabaseRecord) => void;
};

const DraftPanel = memo(function DraftPanel({ draftSource, onSourceChange, allowedSources, pendingLabel, searchFilters, draftedCardIds, onCardPicked }: DraftPanelProps) {
    return (
        <Tabs.Root
            value={draftSource}
            onValueChange={v => onSourceChange(v as CardSourceType)}
            className="flex flex-col h-full min-h-0"
        >
            <Tabs.List className="flex items-center px-3 border-b border-(--divider) gap-x-1 py-1 shrink-0">
                {allowedSources.map(s => (
                    <Tabs.Trigger key={s.key} value={s.key} className={TAB_TRIGGER_CLASS}>
                        {s.label}
                    </Tabs.Trigger>
                ))}
                {pendingLabel && (
                    <span className="ml-auto flex items-center gap-1.5 px-2 shrink-0 border rounded-lg border-amber-500 dark:border-amber-400">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                        <span className="text-md text-amber-500 dark:text-amber-400 font-semibold">
                            {pendingLabel}
                        </span>
                    </span>
                )}
            </Tabs.List>
            {allowedSources.map(s => (
                <Tabs.Content key={s.key} value={s.key} className="flex-1 min-h-0 flex flex-col focus:outline-none">
                    <ShowdownCardSearch
                        source={s.key}
                        compact={true}
                        disableLocalStorage={true}
                        verticalOffset="36"
                        defaultFilters={searchFilters}
                        excludeIds={draftedCardIds}
                        actionButton={{
                            icon: <FaPlus />,
                            label: 'Select',
                            bgColorClass: 'bg-(--showdown-red) opacity-95 border p-2 md:p-1 text-white shadow-sm rounded-full',
                            onClick: onCardPicked,
                        }}
                    />
                </Tabs.Content>
            ))}
        </Tabs.Root>
    );
});

function PositionButton({ label, onClick }: { label: string; onClick: () => void }) {
    return (
        <button
            type="button"
            onClick={onClick}
            className="px-3 py-2 rounded-lg text-[12px] font-bold
                bg-(--background-secondary) border border-(--divider)
                text-(--text-primary) hover:border-(--secondary) hover:text-(--secondary)
                transition-colors"
        >
            {label}
        </button>
    );
}
