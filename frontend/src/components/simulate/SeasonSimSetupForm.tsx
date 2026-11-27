import { useEffect, useRef, useState } from 'react';
import { FaSpinner, FaPlay, FaUserGroup } from 'react-icons/fa6';
import FormDropdown from '../customs/FormDropdown';
import ManagerStyleFields from './ManagerStyleFields';
import SimSettingToggle from './SimSettingToggle';
import FreeAgentSigningsFields, { type FreeAgentSigning } from './FreeAgentSigningsFields';
import { NEUTRAL_MANAGER, managerPayload, type ManagerPreference } from '../../api/manager';
import { useSiteSettings } from '../shared/SiteSettingsContext';
import { SET_SELECT_OPTIONS } from '../shared/SetBadge';
import { BetaBadge } from '../shared/BetaBadge';
import { fetchUserTeams, type TeamSummary } from '../../api/userTeams';
import {
    fetchSimSeasonList, fetchSimSeasonTeams, fetchSimFreeAgents, fetchSimJob, rerunPresetFromJob, SimAlreadyRunningError,
    type SimFreeAgent, type TakeoverClub, type OpenSimPayload, type CreateSimLobbyPayload, type OpenSimRerunPreset,
} from '../../api/sim';

import { Heading } from '../shared/Heading';
import { Eyebrow } from '../shared/Eyebrow';
import { buttonClass } from '../shared/buttonStyles';
import { PageSubtitle } from '../shared/PageSubtitle';
/** Exact text of the backend's global-capacity 429 (`sim.py`'s `_sim_slots` semaphore) — every
 *  worker process only runs so many sims at once, shared across all users, so this isn't a real
 *  error so much as a "someone else is using it, try again shortly" — shown as a lighter warning
 *  rather than the red error banner. */
const SIM_BUSY_MESSAGE = 'The simulator is busy right now. Try again in a minute.';

function errorMessage(err: unknown): string {
    return err instanceof Error ? err.message : String(err);
}

// Bot-generated cards are pinned to one baseline set (WOTC's freely-combinable sets don't apply
// here), so the picker is just `SET_SELECT_OPTIONS` filtered to the ones the bot actually renders —
// reusing the shared list gives the dropdown its set badges for free.
const BOT_SET_VALUES = new Set(['2000', '2001', 'CLASSIC', '2002', '2003', '2004', '2005', 'EXPANDED']);
const CARD_SET_OPTIONS = SET_SELECT_OPTIONS.filter(option => BOT_SET_VALUES.has(option.value));

/** Engine settings that represent a standing user preference (independent of season/team/manager),
 *  persisted so a repeat "Simulate a season" starts from how they last configured it. */
const SIM_SETTINGS_STORAGE_KEY = 'simSetup.engineSettings';

type PersistedSimSettings = {
    set?: string;
    enableInjuries?: boolean;
    simulatePostseason?: boolean;
    postseasonFormat?: string;
    tradeDeadlineEnabled?: boolean;
    tradeDeadlineRespectsStandings?: boolean;
    regressSmallSampleStats?: boolean;
    enablePlatoonEffect?: boolean;
};

function loadPersistedSimSettings(): PersistedSimSettings {
    if (typeof window === 'undefined') return {};
    try {
        const raw = window.localStorage.getItem(SIM_SETTINGS_STORAGE_KEY);
        return raw ? JSON.parse(raw) as PersistedSimSettings : {};
    } catch {
        return {};
    }
}

function savePersistedSimSettings(settings: PersistedSimSettings) {
    if (typeof window === 'undefined') return;
    try {
        window.localStorage.setItem(SIM_SETTINGS_STORAGE_KEY, JSON.stringify(settings));
    } catch {
        // Ignore quota/availability errors — settings just won't be remembered this time.
    }
}

const POSTSEASON_FORMAT_OPTIONS = [
    { value: 'DYNAMIC', label: 'Era-accurate (default)' },
    { value: 'WC1', label: 'Wild Card + Division/Championship/World Series (1995–2011)' },
    { value: 'WC2', label: '2012–2021 Wild Card format' },
    { value: 'WC3', label: '2022+ Wild Card format' },
    { value: 'LCS', label: 'Pre-Wild-Card (Division/Championship/World Series only)' },
    { value: 'WS', label: 'World Series only' },
];

type Props =
    | {
          mode: 'solo';
          token?: string;
          onStart: (payload: OpenSimPayload) => Promise<void>;
          /** Jump straight to the user's already-running job — shown when `onStart` is blocked by
           *  `SimAlreadyRunningError`. */
          onViewExisting: (jobId: string, teamId: string | null) => void;
          /** Pre-selects the season, e.g. from the Seasons page's "Simulate this season" link.
           *  Falls back to the usual default (most recent completed season) if unset or not
           *  simulatable. */
          initialYear?: number;
          /** Franchise abbreviations the user has starred — sorted to the top of the Follow /
           *  Replaces club pickers. */
          starredAbbrs?: string[];
          /** "Run again": a finished sim whose setup (season, settings, takeover, free agent
           *  signings) the form starts from instead of its defaults. */
          rerunJobId?: string;
      }
    | {
          mode: 'lobby';
          token?: string;
          /** Creates the lobby with these engine settings; who follows/takes over which club is
           *  decided later by member claims, so there's no focus club or takeover here. */
          onCreateLobby: (payload: CreateSimLobbyPayload) => Promise<void>;
          initialYear?: number;
      };

/**
 * Settings form for an open sim: pick a season, tune the engine, and — solo only — a club to
 * focus the result on or take over with a built team. Shared between starting a solo run and
 * creating a multiplayer lobby (`mode`), since the engine settings are identical either way; a
 * lobby's per-member follow/takeover choices are made later, inside the lobby room. Every setting
 * here maps directly onto `SeasonSimulationConfig` on the backend.
 */
export function SeasonSimSetupForm(props: Props) {
    const { token, initialYear } = props;
    const isLobby = props.mode === 'lobby';
    const { userShowdownSet } = useSiteSettings();

    const [seasons, setSeasons] = useState<number[]>([]);
    const [unfinishedSeasons, setUnfinishedSeasons] = useState<number[]>([]);
    const [year, setYear] = useState<number | null>(null);
    const [set, setSet] = useState(() => loadPersistedSimSettings().set || userShowdownSet || '2000');
    const [clubsFor, setClubsFor] = useState<{ year: number; teams: TakeoverClub[] } | null>(null);
    const [focusAbbr, setFocusAbbr] = useState<string>('');

    const [takeoverEnabled, setTakeoverEnabled] = useState(false);
    const [userTeams, setUserTeams] = useState<TeamSummary[] | null>(null);
    const [takeoverTeamId, setTakeoverTeamId] = useState<string>('');
    const [takeoverReplaces, setTakeoverReplaces] = useState<string>('');
    const [manager, setManager] = useState<ManagerPreference>(NEUTRAL_MANAGER);

    const [enableInjuries, setEnableInjuries] = useState(() => loadPersistedSimSettings().enableInjuries ?? true);
    const [simulatePostseason, setSimulatePostseason] = useState(() => loadPersistedSimSettings().simulatePostseason ?? true);
    const [postseasonFormat, setPostseasonFormat] = useState(() => loadPersistedSimSettings().postseasonFormat ?? 'DYNAMIC');
    const [resumeEnabled, setResumeEnabled] = useState(false);
    const [mergeRealStats, setMergeRealStats] = useState(false);
    const [resumePostseasonEnabled, setResumePostseasonEnabled] = useState(false);
    const [tradeDeadlineEnabled, setTradeDeadlineEnabled] = useState(() => loadPersistedSimSettings().tradeDeadlineEnabled ?? true);
    const [tradeDeadlineRespectsStandings, setTradeDeadlineRespectsStandings] = useState(() => loadPersistedSimSettings().tradeDeadlineRespectsStandings ?? true);
    const [regressSmallSampleStats, setRegressSmallSampleStats] = useState(() => loadPersistedSimSettings().regressSmallSampleStats ?? false);
    const [enablePlatoonEffect, setEnablePlatoonEffect] = useState(() => loadPersistedSimSettings().enablePlatoonEffect ?? false);

    // OFFSEASON FREE AGENTS (SOLO ONLY). Per-run like the takeover: who's unsigned changes daily.
    const [freeAgentsFor, setFreeAgentsFor] = useState<{ year: number; set: string; list: SimFreeAgent[] } | null>(null);
    const [returnFreeAgents, setReturnFreeAgents] = useState(false);
    const [signFreeAgentsEnabled, setSignFreeAgentsEnabled] = useState(false);
    const [freeAgentSignings, setFreeAgentSignings] = useState<FreeAgentSigning[]>([]);

    // Remember these as a standing preference for next time — season/club/takeover selections stay
    // per-run since they're tied to context that won't carry over (a different season's clubs, a
    // manager profile scoped to "never saved to the team").
    useEffect(() => {
        savePersistedSimSettings({
            set, enableInjuries, simulatePostseason, postseasonFormat,
            tradeDeadlineEnabled, tradeDeadlineRespectsStandings,
            regressSmallSampleStats, enablePlatoonEffect,
        });
    }, [set, enableInjuries, simulatePostseason, postseasonFormat, tradeDeadlineEnabled, tradeDeadlineRespectsStandings, regressSmallSampleStats, enablePlatoonEffect]);

    const [starting, setStarting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    /** Set instead of `error` when the backend's global sim-capacity 429 is hit — every worker is
     *  already running one, unrelated to this account. Shown as a lighter warning since it's not
     *  really a failure, just "wait a bit." */
    const [busy, setBusy] = useState(false);
    const [runningJob, setRunningJob] = useState<{ jobId: string; teamId: string | null } | null>(null);

    // "Run again" preset. Settings apply as soon as it loads; the clubs and free agent signings
    // wait for the season's club / free agent effects below, which would otherwise reset them to
    // their defaults. Each part is consumed once, so changing seasons afterward behaves normally.
    const rerunJobId = props.mode === 'solo' ? props.rerunJobId : undefined;
    const presetRef = useRef<{ preset: OpenSimRerunPreset; clubsPending: boolean; freeAgentsPending: boolean } | null>(null);

    function applyPresetSettings(preset: OpenSimRerunPreset) {
        if (preset.set) setSet(preset.set);
        if (preset.enableInjuries !== undefined) setEnableInjuries(preset.enableInjuries);
        if (preset.simulatePostseason !== undefined) setSimulatePostseason(preset.simulatePostseason);
        if (preset.postseasonFormat) setPostseasonFormat(preset.postseasonFormat);
        setResumeEnabled(!!preset.resume);
        setMergeRealStats(!!preset.mergeRealStats);
        setResumePostseasonEnabled(!!preset.resumeFromRealPostseason);
        if (preset.tradeDeadlineEnabled !== undefined) setTradeDeadlineEnabled(preset.tradeDeadlineEnabled);
        if (preset.tradeDeadlineRespectsStandings !== undefined) setTradeDeadlineRespectsStandings(preset.tradeDeadlineRespectsStandings);
        if (preset.regressSmallSampleStats !== undefined) setRegressSmallSampleStats(preset.regressSmallSampleStats);
        if (preset.enablePlatoonEffect !== undefined) setEnablePlatoonEffect(preset.enablePlatoonEffect);
        setTakeoverEnabled(!!preset.takeover);
        setTakeoverTeamId(preset.takeover?.teamId ?? '');
        setManager(preset.takeover?.manager ?? NEUTRAL_MANAGER);
    }

    useEffect(() => {
        // A preset that fails to load just leaves the form on its defaults
        const presetRequest = rerunJobId && token
            ? fetchSimJob(rerunJobId, token).then(rerunPresetFromJob).catch(() => null)
            : Promise.resolve(null);
        Promise.all([fetchSimSeasonList(), presetRequest])
            .then(([{ seasons: list, unfinished }, preset]) => {
                setSeasons(list);
                setUnfinishedSeasons(unfinished);
                const presetYear = preset?.year !== undefined && list.includes(preset.year) ? preset.year : undefined;
                if (preset && presetYear !== undefined && !presetRef.current) {
                    presetRef.current = { preset, clubsPending: true, freeAgentsPending: true };
                    applyPresetSettings(preset);
                }
                setYear(
                    presetYear
                        ?? (initialYear !== undefined && list.includes(initialYear) ? initialYear : undefined)
                        // Default to the most recent completed season rather than the current
                        // one, which may only be partway played.
                        ?? list[1] ?? list[0] ?? null,
                );
            })
            .catch(err => setError(errorMessage(err)));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Latest starred abbreviations, read (not depended on) inside the club fetch so a starred-list
    // update never clobbers a club the user has already picked.
    const starredAbbrsRef = useRef<string[]>([]);

    useEffect(() => {
        // The focus/takeover club pickers this feeds don't exist in lobby mode, so skip the fetch.
        if (year === null || isLobby) return;
        let stale = false;
        fetchSimSeasonTeams(year)
            .then(({ teams, default: worst }) => {
                if (stale) return;
                setClubsFor({ year, teams });
                // "Follow" defaults to the user's starred club if one played this season, else the
                // best record. "Replaces" stays on the worst club — that's the club worth taking over.
                // A rerun keeps the last run's clubs instead.
                const pending = presetRef.current?.clubsPending && presetRef.current.preset.year === year ? presetRef.current.preset : null;
                if (pending && presetRef.current) presetRef.current.clubsPending = false;
                const isClub = (abbr?: string) => !!abbr && teams.some(club => club.abbreviation === abbr);
                // Teams arrive worst first (pre-Opening Day: by last season's record), so reversing
                // before the stable sort keeps last year's best club on top when everyone is 0-0.
                const byRecord = [...teams].reverse().sort((a, b) => b.wins - a.wins);
                const starredPick = byRecord.find(club => starredAbbrsRef.current.includes(club.abbreviation));
                setFocusAbbr(isClub(pending?.focusAbbr) ? pending!.focusAbbr! : starredPick?.abbreviation ?? byRecord[0]?.abbreviation ?? '');
                setTakeoverReplaces(isClub(pending?.takeover?.replaces) ? pending!.takeover!.replaces! : worst ?? teams[0]?.abbreviation ?? '');
            })
            .catch(err => { if (!stale) setError(errorMessage(err)); });
        return () => { stale = true; };
    }, [year, isLobby]);

    // "Resume from real standings" only makes sense for the current in-progress season - "Resume
    // from the real postseason" works for any year, including a long-finished one (real results
    // played "so far" is then simply the whole bracket, and nothing gets simulated).
    useEffect(() => {
        if (year !== 2026) setResumeEnabled(false);
    }, [year]);

    // Resuming from the real postseason needs a finished regular season to seed from.
    const canResumePostseason = year !== null && !unfinishedSeasons.includes(year);
    useEffect(() => {
        if (!canResumePostseason) setResumePostseasonEnabled(false);
    }, [canResumePostseason]);

    // Only a season before Opening Day has unsigned free agents to place - the endpoint returns an
    // empty list for every other one, which hides the options below. Placements are tied to the
    // season, so a new one starts clean.
    useEffect(() => {
        const pending = presetRef.current?.freeAgentsPending && presetRef.current.preset.year === year ? presetRef.current.preset : null;
        if (pending && presetRef.current) presetRef.current.freeAgentsPending = false;
        const signings = pending?.freeAgentSignings ?? [];
        setReturnFreeAgents(!!pending?.returnFreeAgents);
        setSignFreeAgentsEnabled(signings.length > 0);
        setFreeAgentSignings(signings);
    }, [year]);

    useEffect(() => {
        if (year === null || isLobby) return;
        let stale = false;
        fetchSimFreeAgents(year, set)
            .then(list => { if (!stale) setFreeAgentsFor({ year, set, list }); })
            // Free agent options are an extra - a failed lookup just leaves them hidden.
            .catch(() => { if (!stale) setFreeAgentsFor({ year, set, list: [] }); });
        return () => { stale = true; };
    }, [year, set, isLobby]);

    useEffect(() => {
        if (!takeoverEnabled || !token || userTeams !== null) return;
        fetchUserTeams(token)
            .then(teams => {
                const active = teams.filter(t => !t.is_archived);
                setUserTeams(active);
                // A rerun from before takeovers stored their team id: match the team by name
                const presetTeamName = presetRef.current?.preset.takeover?.teamName;
                if (presetTeamName) setTakeoverTeamId(prev => prev || (active.find(t => t.name === presetTeamName)?.team_id ?? ''));
            })
            .catch(err => setError(errorMessage(err)));
    }, [takeoverEnabled, token, userTeams]);

    const clubs = !isLobby && clubsFor?.year === year ? clubsFor.teams : [];
    const loadingClubs = !isLobby && year !== null && clubsFor?.year !== year;

    // Club pickers ("Follow" / "Replaces") list the user's starred franchises first, then the rest
    // by record, best to worst.
    const starredAbbrs = props.mode === 'solo' ? props.starredAbbrs ?? [] : [];
    starredAbbrsRef.current = starredAbbrs;
    const sortedClubs = [...clubs].sort((a, b) => {
        const aStarred = starredAbbrs.includes(a.abbreviation);
        const bStarred = starredAbbrs.includes(b.abbreviation);
        if (aStarred !== bStarred) return aStarred ? -1 : 1;
        return b.wins - a.wins || a.name.localeCompare(b.name);
    });
    // Before Opening Day every club is 0-0, so the label drops the record.
    const clubLabel = (club: TakeoverClub) => club.wins + club.losses > 0 ? `${club.name} (${club.wins}-${club.losses})` : club.name;

    // While another set's list loads, keep showing the same season's last one so the options don't
    // flicker away.
    const freeAgents = freeAgentsFor?.year === year ? freeAgentsFor.list : [];
    const showFreeAgentOptions = !isLobby && freeAgents.length > 0;
    // A signing whose player has no card in the chosen set can't play, so it's left out.
    const freeAgentIds = new Set(freeAgents.map(freeAgent => freeAgent.mlb_id));
    const activeSignings = showFreeAgentOptions && signFreeAgentsEnabled
        ? freeAgentSignings.filter(signing => freeAgentIds.has(signing.mlb_id))
        : [];
    // A taken-over club plays the user's own roster, so nobody can sign there.
    const signingClubs = takeoverEnabled ? sortedClubs.filter(club => club.abbreviation !== takeoverReplaces) : sortedClubs;

    async function handleSubmit() {
        if (year === null) return;
        if (!isLobby && takeoverEnabled && !takeoverTeamId) {
            setError('Pick a team to take over with, or turn off the takeover option.');
            return;
        }
        if (takeoverEnabled && activeSignings.some(signing => signing.team === takeoverReplaces)) {
            setError(`A free agent is signing with ${takeoverReplaces}, the club you're taking over. Move or remove that signing first.`);
            return;
        }
        setStarting(true);
        setError(null);
        setBusy(false);
        setRunningJob(null);
        try {
            const engineSettings = {
                year, set,
                seed: undefined,
                games_limit: undefined,
                enable_injuries: enableInjuries,
                // Injury severity isn't user-configurable for now — the backend defaults to 1.0 (realistic).
                injury_severity_multiplier: undefined,
                simulate_postseason: simulatePostseason,
                postseason_format: simulatePostseason ? postseasonFormat : undefined,
                resume_as_of_date: resumeEnabled ? new Date().toISOString().slice(0, 10) : undefined,
                merge_real_stats: resumeEnabled ? mergeRealStats : undefined,
                resume_from_real_postseason: resumePostseasonEnabled || undefined,
                enable_trade_deadline: tradeDeadlineEnabled || undefined,
                trade_deadline_respects_standings: tradeDeadlineEnabled ? tradeDeadlineRespectsStandings : undefined,
                regress_small_sample_stats: regressSmallSampleStats || undefined,
                enable_platoon_effect: enablePlatoonEffect || undefined,
            };
            if (props.mode === 'lobby') {
                await props.onCreateLobby(engineSettings);
            } else {
                await props.onStart({
                    ...engineSettings,
                    focus_abbr: focusAbbr || undefined,
                    takeovers: takeoverEnabled
                        ? [{ team_id: takeoverTeamId, replaces: takeoverReplaces || undefined, manager: managerPayload(manager) }]
                        : undefined,
                    return_free_agents: (showFreeAgentOptions && returnFreeAgents) || undefined,
                    free_agent_signings: activeSignings.length > 0 ? activeSignings : undefined,
                });
            }
        } catch (err: unknown) {
            if (props.mode === 'solo' && err instanceof SimAlreadyRunningError) setRunningJob({ jobId: err.jobId, teamId: err.teamId });
            if (err instanceof Error && err.message === SIM_BUSY_MESSAGE) setBusy(true);
            else setError(errorMessage(err));
            setStarting(false);
        }
    }

    return (
        <div className="flex flex-col gap-4 max-w-2xl mx-auto w-full p-4">
            <div>
                <Heading level="page" className="flex items-center gap-2">
                    {isLobby ? 'Create a Lobby' : 'Simulate a Season'}
                    <BetaBadge />
                </Heading>
                <PageSubtitle className="mt-1">
                    {isLobby
                        ? "Set the season and rules — once everyone's joined, each person picks a club to follow or take over."
                        : "Every club plays out a full season — pick one to follow, or take it over with a team you've built."}
                </PageSubtitle>
            </div>

            <div className={`grid grid-cols-1 gap-3 ${isLobby ? 'sm:grid-cols-2' : 'sm:grid-cols-3'}`}>
                <FormDropdown
                    label="Season"
                    options={seasons.map(season => ({ label: String(season), value: String(season) }))}
                    selectedOption={year === null ? '' : String(year)}
                    onChange={value => setYear(Number(value))}
                    placeholder="Select a season"
                />
                {!isLobby && (
                    <FormDropdown
                        label="Follow"
                        options={sortedClubs.map(club => ({ label: clubLabel(club), value: club.abbreviation }))}
                        selectedOption={focusAbbr}
                        onChange={setFocusAbbr}
                        disabled={loadingClubs || clubs.length === 0}
                        placeholder={loadingClubs ? 'Loading teams…' : 'Select a team'}
                    />
                )}
                <FormDropdown
                    label="Card Set"
                    options={CARD_SET_OPTIONS}
                    selectedOption={set}
                    onChange={setSet}
                />
            </div>

            {/* Offseason-only moves, set apart from the engine settings since they only exist before
                Opening Day and change who plays where, not how the games are played. */}
            {showFreeAgentOptions && year !== null && (
                <section className="flex flex-col gap-3 rounded-card border border-(--divider) p-3">
                    <div className="flex flex-col gap-1">
                        <Eyebrow>{year} Offseason</Eyebrow>
                        <Heading level="panel" as="h2">Hot Stove</Heading>
                        <p className="text-[11px] text-(--text-tertiary)">
                            Clubs play on their current 40-man rosters. Decide where the unsigned free agents land.
                        </p>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <SimSettingToggle
                            label="Return free agents"
                            description={`Every unsigned free agent goes back to the club he played for in ${year - 1}. Players who have already signed stay with their new club.`}
                            isEnabled={returnFreeAgents}
                            onToggle={() => setReturnFreeAgents(v => !v)}
                        />
                        <SimSettingToggle
                            label="Sign free agents"
                            description="Send unsigned free agents to the clubs you choose. A player signed here skips “Return free agents”."
                            isEnabled={signFreeAgentsEnabled}
                            onToggle={() => setSignFreeAgentsEnabled(v => !v)}
                            className={signFreeAgentsEnabled ? 'sm:col-span-2' : ''}
                        >
                            <FreeAgentSigningsFields
                                freeAgents={freeAgents}
                                clubs={signingClubs}
                                value={freeAgentSignings}
                                onChange={setFreeAgentSignings}
                            />
                        </SimSettingToggle>
                    </div>
                </section>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <SimSettingToggle
                    label="Injuries"
                    description="Players on each club's 40-man can hit the IL and get replaced by call-ups, calibrated to how durable each player really was that season. Regular-season games only."
                    isEnabled={enableInjuries}
                    onToggle={() => setEnableInjuries(v => !v)}
                />

                <SimSettingToggle
                    label="Simulate postseason"
                    description="Play out a the playoffs after game 162."
                    isEnabled={simulatePostseason}
                    onToggle={() => setSimulatePostseason(v => !v)}
                >
                    <FormDropdown
                        label="Postseason format"
                        options={POSTSEASON_FORMAT_OPTIONS}
                        selectedOption={postseasonFormat}
                        onChange={setPostseasonFormat}
                    />
                </SimSettingToggle>

                <SimSettingToggle
                    label="Trade deadline"
                    description="A player who was really traded mid-season starts on his first club and moves to his next one on that era's deadline date, instead of playing the whole season for one club."
                    isEnabled={tradeDeadlineEnabled}
                    onToggle={() => setTradeDeadlineEnabled(v => !v)}
                >
                    <SimSettingToggle
                        label="Contending clubs keep their players"
                        description="If the sim has a selling club still in the race at the deadline, it holds onto its player and the real trade is skipped for this run."
                        isEnabled={tradeDeadlineRespectsStandings}
                        onToggle={() => setTradeDeadlineRespectsStandings(v => !v)}
                    />
                </SimSettingToggle>

                {!isLobby && (
                    <SimSettingToggle
                        label="Take over a club"
                        description="Play the season as one of your built teams, replacing a real club."
                        isEnabled={takeoverEnabled}
                        onToggle={() => setTakeoverEnabled(v => !v)}
                        isDisabled={resumeEnabled || resumePostseasonEnabled}
                        disabledReason={
                            resumePostseasonEnabled
                                ? "Turn off “Resume from the real postseason” first — a takeover club never played the real postseason results it would otherwise inherit."
                                : "Turn off “Resume from real standings” first — a takeover club can't resume from a real record it never had."
                        }
                    >
                        <FormDropdown
                            label="Team"
                            options={(userTeams ?? []).map(team => ({ label: `${team.name} (${team.abbreviation})`, value: team.team_id }))}
                            selectedOption={takeoverTeamId}
                            onChange={setTakeoverTeamId}
                            disabled={userTeams === null}
                            placeholder={userTeams === null ? 'Loading your teams…' : 'Select a team'}
                        />
                        <FormDropdown
                            label="Replaces"
                            options={sortedClubs.map(club => ({ label: clubLabel(club), value: club.abbreviation }))}
                            selectedOption={takeoverReplaces}
                            onChange={setTakeoverReplaces}
                            disabled={loadingClubs || clubs.length === 0}
                            placeholder={loadingClubs ? 'Loading teams…' : 'Select a team'}
                        />
                    </SimSettingToggle>
                )}

                {year === 2026 && (
                    <SimSettingToggle
                        label="Resume from real standings"
                        description="Every club starts from today's real record; today's games are assumed not yet played, so simulation picks up from today onward."
                        isEnabled={resumeEnabled}
                        onToggle={() => setResumeEnabled(v => !v)}
                        isDisabled={takeoverEnabled || resumePostseasonEnabled}
                        disabledReason={
                            resumePostseasonEnabled
                                ? "Turn off “Resume from the real postseason” first — the two can't both project the season."
                                : "Turn off “Take over a club” first — a takeover club can't resume from a real record it never had."
                        }
                    >
                        <SimSettingToggle
                            label="Merge real stats into player lines"
                            description="Each player's real stats to date are added to their simulated totals. These reflect however much of the season has been scraped, which may lag slightly — the result screen shows the actual as-of date."
                            isEnabled={mergeRealStats}
                            onToggle={() => setMergeRealStats(v => !v)}
                        />
                    </SimSettingToggle>
                )}

                {!isLobby && canResumePostseason && (
                    <SimSettingToggle
                        label="Resume from the real postseason"
                        description="Skips the regular season entirely — every club starts from its real final record, skipping straight to the postseason and simming from there. Every player's real season stats are merged in automatically, so MVP/Cy Young/Rookie of the Year/Silver Sluggers still have a full season to be judged on."
                        isEnabled={resumePostseasonEnabled}
                        onToggle={() => setResumePostseasonEnabled(v => !v)}
                        isDisabled={takeoverEnabled || resumeEnabled}
                        disabledReason={
                            takeoverEnabled
                                ? "Turn off “Take over a club” first — a takeover club never played the real postseason results it would otherwise inherit."
                                : "Turn off “Resume from real standings” first — the two can't both project the season."
                        }
                    />
                )}

                <SimSettingToggle
                    label="Regress small sample sizes towards replacement level"
                    description="A thin sample (a September callup, a spot starter) gets its rate stats pulled toward that year's replacement level before rosters are built, so a hot small sample can't outvalue a proven regular's full season on noise. Real PA/GS/IP are unaffected."
                    isEnabled={regressSmallSampleStats}
                    onToggle={() => setRegressSmallSampleStats(v => !v)}
                />

                <SimSettingToggle
                    label="Adjust for Handedness"
                    description="Same-handed matchups (RHP vs RHB, LHP vs LHB) nudge the pitch/swing rolls toward the pitcher; opposite-handed matchups — including every switch hitter — nudge them toward the hitter, roughly matching real career platoon splits."
                    isEnabled={enablePlatoonEffect}
                    onToggle={() => setEnablePlatoonEffect(v => !v)}
                />
            </div>

            {!isLobby && (
                <div className="flex flex-col gap-2 rounded-card border border-form-element bg-secondary p-3">
                    <ManagerStyleFields value={manager} onChange={setManager} />
                </div>
            )}

            <div className="sticky bottom-0 z-10 -mx-4 -mb-4 flex flex-col gap-2 border-t border-(--divider) bg-(--background-primary) px-4 py-3">
                {busy && (
                    <div className="text-[12px] text-(--gold) px-3 py-2 rounded-card border border-(--gold)/30 bg-(--gold)/5">
                        The simulator is busy running other seasons right now — wait about a minute and try again.
                    </div>
                )}
                {error && (
                    <div className="flex items-center justify-between gap-2 text-[12px] text-(--red) px-3 py-2 rounded-card border border-(--red)/30 bg-(--red)/5">
                        <span>{error}</span>
                        {props.mode === 'solo' && runningJob && (
                            <button
                                type="button"
                                onClick={() => props.mode === 'solo' && props.onViewExisting(runningJob.jobId, runningJob.teamId)}
                                className="shrink-0 font-semibold underline underline-offset-2 hover:opacity-80 transition-opacity cursor-pointer"
                            >
                                View it
                            </button>
                        )}
                    </div>
                )}
                <div className="flex justify-end">
                    <button
                        type="button"
                        onClick={handleSubmit}
                        disabled={starting || loadingClubs || year === null}
                        className={buttonClass('feature', 'md')}
                    >
                        {starting ? <FaSpinner className="animate-spin text-[11px]" /> : isLobby ? <FaUserGroup className="text-[11px]" /> : <FaPlay className="text-[11px]" />}
                        {isLobby ? 'Create lobby' : 'Simulate season'}
                    </button>
                </div>
            </div>
        </div>
    );
}
