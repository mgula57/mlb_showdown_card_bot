import { useEffect, useRef, useState } from 'react';
import { FaSpinner, FaPlay, FaUserGroup, FaGears } from 'react-icons/fa6';
import FormDropdown from '../customs/FormDropdown';
import FormInput from '../customs/FormInput';
import FormSection from '../customs/FormSection';
import FormEnabler from '../customs/FormEnabler';
import ManagerStyleFields from './ManagerStyleFields';
import { NEUTRAL_MANAGER, managerPayload, type ManagerPreference } from '../../api/manager';
import { setOptionsForSource } from '../../domain/teamSets';
import { CardSource } from '../../types/cardSource';
import { useSiteSettings } from '../shared/SiteSettingsContext';
import { fetchUserTeams, type TeamSummary } from '../../api/userTeams';
import {
    fetchSimSeasons, fetchSimSeasonTeams, SimAlreadyRunningError,
    type TakeoverClub, type OpenSimPayload, type CreateSimLobbyPayload,
} from '../../api/sim';

function errorMessage(err: unknown): string {
    return err instanceof Error ? err.message : String(err);
}

const CARD_SET_OPTIONS = setOptionsForSource(CardSource.BOT).map(set => ({ label: set, value: set }));

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
    const [year, setYear] = useState<number | null>(null);
    const [set, setSet] = useState(userShowdownSet || '2000');
    const [clubsFor, setClubsFor] = useState<{ year: number; teams: TakeoverClub[] } | null>(null);
    const [focusAbbr, setFocusAbbr] = useState<string>('');

    const [takeoverEnabled, setTakeoverEnabled] = useState(false);
    const [userTeams, setUserTeams] = useState<TeamSummary[] | null>(null);
    const [takeoverTeamId, setTakeoverTeamId] = useState<string>('');
    const [takeoverReplaces, setTakeoverReplaces] = useState<string>('');
    const [manager, setManager] = useState<ManagerPreference>(NEUTRAL_MANAGER);

    const [enableInjuries, setEnableInjuries] = useState(true);
    const [simulatePostseason, setSimulatePostseason] = useState(true);
    const [postseasonFormat, setPostseasonFormat] = useState('DYNAMIC');
    const [resumeEnabled, setResumeEnabled] = useState(false);
    const [resumeAsOfDate, setResumeAsOfDate] = useState(() => new Date().toISOString().slice(0, 10));
    const [mergeRealStats, setMergeRealStats] = useState(false);

    const [starting, setStarting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [runningJob, setRunningJob] = useState<{ jobId: string; teamId: string | null } | null>(null);

    useEffect(() => {
        fetchSimSeasons()
            .then(list => {
                setSeasons(list);
                setYear(
                    initialYear !== undefined && list.includes(initialYear)
                        ? initialYear
                        // Default to the most recent completed season rather than the current
                        // one, which may only be partway played.
                        : list[1] ?? list[0] ?? null,
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
                const byRecord = [...teams].sort((a, b) => b.wins - a.wins);
                const starredPick = byRecord.find(club => starredAbbrsRef.current.includes(club.abbreviation));
                setFocusAbbr(starredPick?.abbreviation ?? byRecord[0]?.abbreviation ?? '');
                setTakeoverReplaces(worst ?? teams[0]?.abbreviation ?? '');
            })
            .catch(err => { if (!stale) setError(errorMessage(err)); });
        return () => { stale = true; };
    }, [year, isLobby]);

    useEffect(() => {
        if (!takeoverEnabled || !token || userTeams !== null) return;
        fetchUserTeams(token).then(setUserTeams).catch(err => setError(errorMessage(err)));
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
        return b.wins - a.wins;
    });

    async function handleSubmit() {
        if (year === null) return;
        if (!isLobby && takeoverEnabled && !takeoverTeamId) {
            setError('Pick a team to take over with, or turn off the takeover option.');
            return;
        }
        setStarting(true);
        setError(null);
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
                resume_as_of_date: resumeEnabled ? resumeAsOfDate : undefined,
                merge_real_stats: resumeEnabled ? mergeRealStats : undefined,
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
                });
            }
        } catch (err: unknown) {
            if (props.mode === 'solo' && err instanceof SimAlreadyRunningError) setRunningJob({ jobId: err.jobId, teamId: err.teamId });
            setError(errorMessage(err));
            setStarting(false);
        }
    }

    return (
        <div className="flex flex-col gap-4 max-w-2xl mx-auto w-full p-4">
            <div>
                <h1 className="text-[20px] font-black text-(--text-primary)">
                    {isLobby ? 'Create a Lobby' : 'Simulate a Season'}
                </h1>
                <p className="text-[13px] text-(--text-secondary) mt-1">
                    {isLobby
                        ? "Set the season and rules — once everyone's joined, each person picks a club to follow or take over."
                        : "Every club plays out a full season — pick one to follow, or take it over with a team you've built."}
                </p>
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
                        options={sortedClubs.map(club => ({ label: `${club.name} (${club.wins}-${club.losses})`, value: club.abbreviation }))}
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

            {!isLobby && (
                <FormSection title="Take over a club" icon={<FaUserGroup />}>
                    <FormEnabler
                        label="Take over a club with one of my teams"
                        isEnabled={takeoverEnabled}
                        onChange={value => setTakeoverEnabled(!value)}
                        className="col-span-full"
                    />
                    {takeoverEnabled && (
                        <>
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
                                options={sortedClubs.map(club => ({ label: `${club.name} (${club.wins}-${club.losses})`, value: club.abbreviation }))}
                                selectedOption={takeoverReplaces}
                                onChange={setTakeoverReplaces}
                                disabled={loadingClubs || clubs.length === 0}
                                placeholder={loadingClubs ? 'Loading teams…' : 'Select a team'}
                            />
                            <ManagerStyleFields value={manager} onChange={setManager} className="col-span-full" />
                        </>
                    )}
                </FormSection>
            )}

            <FormSection title="Settings" icon={<FaGears />} isOpenByDefault={true}>
                <FormEnabler
                    label="Resume from real standings"
                    isEnabled={resumeEnabled}
                    onChange={value => setResumeEnabled(!value)}
                    className="col-span-full"
                />
                {resumeEnabled && (
                    <>
                        <FormInput
                            label="As of"
                            type="date"
                            value={resumeAsOfDate}
                            onChange={value => setResumeAsOfDate(value ?? resumeAsOfDate)}
                        />
                        <p className="text-[11px] text-(--text-tertiary) col-span-full">
                            Every club starts from its real record as of this date; only the games
                            after it are simulated.
                        </p>
                        <FormEnabler
                            label="Merge real stats into player lines"
                            isEnabled={mergeRealStats}
                            onChange={value => setMergeRealStats(!value)}
                            className="col-span-full"
                        />
                        {mergeRealStats && (
                            <p className="text-[11px] text-(--text-tertiary) col-span-full">
                                Each player's real stats to date are added to their simulated
                                totals. These reflect however much of the season has been scraped,
                                which may lag the date above slightly — the result screen shows
                                the actual as-of date.
                            </p>
                        )}
                    </>
                )}
                <FormEnabler
                    label="Enable injuries"
                    isEnabled={enableInjuries}
                    onChange={value => setEnableInjuries(!value)}
                    className="col-span-full"
                />
                {enableInjuries && (
                    <p className="text-[11px] text-(--text-tertiary) col-span-full">
                        Players on each club's 40-man can hit the IL and get replaced by call-ups,
                        calibrated to how durable each player really was that season. Only
                        regular-season games roll injuries.
                    </p>
                )}
                <FormEnabler
                    label="Simulate postseason"
                    isEnabled={simulatePostseason}
                    onChange={value => setSimulatePostseason(!value)}
                    className="col-span-full"
                />
                {simulatePostseason && (
                    <FormDropdown
                        label="Postseason format"
                        options={POSTSEASON_FORMAT_OPTIONS}
                        selectedOption={postseasonFormat}
                        onChange={setPostseasonFormat}
                    />
                )}
            </FormSection>

            {error && (
                <div className="flex items-center justify-between gap-2 text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
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

            <div className="sticky bottom-0 z-10 -mx-4 -mb-4 flex justify-end border-t border-form-element backdrop-blur-2xl px-4 py-3">
                <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={starting || loadingClubs || year === null}
                    className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg animated-showdown-gradient text-[13px] font-bold text-white hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                >
                    {starting ? <FaSpinner className="animate-spin text-[11px]" /> : isLobby ? <FaUserGroup className="text-[11px]" /> : <FaPlay className="text-[11px]" />}
                    {isLobby ? 'Create Lobby' : 'Simulate Season'}
                </button>
            </div>
        </div>
    );
}
