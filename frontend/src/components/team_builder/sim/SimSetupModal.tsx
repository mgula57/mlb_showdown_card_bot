import { useEffect, useState } from 'react';
import { FaSpinner, FaPlay } from 'react-icons/fa6';
import { Modal } from '../../shared/Modal';
import FormDropdown from '../../customs/FormDropdown';
import ManagerStyleFields from '../../simulate/ManagerStyleFields';
import { NEUTRAL_MANAGER, managerPayload, type ManagerPreference } from '../../../api/manager';
import { fetchSimSeasons, fetchSimSeasonTeams, SimAlreadyRunningError, type TakeoverClub } from '../../../api/sim';

function errorMessage(err: unknown): string {
    return err instanceof Error ? err.message : String(err);
}

type Props = {
    /** Set the team was built in — the sim runs with the same card set. */
    showdownSet: string;
    onCancel: () => void;
    onStart: (options: { year: number; set: string; replaces: string; manager?: ManagerPreference }) => Promise<void>;
    /** Jump straight to the user's already-running job — shown when `onStart` is blocked by
     *  `SimAlreadyRunningError`. Its team may differ from this one, since the cap is per-user. */
    onViewExisting: (jobId: string, teamId: string | null) => void;
};

/**
 * Picks the season and the real club the team takes over. The club list is ordered worst
 * record first and defaults to the worst — taking over a last-place team is the intended
 * uphill version of the game.
 */
export function SimSetupModal({ showdownSet, onCancel, onStart, onViewExisting }: Props) {
    const [seasons, setSeasons] = useState<number[]>([]);
    const [year, setYear] = useState<number | null>(null);
    // Clubs are stored with the year they belong to, so "still loading" is derived from a
    // mismatch rather than tracked as its own state.
    const [clubsFor, setClubsFor] = useState<{ year: number; teams: TakeoverClub[] } | null>(null);
    const [replaces, setReplaces] = useState<string>('');
    const [manager, setManager] = useState<ManagerPreference>(NEUTRAL_MANAGER);
    const [starting, setStarting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [runningJob, setRunningJob] = useState<{ jobId: string; teamId: string | null } | null>(null);

    useEffect(() => {
        fetchSimSeasons()
            .then(list => {
                setSeasons(list);
                // Default to the most recent completed season rather than the current one,
                // which may only be partway played.
                setYear(list[1] ?? list[0] ?? null);
            })
            .catch(err => setError(errorMessage(err)));
    }, []);

    useEffect(() => {
        if (year === null) return;
        let stale = false;
        fetchSimSeasonTeams(year)
            .then(({ teams, default: worst }) => {
                if (stale) return;
                setClubsFor({ year, teams });
                setReplaces(worst ?? teams[0]?.abbreviation ?? '');
            })
            .catch(err => { if (!stale) setError(errorMessage(err)); });
        return () => { stale = true; };
    }, [year]);

    const clubs = clubsFor?.year === year ? clubsFor.teams : [];
    const loadingClubs = year !== null && clubsFor?.year !== year;

    async function handleStart() {
        if (year === null || !replaces) return;
        setStarting(true);
        setError(null);
        setRunningJob(null);
        try {
            await onStart({ year, set: showdownSet, replaces, manager: managerPayload(manager) });
        } catch (err: unknown) {
            if (err instanceof SimAlreadyRunningError) setRunningJob({ jobId: err.jobId, teamId: err.teamId });
            setError(errorMessage(err));
            setStarting(false);
        }
    }

    const selectedClub = clubs.find(club => club.abbreviation === replaces);

    return (
        <Modal title="Simulate a Season" size="md" onClose={onCancel}>
            <div className="flex flex-col gap-4 p-4">
                <p className="text-[13px] text-(--text-secondary)">
                    Your team takes over a real club's schedule, division, and opponents for a full
                    season — then plays through the postseason.
                </p>

                <FormDropdown
                    label="Season"
                    options={seasons.map(season => ({ label: String(season), value: String(season) }))}
                    selectedOption={year === null ? '' : String(year)}
                    onChange={value => setYear(Number(value))}
                    placeholder="Select a season"
                />

                <FormDropdown
                    label="Replace"
                    options={clubs.map(club => ({
                        label: `${club.name} (${club.wins}-${club.losses})`,
                        value: club.abbreviation,
                    }))}
                    selectedOption={replaces}
                    onChange={setReplaces}
                    disabled={loadingClubs || clubs.length === 0}
                    placeholder={loadingClubs ? 'Loading teams…' : 'Select a team'}
                />

                {selectedClub && (
                    <p className="text-[12px] text-(--text-tertiary)">
                        The real {selectedClub.name} went {selectedClub.wins}-{selectedClub.losses}
                        {selectedClub.division ? ` in the ${selectedClub.division}` : ''}.
                    </p>
                )}

                <ManagerStyleFields value={manager} onChange={setManager} />

                {error && (
                    <div className="flex items-center justify-between gap-2 text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                        <span>{error}</span>
                        {runningJob && (
                            <button
                                type="button"
                                onClick={() => onViewExisting(runningJob.jobId, runningJob.teamId)}
                                className="shrink-0 font-semibold underline underline-offset-2 hover:opacity-80 transition-opacity cursor-pointer"
                            >
                                View it
                            </button>
                        )}
                    </div>
                )}

                <div className="flex justify-end gap-2 pt-1">
                    <button
                        type="button"
                        onClick={onCancel}
                        className="px-3 py-2 rounded-lg text-[12px] font-semibold text-(--text-secondary) hover:text-(--text-primary) transition-colors cursor-pointer"
                    >
                        Cancel
                    </button>
                    <button
                        type="button"
                        onClick={handleStart}
                        disabled={starting || loadingClubs || year === null || !replaces}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-(--secondary) text-[12px] font-bold text-(--background-primary) hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        {starting ? <FaSpinner className="animate-spin text-[10px]" /> : <FaPlay className="text-[10px]" />}
                        Play Season
                    </button>
                </div>
            </div>
        </Modal>
    );
}
