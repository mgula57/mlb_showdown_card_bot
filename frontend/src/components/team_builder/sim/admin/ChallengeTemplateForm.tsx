import { useMemo, useState } from 'react';
import FormInput from '../../../customs/FormInput';
import FormDropdown from '../../../customs/FormDropdown';
import FormEnabler from '../../../customs/FormEnabler';
import type { ChallengeCategory, ChallengeGoalType } from '../../../../api/sim';
import type { ChallengeTemplateInput } from '../../../../api/adminChallenges';

const GOAL_OPTIONS: { label: string; value: ChallengeGoalType }[] = [
    { label: 'Make the playoffs', value: 'made_playoffs' },
    { label: 'Win the division', value: 'win_division' },
    { label: 'Win the pennant', value: 'win_pennant' },
    { label: 'Win the World Series', value: 'win_world_series' },
    { label: 'Reach a win total', value: 'min_wins' },
    { label: "Beat a club's record", value: 'beat_team_record' },
];

const CATEGORY_OPTIONS: { label: string; value: ChallengeCategory }[] = [
    { label: 'Legendary', value: 'legendary' },
    { label: 'Budget Cap', value: 'budget_cap' },
    { label: 'Themed', value: 'themed' },
];

const MIN_ROSTER_SIZE = 22;

/** A challenge template as free-text form state — everything is a string here and coerced to
 *  the typed `ChallengeTemplateInput` on submit. */
type FormState = {
    slug: string;
    title: string;
    description: string;
    goal_type: ChallengeGoalType;
    min_wins: string;
    beat_team_abbr: string;
    category: ChallengeCategory;
    pts_limit: string;
    roster_size: string;
    year_pool: string;
    replaces_pool: string;
    player_filters: string;
    active: boolean;
};

function toFormState(initial?: Partial<ChallengeTemplateInput> & { goal_value?: { min_wins?: number; target_abbr?: string } | null }): FormState {
    return {
        slug: initial?.slug ?? '',
        title: initial?.title ?? '',
        description: initial?.description ?? '',
        goal_type: initial?.goal_type ?? 'made_playoffs',
        min_wins: initial?.min_wins != null ? String(initial.min_wins) : (initial?.goal_value?.min_wins != null ? String(initial.goal_value.min_wins) : ''),
        beat_team_abbr: initial?.beat_team_abbr ?? initial?.goal_value?.target_abbr ?? '',
        category: initial?.category ?? 'themed',
        pts_limit: initial?.pts_limit != null ? String(initial.pts_limit) : '',
        roster_size: initial?.roster_size != null ? String(initial.roster_size) : '25',
        year_pool: initial?.year_pool ?? 'any',
        replaces_pool: initial?.replaces_pool ?? 'any',
        player_filters: initial?.player_filters ? JSON.stringify(initial.player_filters, null, 2) : '',
        active: initial?.active ?? true,
    };
}

function validYearPool(value: string): boolean {
    const v = value.trim();
    if (v === 'any') return true;
    if (v.startsWith('random_range:')) {
        const bounds = v.slice('random_range:'.length).split(',');
        return bounds.length === 2 && bounds.every(b => /^\d+$/.test(b.trim()));
    }
    return v.split(',').every(y => /^\d+$/.test(y.trim()));
}

type Props = {
    /** Omit for a create form; pass the current values (including `goal_value`) to edit. */
    initial?: Partial<ChallengeTemplateInput> & { goal_value?: { min_wins?: number; target_abbr?: string } | null };
    submitLabel: string;
    busy?: boolean;
    /** Server-side error from the last submit attempt. */
    error?: string | null;
    onSubmit: (input: ChallengeTemplateInput) => void;
    onCancel: () => void;
};

/** The create/edit form for a Team Challenge template. Deliberately unaware of admin vs. a
 *  future user-submission flow — the caller wires `onSubmit`. */
export function ChallengeTemplateForm({ initial, submitLabel, busy, error, onSubmit, onCancel }: Props) {
    const [form, setForm] = useState<FormState>(() => toFormState(initial));
    const set = <K extends keyof FormState>(key: K, value: FormState[K]) => setForm(f => ({ ...f, [key]: value }));

    const clientError = useMemo(() => {
        if (!form.slug.trim()) return 'Slug is required.';
        if (!form.title.trim()) return 'Title is required.';
        if (form.goal_type === 'min_wins' && !/^\d+$/.test(form.min_wins.trim())) return 'Enter a win total.';
        if (form.goal_type === 'beat_team_record' && !form.beat_team_abbr.trim()) return 'Enter the club abbreviation to beat.';
        const roster = Number(form.roster_size);
        if (!Number.isInteger(roster) || roster < MIN_ROSTER_SIZE) return `Roster size must be at least ${MIN_ROSTER_SIZE}.`;
        if (form.pts_limit.trim() && !/^\d+$/.test(form.pts_limit.trim())) return 'Points cap must be a whole number.';
        if (!validYearPool(form.year_pool)) return "Year pool must be 'any', 'random_range:lo,hi', or a comma list of years.";
        if (form.player_filters.trim()) {
            try {
                const parsed = JSON.parse(form.player_filters);
                if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) return 'Player filters must be a JSON object.';
            } catch {
                return 'Player filters is not valid JSON.';
            }
        }
        return null;
    }, [form]);

    const submit = () => {
        if (clientError) return;
        onSubmit({
            slug: form.slug.trim(),
            title: form.title.trim(),
            description: form.description.trim(),
            goal_type: form.goal_type,
            min_wins: form.goal_type === 'min_wins' ? Number(form.min_wins) : null,
            beat_team_abbr: form.goal_type === 'beat_team_record' ? form.beat_team_abbr.trim().toUpperCase() : null,
            category: form.category,
            pts_limit: form.pts_limit.trim() ? Number(form.pts_limit) : null,
            roster_size: Number(form.roster_size),
            year_pool: form.year_pool.trim(),
            replaces_pool: form.replaces_pool.trim() || 'any',
            player_filters: form.player_filters.trim() ? JSON.parse(form.player_filters) : null,
            active: form.active,
        });
    };

    const fieldLabel = 'text-sm font-medium block text-secondary';

    return (
        <div className="flex flex-col gap-3 p-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <FormInput label="Slug" value={form.slug} onChange={v => set('slug', (v ?? '').toLowerCase().replace(/[^a-z0-9-]/g, ''))} placeholder="small-budget-pennant" />
                <FormInput label="Title" value={form.title} onChange={v => set('title', v ?? '')} placeholder="Cinderella Run" />
            </div>

            <div>
                <label className={fieldLabel}>Description</label>
                <textarea
                    value={form.description}
                    onChange={e => set('description', e.target.value)}
                    rows={2}
                    placeholder="Flavor text shown on the challenge card."
                    className="w-full rounded-lg border border-(--divider) bg-(--background-tertiary) px-3 py-2 text-[13px] text-(--text-primary) resize-y"
                />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <FormDropdown label="Goal" options={GOAL_OPTIONS} selectedOption={form.goal_type} onChange={v => set('goal_type', v as ChallengeGoalType)} />
                <FormDropdown label="Category" options={CATEGORY_OPTIONS} selectedOption={form.category} onChange={v => set('category', v as ChallengeCategory)} />
                {form.goal_type === 'min_wins' && (
                    <FormInput label="Win total" type="number" value={form.min_wins} onChange={v => set('min_wins', v ?? '')} placeholder="90" />
                )}
                {form.goal_type === 'beat_team_record' && (
                    <FormInput label="Club to beat (abbr)" value={form.beat_team_abbr} onChange={v => set('beat_team_abbr', (v ?? '').toUpperCase())} placeholder="NYY" />
                )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <FormInput label="Points cap (blank = none)" type="number" value={form.pts_limit} onChange={v => set('pts_limit', v ?? '')} placeholder="no cap" />
                <FormInput label="Min roster size" type="number" value={form.roster_size} onChange={v => set('roster_size', v ?? '')} step={1} />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                    <FormInput label="Year pool" value={form.year_pool} onChange={v => set('year_pool', v ?? '')} placeholder="any" />
                    <p className="text-[11px] text-(--text-tertiary) mt-1">any · 1998,2001,2004 · random_range:1977,2024</p>
                </div>
                <div>
                    <FormInput label="Replaces pool" value={form.replaces_pool} onChange={v => set('replaces_pool', v ?? '')} placeholder="any" />
                    <p className="text-[11px] text-(--text-tertiary) mt-1">any · worst_record · NYY,BOS,LAD</p>
                </div>
            </div>

            <div>
                <label className={fieldLabel}>Player filters (JSON, optional)</label>
                <textarea
                    value={form.player_filters}
                    onChange={e => set('player_filters', e.target.value)}
                    rows={3}
                    placeholder={'{ "team": ["NYM", "NYY"], "hand": ["L"] }'}
                    className="w-full rounded-lg border border-(--divider) bg-(--background-tertiary) px-3 py-2 font-mono text-[12px] text-(--text-primary) resize-y"
                />
            </div>

            <FormEnabler label="Active (included in the weekly rotation)" isEnabled={form.active} onChange={v => set('active', v)} />

            {(clientError || error) && (
                <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                    {error || clientError}
                </div>
            )}

            <div className="flex justify-end gap-2 pt-1">
                <button
                    type="button"
                    onClick={onCancel}
                    className="px-3 py-1.5 text-[13px] font-semibold text-(--text-secondary) rounded-lg hover:bg-(--background-tertiary) cursor-pointer"
                >
                    Cancel
                </button>
                <button
                    type="button"
                    onClick={submit}
                    disabled={busy || !!clientError}
                    className="px-3 py-1.5 text-[13px] font-bold text-(--background-primary) bg-(--secondary) rounded-lg hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                >
                    {busy ? 'Saving…' : submitLabel}
                </button>
            </div>
        </div>
    );
}
