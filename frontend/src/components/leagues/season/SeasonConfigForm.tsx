import { useState } from 'react';
import { FaFloppyDisk, FaSpinner } from 'react-icons/fa6';
import FormDropdown from '../../customs/FormDropdown';
import NumberInput from '../../customs/NumberInput';
import { DEFAULT_SEASON_CONFIG, updateSeasonConfig, type SeasonConfig } from '../../../api/leagues';
import { ERROR_BOX_CLASS, PRIMARY_BUTTON_CLASS, SECTION_LABEL_CLASS, errorMessage } from '../leagueUi';

/** Rounds each bracket size plays - mirrors `BracketConfig.round_count` on the server. */
const ROUNDS_FOR_TEAMS: Record<number, number> = { 0: 0, 2: 1, 4: 2, 6: 3, 8: 3 };
const SERIES_LENGTH_OPTIONS = [1, 3, 5, 7, 9].map(n => ({ value: String(n), label: n === 1 ? 'One game' : `Best of ${n}` }));

/** Round names counted back from the final. */
function roundName(index: number, roundCount: number): string {
    const fromFinal = roundCount - 1 - index;
    return ['Final', 'Semifinals', 'Quarterfinals'][fromFinal] ?? `Round ${index + 1}`;
}

/** Default series lengths for a bracket size: shortest first, a best-of-7 final. */
function defaultLengths(roundCount: number): number[] {
    return [3, 5, 7].slice(3 - roundCount);
}

type Props = {
    token: string;
    leagueId: string;
    seasonNumber: number;
    initial: Partial<SeasonConfig>;
    teamCount: number;
    canEdit: boolean;
    onSaved: () => void;
};

/** Schedule length and postseason bracket for a season. Read-only unless `canEdit`. */
export function SeasonConfigForm({ token, leagueId, seasonNumber, initial, teamCount, canEdit, onSaved }: Props) {
    const [config, setConfig] = useState<SeasonConfig>({
        games_per_team: initial.games_per_team ?? DEFAULT_SEASON_CONFIG.games_per_team,
        postseason: initial.postseason ?? (teamCount >= 4 ? DEFAULT_SEASON_CONFIG.postseason : { teams: 2, series_lengths: [7] }),
    });
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const bracketSizes = Object.keys(ROUNDS_FOR_TEAMS).map(Number).filter(n => n <= teamCount);
    const roundCount = ROUNDS_FOR_TEAMS[config.postseason.teams] ?? 0;

    function setTeams(teams: number) {
        setConfig(prev => ({ ...prev, postseason: { teams, series_lengths: defaultLengths(ROUNDS_FOR_TEAMS[teams]) } }));
        setSaved(false);
    }

    function setLength(roundIndex: number, length: number) {
        setConfig(prev => ({
            ...prev,
            postseason: { ...prev.postseason, series_lengths: prev.postseason.series_lengths.map((l, i) => (i === roundIndex ? length : l)) },
        }));
        setSaved(false);
    }

    async function save() {
        setSaving(true);
        setError(null);
        try {
            await updateSeasonConfig(token, leagueId, seasonNumber, config);
            setSaved(true);
            onSaved();
        } catch (err) {
            setError(errorMessage(err));
        } finally {
            setSaving(false);
        }
    }

    return (
        <section className="flex flex-col gap-3">
            <div className={SECTION_LABEL_CLASS}>Schedule & postseason</div>
            <fieldset disabled={!canEdit} className="grid grid-cols-1 sm:grid-cols-2 gap-3 disabled:opacity-80">
                <NumberInput
                    label="Games per team"
                    value={config.games_per_team}
                    onChange={v => { setConfig(prev => ({ ...prev, games_per_team: Math.max(2, Math.min(162, v)) })); setSaved(false); }}
                />
                <FormDropdown
                    label="Postseason teams"
                    selectedOption={String(config.postseason.teams)}
                    options={bracketSizes.map(n => ({ value: String(n), label: n === 0 ? 'No postseason' : n === 6 ? '6 teams (top 2 get a bye)' : `${n} teams` }))}
                    onChange={v => setTeams(Number(v))}
                    disabled={!canEdit}
                />
                {Array.from({ length: roundCount }, (_, i) => (
                    <FormDropdown
                        key={i}
                        label={roundName(i, roundCount)}
                        selectedOption={String(config.postseason.series_lengths[i] ?? 7)}
                        options={SERIES_LENGTH_OPTIONS}
                        onChange={v => setLength(i, Number(v))}
                        disabled={!canEdit}
                    />
                ))}
            </fieldset>
            <p className="text-[11px] text-(--text-tertiary)">
                Every team plays a balanced round robin of 3-game series. The best records make the postseason; ties go to run differential.
            </p>
            {error && <div className={ERROR_BOX_CLASS}>{error}</div>}
            {canEdit && (
                <div>
                    <button type="button" onClick={save} disabled={saving} className={PRIMARY_BUTTON_CLASS}>
                        {saving ? <FaSpinner className="animate-spin" /> : <FaFloppyDisk />}
                        {saved ? 'Saved' : 'Save settings'}
                    </button>
                </div>
            )}
        </section>
    );
}
