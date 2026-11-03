import { useEffect, useMemo, useState } from 'react';
import type { AlgorithmOtherEditionsRule } from '../../api/releases';
import { SEASON_HALF_LABELS, type SeasonHalf } from '../../api/showdownBotCard';
import { fetchTeamHierarchy, type TeamHierarchyRecord } from '../../api/card_db/cardDatabase';
import { showdownSets } from '../shared/SiteSettingsContext';
import { hasVariableSpeedSet } from '../../functions/showdownSets';
import { setSelectOption } from '../shared/SetBadge';
import FormInput from '../customs/FormInput';
import FormEnabler from '../customs/FormEnabler';
import FormDropdown from '../customs/FormDropdown';
import MultiSelect from '../shared/MultiSelect';
import YearsInput from './YearsInput';
import { OutsideScopeNotice } from './ScopeSummary';
import { allShowdownSets } from './algorithmSettings';
import { parseSetSize } from './editionScope';
import { yearsInclude } from './years';
import type { EditionScope, OutsideScopeCounts } from './editionScope';

const showdownSetOptions = showdownSets.map(s => setSelectOption(s.value, { compact: true }));

const OTHER_EDITIONS_OPTIONS: { value: AlgorithmOtherEditionsRule; label: string }[] = [
    { value: 'ALLOW', label: 'Allow' },
    { value: 'NEW_TEAM_ONLY', label: 'Only on a New Team' },
    { value: 'EXCLUDE', label: 'Leave Out' },
];

const FULL_SEASON = 'FULL_SEASON';
const STATS_PERIOD_OPTIONS = [
    { value: FULL_SEASON, label: 'Full Season' },
    ...(Object.entries(SEASON_HALF_LABELS) as [SeasonHalf, string][]).map(([value, label]) => ({ value, label })),
];

const HINT_CLASS = 'text-[11px] text-(--text-tertiary)';

type ScopePanelProps = {
    scope: EditionScope;
    onChange: (patch: Partial<EditionScope>) => void;
    /** Saved cards outside the current scope. They stay in the pool; this only warns. */
    outside: OutsideScopeCounts;
};

/** The settings every way of filling the pool shares: years, showdown sets, set size and who may
 * repeat from other editions. Saves as you edit; the Algorithm run and the Manual search both read it. */
export function ScopePanel({ scope, onChange, outside }: ScopePanelProps) {
    // The years field can hold an incomplete entry ('') that must not be saved over the last valid years
    const [yearsDraft, setYearsDraft] = useState(scope.years);
    const [syncedYears, setSyncedYears] = useState(scope.years);
    if (scope.years !== syncedYears) {
        setSyncedYears(scope.years);
        setYearsDraft(scope.years);
    }

    const [hierarchy, setHierarchy] = useState<TeamHierarchyRecord[]>([]);
    useEffect(() => {
        fetchTeamHierarchy().then(setHierarchy).catch(() => {});
    }, []);
    // Teams that had cards in any of the scope's years, plus any already chosen so they can be removed
    const teamOptions = useMemo(() => {
        const inScope = new Set<string>(scope.teams);
        for (const record of hierarchy) {
            for (let year = record.min_year; year <= record.max_year; year++) {
                if (yearsInclude(scope.years, year)) { inScope.add(record.team); break; }
            }
        }
        return [...inScope].sort().map(team => ({ value: team, label: team }));
    }, [hierarchy, scope.years, scope.teams]);

    const hasPitcherSets = scope.pitcher_showdown_sets !== null;
    const hasSet00_01 = hasVariableSpeedSet(allShowdownSets(scope));

    function changeYears(value: string) {
        setYearsDraft(value);
        if (value === '') return;
        setSyncedYears(value);
        onChange({ years: value });
    }

    return (
        <div className="flex flex-col gap-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4 items-end">
                <YearsInput value={yearsDraft} onChange={changeYears} />
                <div className="flex flex-col gap-1.5">
                    <FormInput
                        label="Set Size"
                        type="number"
                        value={scope.set_size}
                        onChange={value => onChange({ set_size: parseSetSize(value) })}
                    />
                    <p className={HINT_CLASS}>How many cards the Algorithm builds. You can change this later.</p>
                </div>
            </div>

            <div className="flex flex-col gap-2.5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
                    <MultiSelect
                        label={hasPitcherSets ? 'Hitter Sets' : 'Showdown Sets'}
                        options={showdownSetOptions}
                        selections={scope.showdown_sets}
                        onChange={values => onChange({ showdown_sets: values })}
                        placeholder="Select set(s)..."
                    />
                    {scope.pitcher_showdown_sets !== null && (
                        <MultiSelect
                            label="Pitcher Sets"
                            options={showdownSetOptions}
                            selections={scope.pitcher_showdown_sets}
                            onChange={values => onChange({ pitcher_showdown_sets: values })}
                            placeholder="Select set(s)..."
                        />
                    )}
                </div>
                <FormEnabler
                    label="Different Sets for Pitchers"
                    className="self-start"
                    isEnabled={hasPitcherSets}
                    // Starts from the hitters' sets so the scope stays runnable until the user changes it
                    onChange={() => onChange({ pitcher_showdown_sets: hasPitcherSets ? null : [...scope.showdown_sets] })}
                />
                <p className={`${HINT_CLASS} -mt-1`}>Mix sets by player type, like 2000 hitters with 2001 pitchers.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-5 items-start">
                <div className="flex flex-col gap-2.5">
                    <MultiSelect
                        label="Teams"
                        options={teamOptions}
                        selections={scope.teams}
                        onChange={values => onChange({ teams: values })}
                        placeholder="All teams"
                    />
                    <p className={`${HINT_CLASS} -mt-1`}>
                        Limit the edition to players on these teams. The Algorithm, Manual and Customs searches all start from them.
                    </p>
                </div>

                <div className="flex flex-col gap-2.5">
                    <FormDropdown
                        label="Stats Period"
                        options={STATS_PERIOD_OPTIONS}
                        selectedOption={scope.season_half ?? FULL_SEASON}
                        onChange={value => onChange({ season_half: value && value !== FULL_SEASON ? value as SeasonHalf : null })}
                    />
                    <p className={`${HINT_CLASS} -mt-1`}>
                        Build every card from one half of its season, split at the All-Star break. The Algorithm still picks players on their full-season stats, so point totals may shift from your buckets.
                    </p>
                </div>

                <div className="flex flex-col gap-2.5">
                    <FormDropdown
                        label="Players in Other Editions"
                        options={OTHER_EDITIONS_OPTIONS}
                        selectedOption={scope.other_editions_rule}
                        onChange={value => onChange({ other_editions_rule: (value as AlgorithmOtherEditionsRule) || 'ALLOW' })}
                    />
                    <p className={`${HINT_CLASS} -mt-1`}>
                        For expansion editions: leave out players already carded elsewhere in this release, or only bring them back on a new team (like WOTC's Trading Deadline).
                    </p>
                </div>

                {hasSet00_01 && (
                    <div className="flex flex-col gap-2.5">
                        <FormEnabler
                            label="Variable Speed"
                            className="self-start"
                            isEnabled={scope.variable_speed}
                            onChange={() => onChange({ variable_speed: !scope.variable_speed })}
                        />
                        <p className={`${HINT_CLASS} -mt-1`}>
                            2000/2001 cards use exact speed instead of 10/15/20, with points recalculated. The Algorithm picks players on their standard points, so point totals may shift slightly from your buckets.
                        </p>
                    </div>
                )}
            </div>

            <OutsideScopeNotice outside={outside} />
        </div>
    );
}
