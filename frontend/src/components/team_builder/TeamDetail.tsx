import { useState, useEffect, useRef, useMemo, useCallback, memo } from 'react';
import * as Tabs from '@radix-ui/react-tabs';

import type { Team, TeamUpdatePayload, LineupSlot, PitcherAssignment, TeamRosterSlot, AutofillStrategy, AutofillResult } from '../../api/userTeams';
import { fetchTeam, autofillTeam, isTeamDrafting, isTeamSetupValid, uploadTeamLogo, deleteTeamLogo, ROTATION_ROLES, BULLPEN_ROLES, MAX_STARTERS } from '../../api/userTeams';
import { AutofillPanel } from './AutofillPanel';
import { TeamLogo } from './TeamLogo';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import type { CardSource as CardSourceType } from '../../types/cardSource';
import { CardSource } from '../../types/cardSource';
import { useCardMap } from '../../hooks/useCardMap';
import { bannerTokens, getContrastTextColor } from "../../functions/colors";
import { FieldView } from './FieldView';
import type { FieldViewRosterData } from './FieldView';
import { DepthChartPanel } from './DepthChartPanel';
import { LineupPanel } from './LineupPanel';
import { TeamSettingsForm } from './TeamSettingsForm';
import { SlideOver } from '../shared/SlideOver';
import { tabButtonClass, radixTabTriggerClass } from '../shared/tabStyles';
import ShowdownCardSearch from '../cards/ShowdownCardSearch';
import {
    FaSpinner, FaArrowLeft, FaPlus, FaXmark, FaCircleCheck, FaWandMagicSparkles,
    FaShuffle, FaPenToSquare, FaStar, FaRegStar, FaGear, FaUsers,
    FaList, FaRing, FaClipboardList, FaListOl, FaCodeFork, FaPlay, FaChartLine,
    FaRobot, FaBaseball, FaHatWizard, FaMagnifyingGlass, FaArrowRight
} from 'react-icons/fa6';
import { useNavigate } from 'react-router-dom';
import { fetchTeamSimSeasons, startSeasonSim, cancelSimJob, fetchActiveSimJob, SimAlreadyRunningError, type SimSeasonListItem, type ActiveSimJob, type ChallengeInstance } from '../../api/sim';
import { SimSetupModal } from './sim/SimSetupModal';
import type { ManagerPreference } from '../../api/manager';
import { SimSeasonRow } from './sim/SimSeasonRow';
import { CardItemFromCardDatabaseRecord } from '../cards/CardItem';
import { CardItemCompactFromCardDatabaseRecord } from '../cards/CardItemCompact';
import { imageForSet } from '../shared/SiteSettingsContext';
import { TEAM_CARD_SOURCES, activeSources, allowedSetsForSource } from '../../domain/teamSets';
import { effectiveBenchBullpenMinimums } from '../../domain/roster';
import { ToastMessage } from '../shared/ToastMessage';
import { Modal } from '../shared/Modal';

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
    /** When provided, shows a "Make a copy" button that forks this team into the user's own. */
    onFork?: () => void | Promise<void>;
    /** Set when this team page was reached from a Team Challenge card - offers "Play Challenge"
     *  in place of the plain "Play" action. Not stored on the team itself: a refresh drops back
     *  to the normal action, and the team can still be freely reused for other challenges/sims. */
    challenge?: ChallengeInstance;
    /** True when the user just created this team (no pre-creation modal anymore) — starts them
     *  on the "Team Settings" setup step instead of straight into the draft. */
    isNewTeam?: boolean;
};


function getSearchFiltersForSlot(slot: PendingSlot | null): Record<string, string[]> {
    if (!slot) return {};
    if (slot.kind === 'field') {
        if (slot.position === 'SP') return { positions: ['STARTER'] };
        const posMap: Record<string, string[]> = {
            C: ['C'], '1B': ['1B'], '2B': ['2B'], '3B': ['3B'],
            SS: ['SS'], LF: ['LF/RF'], RF: ['LF/RF'], CF: ['CF'], DH: ['DH'],
        };
        const positions = posMap[slot.position];
        return { ...(positions ? { positions } : {}), player_type: ['HITTER'] };
    }
    if (slot.kind === 'rotation') {
        if (slot.role.startsWith('SP')) return { positions: ['STARTER'] };
        return { positions: ['RELIEVER', 'CLOSER'] };
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
    if ('allowed_sets' in pending || 'allowed_sets_by_source' in pending) {
        // Sets are per source, so report each source's list separately.
        const merged = { ...original, ...pending };
        for (const { value, label } of TEAM_CARD_SOURCES) {
            const orig = allowedSetsForSource(original, value).slice().sort().join(', ') || 'all';
            const next = allowedSetsForSource(merged, value).slice().sort().join(', ') || 'all';
            if (orig !== next) lines.push(`${label} sets: ${orig} → ${next}`);
        }
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

function getEligiblePositions(card: CardDatabaseRecord, numStarters: number): string[] {
    if (card.is_pitcher) {
        if ('STARTER' in card.positions_and_defense) return ROTATION_ROLES.slice(0, Math.min(numStarters, MAX_STARTERS));
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

export function TeamDetail({ team, onSave, onBack, onReload, token, readOnly = false, embedded = false, isStarred = false, onToggleStar, onFork, challenge, isNewTeam = false }: TeamDetailProps) {
    const [draft, setDraft] = useState<Team>(team);
    const [forking, setForking] = useState(false);
    // Setup flow: a freshly created (or still-empty) team opens on the "Team Settings" step;
    // otherwise straight into "Drafting". Steps are freely navigable via the banner chips.
    const [setupStep, setSetupStep] = useState<'settings' | 'draft'>(
        () => (isNewTeam || team.roster.length === 0) ? 'settings' : 'draft',
    );

    const [pendingSlot, setPendingSlot] = useState<PendingSlot | null>(null);
    const [confirmCard, setConfirmCard] = useState<CardDatabaseRecord | null>(null);
    // Bumped after each successful draft pick to clear the mobile search's leftover text/filters.
    const [draftSearchResetKey, setDraftSearchResetKey] = useState(0);
    const [dirty, setDirty] = useState(false);
    const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
    const [stale, setStale] = useState(false);
    const [draftSource, setDraftSource] = useState<CardSourceType>(CardSource.BOT);
    const [draftToast, setDraftToast] = useState<{ name: string; position: string } | null>(null);
    const [draftToastExiting, setDraftToastExiting] = useState(false);
    const [showAutofill, setShowAutofill] = useState(false);
    const [lastAutofillStrategy, setLastAutofillStrategy] = useState<AutofillStrategy | null>(null);
    const [reshuffling, setReshuffling] = useState(false);
    // Staged autofill result, shown as a preview (with a reshuffle option) before it's
    // committed to the draft and picked up by the auto-save effect.
    const [autofillPreview, setAutofillPreview] = useState<{ strategy: AutofillStrategy; result: AutofillResult } | null>(null);

    const rosterSlots = useMemo(() => {
        const base = draft.roster.map(s => ({ card_id: s.card_id, card_source: s.card_source }));
        if (!autofillPreview) return base;
        const seen = new Set(base.map(s => s.card_id));
        const previewOnly = autofillPreview.result.roster
            .filter(s => !seen.has(s.card_id))
            .map(s => ({ card_id: s.card_id, card_source: s.card_source }));
        return [...base, ...previewOnly];
    }, [draft.roster, autofillPreview]);
    const { cardMap, loading: isLoadingCards, addCard } = useCardMap(rosterSlots, token);
    const [editMode, setEditMode] = useState(false);
    const [pendingSettings, setPendingSettings] = useState<TeamUpdatePayload | null>(null);
    const [showSettingsModal, setShowSettingsModal] = useState(false);
    const [showSimModal, setShowSimModal] = useState(false);
    const [showChallengeConfirm, setShowChallengeConfirm] = useState(false);
    const [startingChallenge, setStartingChallenge] = useState(false);
    const [challengeError, setChallengeError] = useState<string | null>(null);
    const [challengeRunningJob, setChallengeRunningJob] = useState<{ jobId: string; teamId: string | null } | null>(null);
    const [logoUploading, setLogoUploading] = useState(false);
    // null = not loaded yet. The Sims tab only appears once this comes back non-empty, so a
    // team that's never been played shows no dead tab.
    const [teamSeasons, setTeamSeasons] = useState<SimSeasonListItem[] | null>(null);
    // The signed-in user's own in-flight job, if any - shown (and cancellable) in the Sims tab
    // only when it belongs to *this* team, so a job started elsewhere doesn't show up here.
    const [activeJob, setActiveJob] = useState<ActiveSimJob | null>(null);
    const [cancellingJob, setCancellingJob] = useState(false);
    const navigate = useNavigate();
    const [hoveredCardId, setHoveredCardId] = useState<string | null>(null);
    const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const [isLg, setIsLg] = useState(() => window.matchMedia('(min-width: 1024px)').matches);

    useEffect(() => {
        const mq = window.matchMedia('(min-width: 1024px)');
        const handler = (e: MediaQueryListEvent) => {
            setIsLg(e.matches);
            // Crossing down into the mobile SlideOver layout: clear any pending slot left over
            // from the desktop panel so the slideover doesn't spring open immediately.
            if (!e.matches) setPendingSlot(null);
        };
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

    useEffect(() => { setDraft(team); setDirty(false); setSaveStatus('idle'); setEditMode(false); setPendingSettings(null); setShowSettingsModal(false); }, [team]);

    // Re-pick the setup step only when the underlying team actually changes (e.g. forking into a
    // different team), never on the same-team prop churn from an auto-save round-trip — that
    // would kick the user back to Settings mid-edit.
    useEffect(() => {
        setSetupStep((isNewTeam || team.roster.length === 0) ? 'settings' : 'draft');
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [team.team_id]);

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

    // Recent simulations played with this team, across every user — a public team can be
    // simulated by anyone, not just its owner, so this isn't limited to the viewer's own runs.
    // Synthetic (MLB/ASG) teams have no real team_id and simply never fetch, which is fine:
    // `teamSeasons` staying null already means the Sims tab doesn't render.
    useEffect(() => {
        if (!team.team_id) return;
        let stale = false;
        fetchTeamSimSeasons(team.team_id, token)
            .then(seasons => { if (!stale) setTeamSeasons(seasons); })
            .catch(() => { if (!stale) setTeamSeasons([]); });
        return () => { stale = true; };
    }, [team.team_id, token]);

    // The user's own in-flight job (at most one can exist) - lets the Sims tab surface it, so a
    // stuck run can be found and cancelled without having to trigger the blocked-start 429 first.
    useEffect(() => {
        if (!team.team_id || !token) return;
        let stale = false;
        fetchActiveSimJob(token)
            .then(job => { if (!stale) setActiveJob(job); })
            .catch(() => { if (!stale) setActiveJob(null); });
        return () => { stale = true; };
    }, [team.team_id, token]);

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

    // Flush any pending debounced save before navigating away, so a change made in the last
    // 1.5s isn't lost — and, for a just-created team, so the abandon-cleanup on the parent sees
    // the real roster rather than deleting a team that does have picks.
    async function handleBack() {
        if (dirty && !readOnly) {
            if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
            try {
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
                const { team_id, user_id, created_at, updated_at, total_points, ...payload } = draft;
                await onSave(payload);
            } catch { /* leaving anyway */ }
        }
        onBack?.();
    }


    // Set restrictions are per card source, so the draft panel's filters follow the active tab.
    const { allowed_sets, allowed_sets_by_source, player_filters } = draft;
    const searchFilters = useMemo(() => {
        const sets = allowedSetsForSource({ allowed_sets, allowed_sets_by_source }, draftSource);
        return {
            ...(player_filters ?? {}),
            ...getSearchFiltersForSlot(pendingSlot),
            ...(sets.length ? { showdown_set: sets } : {}),
        };
    }, [pendingSlot, draftSource, allowed_sets, allowed_sets_by_source, player_filters]);

    function update(updates: TeamUpdatePayload) {
        setDraft(prev => ({ ...prev, ...updates } as Team));
        setDirty(true);
    }

    /** Runs autofill and stages the result as a preview rather than committing it straight to
     *  the draft — the user reviews it (and can reshuffle for a different result) before it's
     *  applied and picked up by the auto-save effect. */
    async function generateAutofillPreview(strategy: AutofillStrategy) {
        if (!token || !draft.team_id || reshuffling) return;
        setReshuffling(true);
        try {
            // Sets are left to the server: it queries one source at a time and applies that
            // source's own allowed sets, which a single flat filter here couldn't express.
            const result = await autofillTeam(draft.team_id, strategy, token, {});
            setAutofillPreview({ strategy, result });
        } finally {
            setReshuffling(false);
        }
    }

    function acceptAutofillPreview() {
        if (!autofillPreview) return;
        const { strategy, result } = autofillPreview;
        update({ roster: result.roster, lineups: result.lineups, rotation: result.rotation });
        const added = result.roster.length - draft.roster.length;
        setLastAutofillStrategy(strategy);
        setDraftToast({ name: 'Roster Autofilled', position: `${added} player${added !== 1 ? 's' : ''} added` });
        setAutofillPreview(null);
    }

    function handleReshuffle() {
        if (lastAutofillStrategy) generateAutofillPreview(lastAutofillStrategy);
    }

    async function handleLogoUpload(file: File) {
        if (!token || !draft.team_id || logoUploading) return;
        setLogoUploading(true);
        try {
            const updated = await uploadTeamLogo(draft.team_id, file, token);
            setDraft(prev => ({ ...prev, logo_url: updated.logo_url }));
        } catch (err) {
            console.error('Failed to upload team logo', err);
        } finally {
            setLogoUploading(false);
        }
    }

    async function handleLogoRemove() {
        if (!token || !draft.team_id || logoUploading) return;
        setLogoUploading(true);
        try {
            const updated = await deleteTeamLogo(draft.team_id, token);
            setDraft(prev => ({ ...prev, logo_url: updated.logo_url }));
        } catch (err) {
            console.error('Failed to remove team logo', err);
        } finally {
            setLogoUploading(false);
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
            const roster = [...draft.roster.filter(s => s.roster_position !== position), rosterSlot];
            update({ roster });
        } else if (/^BE\d+$/.test(position)) {
            const roster = [...draft.roster.filter(s => s.roster_position !== position), rosterSlot];
            update({ roster });
        } else if (position === 'BE') {
            update({ roster: [...draft.roster, rosterSlot] });
        } else {
            // Field position: update roster only — lineups/rotation are re-derived from the roster on save.
            const roster = [...draft.roster.filter(s => s.roster_position !== position), rosterSlot];
            update({ roster });
        }

        setDraftToast({ name: card.name, position });
        setConfirmCard(null);
        setPendingSlot(null);
        setDraftSearchResetKey(k => k + 1);
    }

    const isDrafting = isTeamDrafting(draft);
    // The Lineup tab is only meaningful once every roster spot is filled — hide it while the
    // roster is still being built out.
    const rosterFull = draft.roster.length >= draft.roster_size;
    const teamMode: 'drafting' | 'editing' | 'complete' = readOnly ? 'complete' : isDrafting ? 'drafting' : editMode ? 'editing' : 'complete';
    const showEditControls = !readOnly && teamMode !== 'complete';
    // Real MLB/WBC rosters are synthesized read-only from the card archive — there's no draft history or editable settings to show
    const isMlbTeam = team.source === 'mlb';
    // A season needs a complete roster and a signed-in owner (the sim endpoint is authenticated).
    // Synthetic MLB/ASG teams aren't saved, so there is no team_id for the job to reference.
    const canSimulate = !!token && !isMlbTeam && !isDrafting && team.source === 'user' && !!team.team_id;
    // Scoped to this team so a job started from a different team's page doesn't show up here.
    const activeJobForTeam = activeJob && activeJob.team_id === team.team_id ? activeJob : null;
    const hasSims = (!!teamSeasons && teamSeasons.length > 0) || !!activeJobForTeam;

    const settingsDraft = useMemo(
        () => pendingSettings ? { ...draft, ...pendingSettings } as Team : draft,
        [draft, pendingSettings],
    );

    const defaultLineup = draft.lineups[0] ?? { name: 'Default', slots: [] };
    const primary = draft.primary_color || 'rgb(0,0,0)';
    const secondary = draft.secondary_color || 'rgb(100,100,100)';

    // Banner color tokens derived from team colors. The banner is a left→right
    // primary→secondary gradient, so the left side (dot + message) contrasts against
    // primary while the right side (progress + controls) contrasts against secondary.
    const bannerLeft  = bannerTokens(primary);
    const bannerRight = bannerTokens(secondary);
    const bannerStyle = { background: `linear-gradient(to right, ${primary}, ${secondary})` };

    const effectiveBucketMins = useMemo(() => effectiveBenchBullpenMinimums(draft), [draft]);

    const rosterProgress = useMemo(() => {
        const { bench: benchTarget, bullpen: bullpenTarget } = effectiveBucketMins;
        const filledLineup = (draft.lineups[0]?.slots ?? []).length;
        const filledStarters = draft.rotation.filter(r => (ROTATION_ROLES as readonly string[]).includes(r.role)).length;
        const filledBench = draft.roster.filter(s => s.roster_position === 'BE').length;
        const filledBullpen = draft.rotation.filter(r => !(ROTATION_ROLES as readonly string[]).includes(r.role)).length;
        const filled = filledLineup + Math.min(filledStarters, draft.num_starters) + Math.min(filledBench, benchTarget) + Math.min(filledBullpen, bullpenTarget);
        const total = 9 + draft.num_starters + benchTarget + bullpenTarget;
        return { filled, total };
    }, [draft, effectiveBucketMins]);

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
        minBench: effectiveBucketMins.bench,
        minBullpen: effectiveBucketMins.bullpen,
        maxRotation: draft.num_starters,
    }), [draft.roster, draft.rotation, draft.bench_pts_multiplier, effectiveBucketMins, draft.num_starters]);

    const previewRosterData: FieldViewRosterData | null = useMemo(() => {
        if (!autofillPreview) return null;
        return {
            roster: autofillPreview.result.roster,
            rotation: autofillPreview.result.rotation,
            benchPtsMultiplier: draft.bench_pts_multiplier,
            minBench: effectiveBucketMins.bench,
            minBullpen: effectiveBucketMins.bullpen,
            maxRotation: draft.num_starters,
        };
    }, [autofillPreview, draft.bench_pts_multiplier, effectiveBucketMins, draft.num_starters]);
    const previewLineup = autofillPreview?.result.lineups[0] ?? { name: 'Default', index: 0, slots: [] };

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

    const allowedSources = useMemo(
        () => activeSources({ allowed_card_sources: draft.allowed_card_sources })
            .map(value => ({ key: value, label: TEAM_CARD_SOURCES.find(s => s.value === value)!.label })),
        [draft.allowed_card_sources],
    );

    const draftPanel = (
        <DraftPanel
            draftSource={draftSource}
            onSourceChange={setDraftSource}
            allowedSources={allowedSources}
            pendingLabel={pendingLabel}
            searchFilters={searchFilters}
            draftedCardIds={draftedCardIds}
            onCardPicked={handleCardPicked}
            onDismissPending={() => setPendingSlot(null)}
        />
    );

    // Bot/WOTC/WBC source selector rendered in the SlideOver's fixed header so it stays
    // reachable alongside the search results. stopPropagation avoids interfering with
    // taps elsewhere in the header.
    const draftSourceTabs = (
        <div
            className="flex items-center w-full justify-start gap-x-1 px-3 overflow-x-auto scrollbar-hide"
            onMouseDown={e => e.stopPropagation()}
            onTouchStart={e => e.stopPropagation()}
        >
            {allowedSources.map(s => (
                <button
                    key={s.key}
                    type="button"
                    onClick={() => setDraftSource(s.key)}
                    className={tabButtonClass(draftSource === s.key)}
                >
                    {s.label}
                </button>
            ))}
            {pendingLabel && (
                <span className="ml-auto text-sm flex items-center gap-1.5 pl-2 pr-1 py-1 shrink-0 border rounded-lg border-amber-500 dark:border-amber-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                    <span className=" text-amber-500 dark:text-amber-400 font-semibold">
                        {pendingLabel}
                    </span>
                    <button
                        type="button"
                        onClick={() => setPendingSlot(null)}
                        className="text-amber-500 dark:text-amber-400 hover:opacity-70 cursor-pointer p-1"
                        aria-label="Cancel filling"
                    >
                        <FaXmark />
                    </button>
                </span>
            )}
        </div>
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
            isLoadingCards={isLoadingCards}
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
            onReorder={showEditControls ? updates => update(updates) : undefined}
            readOnly={!showEditControls}
            activePosition={activeFieldPosition}
            activeRole={activeRole}
            hoveredCardId={hoveredCardId}
            onCardHover={setHoveredCardId}
            isLoadingCards={isLoadingCards}
        />
    );

    const lineupPanelContent = (
        <LineupPanel
            lineups={draft.lineups}
            cardMap={cardMap}
            onLineupsChange={userLineups => {
                // Merge user-created lineups back with the computed Default (index 0)
                const defaultLn = draft.lineups.find(ln => ln.name === 'Default');
                const next = [...(defaultLn ? [defaultLn] : []), ...userLineups];
                update({ lineups: next });
            }}
            readOnly={readOnly}
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

    async function handleCancelActiveJob() {
        if (!token || !activeJobForTeam) return;
        setCancellingJob(true);
        try {
            await cancelSimJob(activeJobForTeam.job_id, token);
            setActiveJob(null);
        } catch {
            // Leave the banner in place - the user can retry, or open it to see what happened.
        } finally {
            setCancellingJob(false);
        }
    }

    const simsContent = (
        <div className="flex flex-col gap-1.5 p-4">
            {activeJobForTeam && (
                <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-(--background-tertiary) ring-1 ring-(--showdown-blue)/40">
                    <FaSpinner className="animate-spin text-(--text-tertiary) text-[13px] shrink-0" />
                    <div className="min-w-0 flex-1">
                        <div className="text-[12px] font-bold text-(--text-primary) truncate">
                            {activeJobForTeam.phase ?? 'Starting simulation'}
                        </div>
                        {activeJobForTeam.games_total > 0 && (
                            <div className="text-[11px] text-(--text-tertiary)">
                                {activeJobForTeam.games_completed.toLocaleString()} / {activeJobForTeam.games_total.toLocaleString()} games
                            </div>
                        )}
                    </div>
                    <button
                        type="button"
                        onClick={() => navigate(`/teams/${team.team_id}/sim/${activeJobForTeam.job_id}`)}
                        className="shrink-0 text-[11px] font-bold px-2 py-1.5 rounded-lg border border-(--divider) text-(--text-secondary) hover:text-(--text-primary) cursor-pointer transition-colors"
                    >
                        View
                    </button>
                    <button
                        type="button"
                        onClick={handleCancelActiveJob}
                        disabled={cancellingJob}
                        className="shrink-0 text-[11px] font-bold px-2 py-1.5 rounded-lg text-red-400 hover:text-red-300 disabled:opacity-50 cursor-pointer transition-colors"
                    >
                        Cancel
                    </button>
                </div>
            )}
            {(teamSeasons ?? []).map(entry => (
                <SimSeasonRow
                    key={entry.entry_id}
                    entry={entry}
                    showTime
                    onOpen={() => entry.job_id && navigate(`/teams/${team.team_id}/sim/${entry.job_id}`)}
                />
            ))}
        </div>
    );

    const settingsChanges = pendingSettings ? getSettingsChanges(draft, pendingSettings) : [];

    function closeSettingsModal() {
        setPendingSettings(null);
        setShowSettingsModal(false);
    }

    /** Queue a season and hand off to the job's own URL, which owns polling and the result. */
    async function handleStartSim(options: { year: number; set: string; replaces: string; manager?: ManagerPreference }) {
        if (!token) return;
        const { job_id } = await startSeasonSim({ team_id: team.team_id, ...options }, token);
        setShowSimModal(false);
        navigate(`/teams/${team.team_id}/sim/${job_id}`);
    }

    /** Same as `handleStartSim`, but year/club/budget all come from the challenge instance - the
     *  backend re-derives and enforces them server-side regardless of what's sent here. */
    async function handleStartChallenge() {
        if (!token || !challenge) return;
        setStartingChallenge(true);
        setChallengeError(null);
        setChallengeRunningJob(null);
        try {
            const { job_id } = await startSeasonSim({
                team_id: team.team_id,
                year: challenge.year,
                set: draft.allowed_sets?.[0] ?? '2000',
                replaces: challenge.replaces_abbr,
                challenge_instance_id: challenge.instance_id,
            }, token);
            setShowChallengeConfirm(false);
            navigate(`/teams/${team.team_id}/sim/${job_id}`);
        } catch (err) {
            if (err instanceof SimAlreadyRunningError) setChallengeRunningJob({ jobId: err.jobId, teamId: err.teamId });
            setChallengeError(err instanceof Error ? err.message : 'Failed to start the challenge.');
            setStartingChallenge(false);
        }
    }

    /** Team total PTS if `confirmCard` were dropped into `position` — mirrors the roster
     *  mutation in handleConfirmPosition (BE appends and is multiplied; every other slot
     *  replaces whatever currently holds that roster_position). */
    const projectedTotalForPosition = (position: string): number => {
        if (!confirmCard) return pointsBreakdown.total;
        const addedPts = position === 'BE'
            ? Math.round(confirmCard.points * draft.bench_pts_multiplier)
            : confirmCard.points;
        const removedPts = position === 'BE'
            ? 0
            : draft.roster
                .filter(s => s.roster_position === position)
                .reduce((sum, s) => sum + (cardMap[s.card_id]?.points ?? 0), 0);
        return pointsBreakdown.total + addedPts - removedPts;
    };

    // Eligible positions split into groups for the confirmation modal
    const confirmPositions = confirmCard ? getEligiblePositions(confirmCard, draft.num_starters) : [];
    const confirmFieldPositions   = confirmPositions.filter(p => !([...ROTATION_ROLES, ...BULLPEN_ROLES] as string[]).includes(p));
    const confirmRotationPositions = confirmPositions.filter(p => (ROTATION_ROLES as readonly string[]).includes(p));
    const confirmBullpenPositions  = confirmPositions.filter(p => (BULLPEN_ROLES as readonly string[]).includes(p));

    /** Name of the player currently holding `position`, if the pick would replace someone.
     *  Mirrors handleConfirmPosition: 'BE' appends (no replacement); every other slot
     *  swaps out whatever roster entry currently holds that roster_position. */
    const replacedPlayerName = (position: string): string | null => {
        if (position === 'BE') return null;
        const slot = draft.roster.find(s => s.roster_position === position);
        return slot ? cardMap[slot.card_id]?.name ?? null : null;
    };

    const renderPositionButton = (pos: string) => {
        const projected = projectedTotalForPosition(pos);
        return (
            <PositionButton
                key={pos}
                label={pos}
                onClick={() => handleConfirmPosition(pos)}
                currentPts={pointsBreakdown.total}
                projectedPts={projected}
                overLimit={draft.pts_limit != null && projected > draft.pts_limit}
                replacingName={replacedPlayerName(pos)}
            />
        );
    };

    return (
        <div className={`flex flex-col ${embedded ? '' : 'lg:h-[calc(100dvh-2.5rem)] lg:overflow-hidden'}`}>
            
            {/* Header */}
            <div
                className="@container flex flex-col @lg:flex-row @lg:items-center gap-2 px-4 py-2.5 border-b border-(--divider) shrink-0"
            >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                    {onBack && (
                        <button type="button" onClick={handleBack} className="text-(--text-tertiary) opacity-70 hover:text-(--text-primary) transition-colors shrink-0 mt-0.5 h-full">
                            <FaArrowLeft />
                        </button>
                    )}

                    <TeamLogo
                        logoUrl={draft.logo_url}
                        abbreviation={draft.abbreviation}
                        primaryColor={primary}
                        editable={!readOnly && !isMlbTeam && !!token && !!draft.team_id}
                        uploading={logoUploading}
                        onUpload={handleLogoUpload}
                        onRemove={handleLogoRemove}
                        className="mt-0.5"
                    />

                    {/* Team Header */}
                    <div className="flex-1 min-w-0 space-y-1">
                        {/* Name + total pts */}
                        <div className="flex flex-wrap items-center gap-x-2 overflow-x-scroll scrollbar-hide">
                            <div className="text-xl font-black text-(--text-primary) truncate uppercase">{draft.name || 'Untitled Team'}</div>
                            
                            {draft.roster.length === draft.roster_size && (
                                <span className="flex gap-x-0.5 items-center text-[12px] font-semibold text-(--text-tertiary) shrink-0">
                                    <FaUsers /> {draft.roster.length}
                                </span>
                            )}

                            {/* Showdown Sets */}
                            <div className="flex items-center gap-0.5 ">
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
                        <div className="flex items-center gap-x-1.5 gap-y-1 mt-0.5 overflow-x-scroll scrollbar-hide">
                            <span className={`text-[12px] font-bold shrink-0 rounded-xl px-1.5`} style={{ backgroundColor: primary, color: getContrastTextColor(primary) }}>
                                {pointsBreakdown.total}{draft.pts_limit != null ? `/${draft.pts_limit}` : ''} PTS
                            </span>
                            <div className="hidden @[350px]:flex gap-1.5 items-center text-nowrap">
                                {([
                                    { label: 'LINEUP', value: pointsBreakdown.lineup },
                                    { label: 'BENCH', value: pointsBreakdown.bench },
                                    { label: 'ROTATION', value: pointsBreakdown.rotation },
                                    { label: 'BULLPEN', value: pointsBreakdown.bullpen },
                                ] as const).map(({ label, value }) => (
                                    <span key={label} className="flex gap-1 text-[10px] text-(--text-tertiary) px-2 py-0.5 rounded-lg font-bold" style={{ backgroundColor: team.secondary_color, color: getContrastTextColor(team.secondary_color) }}>
                                        {label} <span className="font-semibold text-(--text-secondary)">{value}</span>
                                    </span>
                                ))}
                            </div>

                        </div>
                    </div>

                    {/* {!readOnly && ( */}
                        <div className="flex items-center justify-center @lg:h-full gap-2 text-sm font-semibold">
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
                                    className="
                                        flex items-center justify-center 
                                        gap-1 px-2 py-1 h-8 w-full rounded-lg bg-quaternary
                                        text-md text-(--text-secondary) font-bold hover:text-(--text-primary) 
                                        cursor-pointer transition-colors
                                    "
                                >
                                    <FaPenToSquare /> Edit
                                </button>
                            )}
                        </div>
                    {/* )} */}
                </div>

                {/* Action buttons: wrap into a grid below the team info on narrow views, sit inline to the right once there's room */}
                {(onToggleStar || onFork || !readOnly || canSimulate) && (
                    <div className="grid grid-cols-2 @sm:grid-cols-3 @lg:grid-cols-4 @lg:items-center gap-2 @lg:w-auto shrink-0">
                        {onToggleStar && (
                            <button
                                type="button"
                                onClick={onToggleStar}
                                className="flex items-center justify-center gap-1 rounded-md px-1.5 py-1.5 @lg:py-1 text-[11px] font-semibold text-(--text-secondary) hover:bg-(--divider) cursor-pointer"
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
                        {onFork && (
                            <button
                                type="button"
                                disabled={forking}
                                onClick={async () => {
                                    setForking(true);
                                    try {
                                        await onFork();
                                    } finally {
                                        setForking(false);
                                    }
                                }}
                                className="flex items-center justify-center gap-1.5 rounded-md px-2 py-1.5 @lg:py-1 text-[11px] font-semibold text-(--background-primary) bg-(--secondary) hover:opacity-90 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
                                aria-label="Make a copy of this team"
                                title="Make an editable copy of this team"
                            >
                                {forking ? <FaSpinner className="h-3 w-3 animate-spin" /> : <FaCodeFork className="h-3 w-3" />}
                                Make a copy
                            </button>
                        )}
                        {canSimulate && teamMode === 'complete' && (
                            <button
                                type="button"
                                onClick={() => challenge ? setShowChallengeConfirm(true) : setShowSimModal(true)}
                                className="flex items-center justify-center gap-1.5 rounded-md h-8 px-2 py-1 text-sm font-semibold hover:opacity-90 cursor-pointer transition-opacity"
                                style={{
                                    backgroundImage: `linear-gradient(135deg, ${draft.primary_color}, ${draft.secondary_color})`,
                                    color: getContrastTextColor(draft.primary_color)
                                }}
                                aria-label={challenge ? `Play the ${challenge.title} challenge with this team` : 'Simulate a season with this team'}
                                title={challenge ? challenge.title : 'Drop this team into a real season and play all 162 games'}
                            >
                                <FaPlay className="h-3 w-3" />
                                {challenge ? 'Play Challenge' : 'Play'}
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
                <div className="flex items-center gap-1 px-4 py-2.5 shrink-0" style={bannerStyle}>
                    <span className={`w-2 h-2 rounded-full shrink-0 ${teamMode === 'drafting' ? 'animate-pulse' : ''}`} style={{ backgroundColor: bannerLeft.dot }} />
                    <span className="text-[11px] font-bold flex-1 drop-shadow-sm flex items-center gap-2" style={{ color: bannerLeft.fill }}>
                        {teamMode === 'drafting'
                            ? <SetupStepChips
                                step={setupStep}
                                onStep={setSetupStep}
                                settingsDone={draft.roster.length > 0}
                                draftProgress={`${rosterProgress.filled}/${rosterProgress.total}`}
                                color={bannerLeft.fill}
                              />
                            : <>EDITING<span className="hidden md:inline"> — changes are saved automatically</span></>}
                        {teamMode === 'editing' && (
                            <>
                                {!isMlbTeam && editMode && (
                                    <button
                                        type="button"
                                        onClick={() => setShowSettingsModal(true)}
                                        className={`flex items-center gap-1 px-2 py-1 h-8 rounded-lg text-[11px] font-bold cursor-pointer transition-colors ${bannerLeft.btnClass}`}
                                        aria-label="Team settings"
                                        title="Team settings"
                                    >
                                        <FaGear /> Settings
                                    </button>
                                )}
                            </>
                        )}
                    </span>
                    <div className="flex items-center gap-2 shrink-0">
                        {teamMode === 'drafting' && setupStep === 'draft' && (
                            <>
                                <div className="w-18 md:w-24 h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: bannerRight.track }}>
                                    <div
                                        className="h-full rounded-full transition-all"
                                        style={{ width: `${Math.min(100, (rosterProgress.filled / rosterProgress.total) * 100)}%`, backgroundColor: bannerRight.fill }}
                                    />
                                </div>
                                <span className="text-[11px] font-black" style={{ color: bannerRight.fill }}>
                                    {rosterProgress.filled}/{rosterProgress.total}
                                </span>
                            </>
                        )}
                        {token && (setupStep === 'draft' || teamMode === 'editing') && (
                            <>
                                {lastAutofillStrategy && (
                                    <button
                                        type="button"
                                        onClick={handleReshuffle}
                                        disabled={reshuffling}
                                        className={`flex items-center gap-1 px-2 py-1 h-7 rounded-lg text-[11px] font-bold disabled:opacity-50 cursor-pointer transition-colors ${bannerRight.btnClass}`}
                                        title="Reshuffle with same strategy"
                                    >
                                        <FaShuffle className={reshuffling ? 'animate-spin' : ''} />
                                    </button>
                                )}
                                <button
                                    type="button"
                                    onClick={() => setShowAutofill(true)}
                                    className={`flex items-center gap-1 px-2 py-1 h-7 rounded-lg text-[11px] font-bold cursor-pointer transition-colors ${bannerRight.btnClass}`}
                                >
                                    <FaWandMagicSparkles className="text-[9px]" /> Autofill
                                </button>
                            </>
                        )}
                        {teamMode === 'editing' && (
                            <>
                                <button
                                    type="button"
                                    onClick={() => setEditMode(false)}
                                    className={`flex items-center gap-1 px-2 py-1 h-7 rounded-lg text-[11px] font-bold cursor-pointer transition-colors ${bannerRight.btnClass}`}
                                >
                                    <FaCircleCheck className="text-[9px]" /> Done
                                </button>
                            </>
                        )}
                    </div>
                </div>
            )}

            {/* Team Roster Content */}
            <div className={`flex flex-1 ${embedded ? '' : 'lg:min-h-0 lg:overflow-hidden'}`}>
                {showEditControls && setupStep === 'settings' ? (
                    /* Setup step 1: team settings, edited inline (auto-saved) before drafting */
                    <div className="flex flex-col flex-1 min-w-0 lg:min-h-0 lg:overflow-y-auto scrollbar-hide">
                        <div className="flex-1">
                            <TeamSettingsForm team={draft} onChange={updates => update(updates)} />
                        </div>
                        <div className="sticky bottom-0 flex items-center justify-end gap-3 px-4 py-3 border-t border-(--divider) bg-(--background-primary)">
                            {!isTeamSetupValid(draft) && (
                                <span className="text-[11px] text-(--text-tertiary) mr-auto">Resolve the highlighted settings to continue.</span>
                            )}
                            <button
                                type="button"
                                onClick={() => setSetupStep('draft')}
                                disabled={!isTeamSetupValid(draft)}
                                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-[13px] font-bold text-white bg-(--showdown-red) hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-opacity"
                            >
                                Continue to Draft <FaArrowRight className="text-[11px]" />
                            </button>
                        </div>
                    </div>
                ) : isLg && teamMode === 'complete' ? (
                    /* Filled + large screen: FieldView fixed on left, Depth/Draft/Settings tabs on right */
                    <>
                        <div className="flex flex-col shrink-0 overflow-y-auto scrollbar-hide w-80 md:w-108 lg:w-124 xl:w-148 2xl:w-164 3xl:w-184 border-r border-(--divider)" onClick={() => setPendingSlot(null)}>
                            {fieldViewContent}
                        </div>
                        <Tabs.Root
                            defaultValue="depth"
                            className={`flex flex-col flex-1 min-w-0 overflow-x-scroll ${embedded ? '' : 'min-h-0 overflow-hidden'}`}
                        >
                            {!isMlbTeam && (
                                <Tabs.List className="flex px-3 border-b border-(--divider) gap-x-1 py-1 shrink-0 overflow-x-auto scrollbar-hide">
                                    <Tabs.Trigger value="depth"    className={TAB_TRIGGER_CLASS}><FaClipboardList className="inline mr-1" /><span>Depth <span className="hidden sm:inline"> Chart</span></span></Tabs.Trigger>
                                    {rosterFull && <Tabs.Trigger value="lineup"   className={TAB_TRIGGER_CLASS}><FaListOl className="inline mr-1" /> Lineup</Tabs.Trigger>}
                                    <Tabs.Trigger value="draft"    className={TAB_TRIGGER_CLASS}><FaList className="inline mr-1" /> Draft</Tabs.Trigger>
                                    {hasSims && <Tabs.Trigger value="sims" className={TAB_TRIGGER_CLASS}><FaChartLine className="inline mr-1" /> Sims</Tabs.Trigger>}
                                </Tabs.List>
                            )}
                            <Tabs.Content value="depth" className="focus:outline-none flex-1 overflow-y-auto scrollbar-hide" onClick={() => setPendingSlot(null)}>
                                {depthChartContent}
                            </Tabs.Content>
                            {rosterFull && (
                                <Tabs.Content value="lineup" className="focus:outline-none flex-1 overflow-y-auto scrollbar-hide" onClick={() => setPendingSlot(null)}>
                                    {lineupPanelContent}
                                </Tabs.Content>
                            )}
                            {!isMlbTeam && (
                                <Tabs.Content value="draft" className="focus:outline-none flex-1 overflow-y-auto scrollbar-hide">
                                    {draftHistoryContent}
                                </Tabs.Content>
                            )}
                            {hasSims && (
                                <Tabs.Content value="sims" className="focus:outline-none flex-1 overflow-y-auto scrollbar-hide">
                                    {simsContent}
                                </Tabs.Content>
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
                                overflow-y-auto scrollbar-hide
                                w-full lg:w-124 2xl:w-148 3xl:w-190 4xl:w-256
                            "
                        >
                            <Tabs.List className="flex px-3 border-b border-(--divider) gap-x-1 py-1 sticky top-0 z-10 bg-(--background-primary) shrink-0 overflow-x-auto scrollbar-hide">
                                <Tabs.Trigger value="field"    className={TAB_TRIGGER_CLASS}><FaRing className="inline mr-1" /> <span>Field<span className="hidden sm:inline ml-1">View</span></span></Tabs.Trigger>
                                <Tabs.Trigger value="depth"    className={TAB_TRIGGER_CLASS}><FaClipboardList className="inline mr-1" /> <span>Depth<span className="hidden sm:inline ml-1">Chart</span></span></Tabs.Trigger>
                                {rosterFull && <Tabs.Trigger value="lineup"   className={TAB_TRIGGER_CLASS}><FaListOl className="inline mr-1" /> Lineup</Tabs.Trigger>}
                                {!isMlbTeam && <Tabs.Trigger value="draft"    className={TAB_TRIGGER_CLASS}><FaList className="inline mr-1" />Draft</Tabs.Trigger>}
                                {hasSims && <Tabs.Trigger value="sims" className={TAB_TRIGGER_CLASS}><FaChartLine className="inline mr-1" />Sims</Tabs.Trigger>}
                            </Tabs.List>

                            <Tabs.Content value="field" className="focus:outline-none" onClick={() => setPendingSlot(null)}>
                                {fieldViewContent}
                            </Tabs.Content>

                            <Tabs.Content value="depth" className="focus:outline-none" onClick={() => setPendingSlot(null)}>
                                {depthChartContent}
                                {showEditControls && !isLg && <div className="h-48" />}
                            </Tabs.Content>

                            {rosterFull && (
                                <Tabs.Content value="lineup" className="focus:outline-none" onClick={() => setPendingSlot(null)}>
                                    {lineupPanelContent}
                                    {showEditControls && !isLg && <div className="h-48" />}
                                </Tabs.Content>
                            )}

                            {!isMlbTeam && (
                                <Tabs.Content value="draft" className="focus:outline-none">
                                    {draftHistoryContent}
                                    {showEditControls && !isLg && <div className="h-48" />}
                                </Tabs.Content>
                            )}

                            {hasSims && (
                                <Tabs.Content value="sims" className="focus:outline-none">
                                    {simsContent}
                                    {showEditControls && !isLg && <div className="h-48" />}
                                </Tabs.Content>
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

            {showEditControls && !isLg && setupStep === 'draft' && (
                <>
                    {/* Search FAB — hidden while the slideover is open, since the slideover's
                        own dismiss button occupies the same corner. A larger halo sits behind
                        it (same treatment as SlideOver's dismiss button) so it stays legible
                        over busy content, fading out via a radial mask rather than a hard edge. */}
                    {!pendingSlot && (
                        <div
                            className="lg:hidden fixed bottom-0 right-0 z-50 w-24 h-24 flex items-center justify-center pointer-events-none"
                            style={{
                                background: 'radial-gradient(circle, rgba(0,0,0,0.4) 0%, rgba(0,0,0,0.2) 40%, rgba(0,0,0,0) 72%)',
                                backdropFilter: 'blur(16px)',
                                WebkitBackdropFilter: 'blur(16px)',
                                maskImage: 'radial-gradient(circle, black 40%, transparent 72%)',
                                WebkitMaskImage: 'radial-gradient(circle, black 40%, transparent 72%)',
                            }}
                        >
                            <button
                                type="button"
                                onClick={() => setPendingSlot({ kind: 'roster' })}
                                aria-label="Search cards"
                                className="
                                    pointer-events-auto
                                    w-12 h-12 rounded-full flex items-center justify-center
                                    bg-(--showdown-red) text-white
                                    shadow-lg cursor-pointer hover:opacity-90 transition-opacity
                                "
                            >
                                <FaMagnifyingGlass className="text-[16px]" />
                            </button>
                        </div>
                    )}

                    <SlideOver
                        isOpen={pendingSlot !== null}
                        onClose={() => setPendingSlot(null)}
                        handleContent={draftSourceTabs}
                    >
                        <DraftPanel
                            draftSource={draftSource}
                            onSourceChange={setDraftSource}
                            allowedSources={allowedSources}
                            pendingLabel={pendingLabel}
                            searchFilters={searchFilters}
                            draftedCardIds={draftedCardIds}
                            onCardPicked={handleCardPicked}
                            resetTrigger={draftSearchResetKey}
                            hideSourceTabs
                        />
                    </SlideOver>
                </>
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
                        className="bg-(--background-primary) rounded-2xl w-full max-w-md shadow-2xl border border-(--divider) overflow-hidden"
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
                                <div className="grid grid-cols-2 lg:grid-cols-3 gap-1.5">
                                    {confirmFieldPositions.map(renderPositionButton)}
                                </div>
                            )}
                            {confirmRotationPositions.length > 0 && (
                                <>
                                    <div className="text-[10px] font-semibold text-(--text-tertiary) uppercase tracking-wide">Rotation</div>
                                    <div className="grid grid-cols-2 lg:grid-cols-3 gap-1.5">
                                        {confirmRotationPositions.map(renderPositionButton)}
                                    </div>
                                </>
                            )}
                            {confirmBullpenPositions.length > 0 && (
                                <>
                                    <div className="text-[10px] font-semibold text-(--text-tertiary) uppercase tracking-wide">Bullpen</div>
                                    <div className="flex flex-wrap gap-1.5">
                                        {confirmBullpenPositions.map(renderPositionButton)}
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Settings modal */}
            {showSimModal && (
                <SimSetupModal
                    showdownSet={draft.allowed_sets?.[0] ?? '2000'}
                    onCancel={() => setShowSimModal(false)}
                    onStart={handleStartSim}
                    onViewExisting={(jobId, teamId) => {
                        setShowSimModal(false);
                        navigate(`/teams/${teamId ?? team.team_id}/sim/${jobId}`);
                    }}
                />
            )}

            {/* Challenge launch confirm - year/club/budget are all already fixed by the
                challenge, so there's nothing left to pick, just a confirmation. */}
            {showChallengeConfirm && challenge && (() => {
                const fits = challenge.pts_limit == null || pointsBreakdown.total <= challenge.pts_limit;
                return (
                    <div
                        className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
                        onClick={() => !startingChallenge && setShowChallengeConfirm(false)}
                    >
                        <div
                            className="bg-(--background-primary) rounded-2xl w-full max-w-sm shadow-2xl border border-(--divider) overflow-hidden flex flex-col"
                            onClick={e => e.stopPropagation()}
                        >
                            <div className="px-4 pt-4 pb-3 border-b border-(--divider)">
                                <div className="text-[14px] font-black text-(--text-primary)">{challenge.title}</div>
                                <div className="text-[12px] text-(--text-secondary) mt-1">
                                    Bringing <span className="font-bold text-(--text-primary)">{draft.name}</span> to take over
                                    the {challenge.year} {challenge.replaces_abbr}.
                                </div>
                            </div>
                            <div className="px-4 py-3 flex flex-col gap-2">
                                {!fits && (
                                    <div className="text-[11px] text-red-400 px-2 py-1.5 rounded-lg border border-red-400/30 bg-red-400/5">
                                        This team costs {pointsBreakdown.total} pts, over the {challenge.pts_limit} pt challenge limit.
                                    </div>
                                )}
                                {challengeError && (
                                    <div className="flex items-center justify-between gap-2 text-[11px] text-red-400 px-2 py-1.5 rounded-lg border border-red-400/30 bg-red-400/5">
                                        <span>{challengeError}</span>
                                        {challengeRunningJob && (
                                            <button
                                                type="button"
                                                onClick={() => navigate(`/teams/${challengeRunningJob.teamId ?? team.team_id}/sim/${challengeRunningJob.jobId}`)}
                                                className="shrink-0 font-semibold underline underline-offset-2 hover:opacity-80 transition-opacity cursor-pointer"
                                            >
                                                View it
                                            </button>
                                        )}
                                    </div>
                                )}
                                <div className="flex gap-2 pt-1">
                                    <button
                                        type="button"
                                        onClick={() => setShowChallengeConfirm(false)}
                                        disabled={startingChallenge}
                                        className="flex-1 py-2.5 rounded-xl text-[13px] font-semibold border border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors cursor-pointer"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="button"
                                        onClick={handleStartChallenge}
                                        disabled={startingChallenge || !fits}
                                        className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-[13px] font-bold text-white bg-linear-to-r from-blue-500 to-red-500 hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                                    >
                                        {startingChallenge ? <FaSpinner className="animate-spin text-[11px]" /> : <FaPlay className="text-[11px]" />}
                                        Play
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                );
            })()}

            {showSettingsModal && (
                <Modal
                    title="Team Settings"
                    onClose={closeSettingsModal}
                    size="sm"
                    footer={
                        <>
                            {pendingSettings && settingsChanges.length > 0 && (
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
                                    onClick={() => {
                                        if (pendingSettings) update(pendingSettings);
                                        setPendingSettings(null);
                                        setShowSettingsModal(false);
                                    }}
                                    disabled={!pendingSettings || settingsChanges.length === 0}
                                    className="flex-1 px-3 py-4 rounded-lg text-[12px] font-bold bg-(--showdown-red) text-white hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-opacity"
                                >
                                    Apply Changes
                                </button>
                                <button
                                    type="button"
                                    onClick={closeSettingsModal}
                                    className="px-3 py-4 rounded-lg text-[12px] font-bold border border-(--divider) text-(--text-secondary) hover:text-(--text-primary) cursor-pointer transition-colors"
                                >
                                    {pendingSettings && settingsChanges.length > 0 ? 'Discard' : 'Close'}
                                </button>
                            </div>
                        </>
                    }
                >
                    <TeamSettingsForm
                        team={settingsDraft}
                        onChange={updates => setPendingSettings(prev => ({ ...(prev ?? {}), ...updates }))}
                    />
                </Modal>
            )}

            {showAutofill && (
                <AutofillPanel
                    ptsLimit={draft.pts_limit}
                    bucketSizes={{
                        offense: 9,
                        rotation: draft.num_starters,
                        bench: effectiveBucketMins.bench,
                        bullpen: effectiveBucketMins.bullpen,
                    }}
                    existingPts={{
                        offense: pointsBreakdown.lineup,
                        rotation: pointsBreakdown.rotation,
                        bench: pointsBreakdown.bench,
                        bullpen: pointsBreakdown.bullpen,
                    }}
                    onConfirm={generateAutofillPreview}
                    onClose={() => setShowAutofill(false)}
                />
            )}

            {/* Autofill result preview: reshuffle for a different result, or accept to commit
                it to the draft (which then flows through the normal auto-save). */}
            {autofillPreview && previewRosterData && (
                <Modal
                    title="Autofill Preview"
                    subtitle="Reshuffle for a different result, or use this roster as-is."
                    onClose={() => setAutofillPreview(null)}
                    size="md"
                    footer={
                        <div className="flex gap-2">
                            <button
                                type="button"
                                onClick={() => setAutofillPreview(null)}
                                className="px-3 py-2.5 rounded-xl text-[13px] font-semibold border border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors cursor-pointer"
                            >
                                Discard
                            </button>
                            <button
                                type="button"
                                onClick={() => generateAutofillPreview(autofillPreview.strategy)}
                                disabled={reshuffling}
                                className="flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-xl text-[13px] font-bold border border-(--divider) text-(--text-secondary) hover:text-(--text-primary) disabled:opacity-50 cursor-pointer transition-colors"
                            >
                                <FaShuffle className={reshuffling ? 'animate-spin' : ''} /> Reshuffle
                            </button>
                            <button
                                type="button"
                                onClick={acceptAutofillPreview}
                                disabled={reshuffling}
                                className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-[13px] font-bold text-white bg-linear-to-r from-blue-500 to-red-500 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-opacity"
                            >
                                <FaCircleCheck className="text-[11px]" /> Use This Roster
                            </button>
                        </div>
                    }
                >
                    {/* Field Value */}
                    <FieldView
                        lineup={previewLineup}
                        cardMap={cardMap}
                        onSlotClick={() => {}}
                        readOnly
                        rosterData={previewRosterData}
                        isLoadingCards={isLoadingCards}
                        showTotalPoints={true}
                    />
                </Modal>
            )}
        </div>
    );
}

const TAB_TRIGGER_CLASS = radixTabTriggerClass();

type DraftPanelProps = {
    draftSource: CardSourceType;
    onSourceChange: (source: CardSourceType) => void;
    allowedSources: readonly { key: CardSourceType; label: string }[];
    pendingLabel: string | null;
    searchFilters: Record<string, string[]>;
    draftedCardIds: string[];
    onCardPicked: (card: CardDatabaseRecord) => void;
    /** When true, hides the internal Bot/WOTC/WBC tab list — used when the tabs are
     *  rendered elsewhere (e.g. the SlideOver header) while source is controlled externally. */
    hideSourceTabs?: boolean;
    /** Clears the pending slot — shown as an X on the "Filling" badge. */
    onDismissPending?: () => void;
    /** Forwarded to ShowdownCardSearch — bump to clear search text/filters after a pick completes. */
    resetTrigger?: unknown;
};

const DraftPanel = memo(function DraftPanel({ draftSource, onSourceChange, allowedSources, pendingLabel, searchFilters, draftedCardIds, onCardPicked, hideSourceTabs = false, onDismissPending, resetTrigger }: DraftPanelProps) {
    return (
        <Tabs.Root
            value={draftSource}
            onValueChange={v => onSourceChange(v as CardSourceType)}
            className="flex flex-col gap-0 h-full min-h-0"
        >
            {!hideSourceTabs && (
                <Tabs.List className="flex items-center px-3 border-b border-(--divider) gap-x-1 py-1 shrink-0 overflow-x-auto scrollbar-hide">
                    {allowedSources.map(s => (
                        <Tabs.Trigger key={s.key} value={s.key} className={TAB_TRIGGER_CLASS}>
                            {s.key === 'BOT' && <FaRobot className="inline-block" />}
                            {s.key === 'WOTC' && <FaHatWizard className="inline-block" />}
                            {s.key === 'WBC' && <FaBaseball className="inline-block" />}
                            {s.label}
                        </Tabs.Trigger>
                    ))}
                    {pendingLabel && (
                        <span className="ml-auto flex text-sm items-center gap-1.5 pl-2 pr-1 shrink-0 border rounded-lg border-amber-500 dark:border-amber-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                            <span className=" text-amber-500 dark:text-amber-400 font-semibold">
                                {pendingLabel}
                            </span>
                            {onDismissPending && (
                                <button
                                    type="button"
                                    onClick={onDismissPending}
                                    className="text-amber-500 dark:text-amber-400 hover:opacity-70 cursor-pointer p-1"
                                    aria-label="Cancel filling"
                                >
                                    <FaXmark className="text-[11px]" />
                                </button>
                            )}
                        </span>
                    )}
                </Tabs.List>
            )}
            {allowedSources.map(s => (
                <Tabs.Content key={s.key} value={s.key} className="flex-1 min-h-0 flex flex-col focus:outline-none">
                    <ShowdownCardSearch
                        source={s.key}
                        compact={true}
                        disableLocalStorage={true}
                        verticalOffset="36"
                        defaultFilters={searchFilters}
                        lockDefaultFilters={false}
                        excludeIds={draftedCardIds}
                        resetTrigger={resetTrigger}
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

/** The two-step "Team Settings → Drafting" indicator shown in the drafting banner. Both steps
 *  are always clickable — the marks (check / number) are just progress hints. */
function SetupStepChips({ step, onStep, settingsDone, draftProgress, color }: {
    step: 'settings' | 'draft';
    onStep: (s: 'settings' | 'draft') => void;
    settingsDone: boolean;
    draftProgress: string;
    color: string;
}) {
    const chip = (id: 'settings' | 'draft', label: string, trailing: string | null, done: boolean) => (
        <button
            type="button"
            onClick={() => onStep(id)}
            className={`flex items-center gap-1.5 px-2 py-1 rounded-lg cursor-pointer transition-opacity ${step === id ? 'bg-black/20' : 'opacity-65 hover:opacity-100'}`}
            style={{ color }}
        >
            <span className="w-4 h-4 rounded-full border flex items-center justify-center text-[8px] shrink-0" style={{ borderColor: color }}>
                {done ? <FaCircleCheck /> : id === 'settings' ? '1' : '2'}
            </span>
            <span className="inline">{label}</span>
            {trailing && <span className="font-black tabular-nums">{trailing}</span>}
        </button>
    );
    return (
        <span className="flex items-center gap-0.5">
            {chip('settings', 'Team Settings', null, settingsDone)}
            <FaArrowRight className="text-[8px] opacity-40 shrink-0" style={{ color }} />
            {chip('draft', 'Drafting', step === 'draft' ? draftProgress : null, false)}
        </span>
    );
}

function PositionButton({ label, onClick, currentPts, projectedPts, overLimit, replacingName }: {
    label: string;
    onClick: () => void;
    currentPts?: number;
    projectedPts?: number;
    overLimit?: boolean;
    /** When set, this pick replaces an existing player — shown under the label. */
    replacingName?: string | null;
}) {
    return (
        <button
            type="button"
            onClick={onClick}
            className="flex flex-col items-center justify-between gap-0.5 px-3 py-2 rounded-lg text-[12px] font-bold
                bg-(--background-secondary) border border-(--divider)
                text-(--text-primary) hover:border-(--secondary) hover:text-(--secondary)
                transition-colors"
        >
            {label}
            {replacingName && (
                <span className="text-[9px] font-semibold text-(--text-tertiary) normal-case">
                    Replaces {replacingName}
                </span>
            )}
            {currentPts != null && projectedPts != null && (
                <span className={`text-[10px] font-semibold tabular-nums ${overLimit ? 'text-red-500' : 'text-(--text-tertiary)'}`}>
                    {currentPts} → {projectedPts}
                </span>
            )}
        </button>
    );
}
