import { useState } from 'react';
import { FaPlus, FaSpinner } from 'react-icons/fa6';
import { Modal } from '../shared/Modal';
import FormInput from '../customs/FormInput';
import FormDropdown from '../customs/FormDropdown';
import FormEnabler from '../customs/FormEnabler';
import NumberInput from '../customs/NumberInput';
import SetMultiSelect from '../cards/SetMultiSelect';
import { useReleaseEditionOptions } from '../../hooks/useReleaseEditionOptions';
import { createLeague, DEFAULT_LEAGUE_SETTINGS, DEFAULT_LUXURY_TAX, type LeagueSettings, type LeagueState, type LuxuryTax, type LuxuryTaxType } from '../../api/leagues';
import { ERROR_BOX_CLASS, PRIMARY_BUTTON_CLASS, SECONDARY_BUTTON_CLASS, errorMessage } from './leagueUi';

const TEAM_COUNT_OPTIONS = Array.from({ length: 11 }, (_, i) => ({ value: String(i + 2), label: `${i + 2} teams` }));
const LINEUP_SPOTS = 9;
const LUXURY_TAX_TYPE_OPTIONS = [
    { value: 'linear', label: 'Linear ($1 / 10 pts)' },
    { value: 'exponential', label: 'Exponential' },
];

type Props = {
    token: string;
    onCreated: (state: LeagueState) => void;
    onClose: () => void;
};

/** Create a league: name, the editions that make up its card pool, and its roster rules. */
export function NewLeagueModal({ token, onCreated, onClose }: Props) {
    const editionOptions = useReleaseEditionOptions(token);
    const [name, setName] = useState('');
    const [displayName, setDisplayName] = useState('');
    const [editionIds, setEditionIds] = useState<string[]>([]);
    const [settings, setSettings] = useState<LeagueSettings>(DEFAULT_LEAGUE_SETTINGS);
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const update = (patch: Partial<LeagueSettings>) => setSettings(prev => ({ ...prev, ...patch }));
    const updateTax = (patch: Partial<LuxuryTax>) => setSettings(prev => ({ ...prev, luxury_tax: { ...(prev.luxury_tax ?? DEFAULT_LUXURY_TAX), ...patch } }));
    const tax = settings.luxury_tax ?? null;
    const requiredSlots = LINEUP_SPOTS + settings.num_starters + settings.min_bench + settings.min_bullpen;
    const rosterTooSmall = settings.roster_size < requiredSlots;
    const canCreate = name.trim().length > 0 && editionIds.length > 0 && !rosterTooSmall && !creating;

    async function handleCreate() {
        if (!canCreate) return;
        setCreating(true);
        setError(null);
        try {
            onCreated(await createLeague(token, {
                name: name.trim(),
                edition_ids: editionIds,
                settings,
                display_name: displayName.trim() || undefined,
            }));
        } catch (err) {
            setError(errorMessage(err));
            setCreating(false);
        }
    }

    const footer = (
        <div className="flex flex-col gap-2 w-full">
            {error && <div className={ERROR_BOX_CLASS}>{error}</div>}
            <div className="flex justify-end gap-2">
                <button type="button" onClick={onClose} className={SECONDARY_BUTTON_CLASS}>Cancel</button>
                <button type="button" onClick={handleCreate} disabled={!canCreate} className={PRIMARY_BUTTON_CLASS}>
                    {creating ? <FaSpinner className="animate-spin" /> : <FaPlus className="text-[10px]" />}
                    Create League
                </button>
            </div>
        </div>
    );

    return (
        <Modal title="New League" subtitle="Pick a card pool and roster rules - you'll invite people next" onClose={onClose} footer={footer} size="md">
            <div className="flex flex-col gap-4 p-4">
                <FormInput label="League name" value={name} onChange={v => setName(v ?? '')} placeholder="Friday Night Showdown" />
                <FormInput label="Your name in the league" value={displayName} onChange={v => setDisplayName(v ?? '')} placeholder="Defaults to your username" />

                <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-secondary">Card pool</label>
                    {editionOptions === null ? (
                        <div className="h-11 w-full rounded-xl bg-(--background-secondary) animate-pulse" />
                    ) : (
                        <SetMultiSelect
                            variant="form"
                            options={editionOptions}
                            selections={editionIds}
                            onChange={setEditionIds}
                            placeholder={editionOptions.length === 0 ? 'No editions available' : 'Pick editions'}
                            disabled={editionOptions.length === 0}
                        />
                    )}
                    <span className="text-[11px] text-(--text-tertiary)">
                        Every card in these Release Builder editions is up for grabs, one copy each. All editions must use the same Showdown set.
                    </span>
                </div>

                <FormDropdown
                    label="Teams"
                    selectedOption={String(settings.team_count)}
                    options={TEAM_COUNT_OPTIONS}
                    onChange={v => update({ team_count: Number(v) })}
                />

                <div className="grid grid-cols-2 gap-3">
                    <NumberInput label="Roster size" value={settings.roster_size} onChange={v => update({ roster_size: v })} />
                    <NumberInput label="Starting pitchers" value={settings.num_starters} onChange={v => update({ num_starters: v })} />
                    <NumberInput label="Min bench" value={settings.min_bench} onChange={v => update({ min_bench: v })} />
                    <NumberInput label="Min bullpen" value={settings.min_bullpen} onChange={v => update({ min_bullpen: v })} />
                </div>
                {rosterTooSmall && (
                    <div className={ERROR_BOX_CLASS}>
                        A roster needs at least {requiredSlots} cards: 9 lineup spots, {settings.num_starters} starters, {settings.min_bench} bench, {settings.min_bullpen} bullpen.
                    </div>
                )}

                <FormEnabler
                    label="Points cap"
                    isEnabled={settings.pts_cap !== null}
                    onChange={wasEnabled => update(wasEnabled ? { pts_cap: null, luxury_tax: null } : { pts_cap: 5000 })}
                />
                {settings.pts_cap !== null && (
                    <>
                        <NumberInput label="Max points per roster" value={settings.pts_cap} onChange={v => update({ pts_cap: v })} />
                        <FormEnabler
                            label="Luxury tax (soft cap)"
                            isEnabled={tax !== null}
                            onChange={wasEnabled => update({ luxury_tax: wasEnabled ? null : DEFAULT_LUXURY_TAX })}
                        />
                        {tax !== null && (
                            <>
                                <div className="grid grid-cols-2 gap-3">
                                    <NumberInput label="Buy-in ($)" value={tax.buy_in} onChange={v => updateTax({ buy_in: v })} />
                                    <FormDropdown
                                        label="Tax curve"
                                        selectedOption={tax.type}
                                        options={LUXURY_TAX_TYPE_OPTIONS}
                                        onChange={v => updateTax({ type: v as LuxuryTaxType })}
                                    />
                                </div>
                                <span className="text-[11px] text-(--text-tertiary)">
                                    Teams can draft over the cap. Every team pays the buy-in, and teams that finish over the cap pay a tax on top.
                                </span>
                            </>
                        )}
                    </>
                )}
            </div>
        </Modal>
    );
}
