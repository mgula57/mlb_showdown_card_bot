import { useState } from 'react';
import { FaPlus, FaXmark } from 'react-icons/fa6';
import FormDropdown from '../customs/FormDropdown';
import IconButton from '../shared/IconButton';
import { buttonClass } from '../shared/buttonStyles';
import type { SimFreeAgent, TakeoverClub } from '../../api/sim';

export type FreeAgentSigning = { mlb_id: number; team: string };

type Props = {
    freeAgents: SimFreeAgent[];
    /** Clubs a free agent can sign with, in the order the picker should list them. */
    clubs: TakeoverClub[];
    value: FreeAgentSigning[];
    onChange: (next: FreeAgentSigning[]) => void;
};

function freeAgentDetail(freeAgent: SimFreeAgent): string {
    const sample = freeAgent.is_pitcher ? `${freeAgent.ip ?? 0} IP` : `${freeAgent.pa ?? 0} PA`;
    return `${freeAgent.positions.join('/')} · ${freeAgent.points ?? 0} pts · ${sample}`;
}

/**
 * Picks unsigned free agents and the clubs they sign with for an offseason sim: choose a player
 * and a club, add the pair, repeat. Each player can sign once, so an added one leaves the picker.
 */
export default function FreeAgentSigningsFields({ freeAgents, clubs, value, onChange }: Props) {
    const [pickedId, setPickedId] = useState('');
    const [pickedTeam, setPickedTeam] = useState('');

    const signedIds = new Set(value.map(signing => signing.mlb_id));
    const byId = new Map(freeAgents.map(freeAgent => [freeAgent.mlb_id, freeAgent]));
    const clubNames = new Map(clubs.map(club => [club.abbreviation, club.name]));

    const playerOptions = freeAgents
        .filter(freeAgent => !signedIds.has(freeAgent.mlb_id))
        .map(freeAgent => ({
            value: String(freeAgent.mlb_id),
            label: freeAgent.original_team ? `${freeAgent.name} (${freeAgent.original_team})` : freeAgent.name,
            group: freeAgent.is_small_sample ? 'Depth (small sample)' : 'Regulars',
            trailing: <span className="text-[11px] text-(--text-tertiary)">{freeAgentDetail(freeAgent)}</span>,
        }));

    function add() {
        if (!pickedId || !pickedTeam) return;
        onChange([...value, { mlb_id: Number(pickedId), team: pickedTeam }]);
        setPickedId('');
    }

    return (
        <div className="flex flex-col gap-3">
            <div className="grid grid-cols-1 sm:grid-cols-[1fr_1fr_auto] gap-3 sm:items-end">
                <FormDropdown
                    label="Free agent"
                    options={playerOptions}
                    selectedOption={pickedId}
                    onChange={setPickedId}
                    disabled={playerOptions.length === 0}
                    placeholder={playerOptions.length === 0 ? 'Everyone is signed' : 'Select a player'}
                />
                <FormDropdown
                    label="Signs with"
                    options={clubs.map(club => ({ label: club.name, value: club.abbreviation }))}
                    selectedOption={pickedTeam}
                    onChange={setPickedTeam}
                    placeholder="Select a team"
                />
                <button
                    type="button"
                    onClick={add}
                    disabled={!pickedId || !pickedTeam}
                    className={buttonClass('secondary', 'md')}
                >
                    <FaPlus className="text-[11px]" />
                    Add
                </button>
            </div>

            {value.length > 0 && (
                <ul className="flex flex-col divide-y divide-(--divider) rounded-card border border-form-element">
                    {value.map(signing => {
                        const freeAgent = byId.get(signing.mlb_id);
                        return (
                            <li key={signing.mlb_id} className="flex items-center justify-between gap-2 px-3 py-2 text-[12px]">
                                <div className="flex min-w-0 flex-col">
                                    <span className="truncate">
                                        <span className="font-semibold">{freeAgent?.name ?? signing.mlb_id}</span>
                                        {' → '}
                                        {clubNames.get(signing.team) ?? signing.team}
                                    </span>
                                    {freeAgent && <span className="text-[11px] text-(--text-tertiary)">{freeAgentDetail(freeAgent)}</span>}
                                </div>
                                <IconButton
                                    icon={<FaXmark className="text-[11px]" />}
                                    label={`Remove ${freeAgent?.name ?? 'signing'}`}
                                    onClick={() => onChange(value.filter(other => other.mlb_id !== signing.mlb_id))}
                                />
                            </li>
                        );
                    })}
                </ul>
            )}
        </div>
    );
}
