import type { PitcherAssignment } from '../../api/userTeams';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { CardItemCompactFromCardDatabaseRecord } from '../cards/CardItemCompact';
import { FaPlus } from 'react-icons/fa6';

const ROTATION_ROLES = ['SP1', 'SP2', 'SP3', 'SP4', 'SP5'] as const;
const BULLPEN_ROLES = ['CP', 'SU', 'MR', 'LONG'] as const;

const ROLE_LABELS: Record<string, string> = {
    SP1: 'Ace',
    SP2: 'No. 2',
    SP3: 'No. 3',
    SP4: 'No. 4',
    SP5: 'No. 5',
    CP:  'Closer',
    SU:  'Setup',
    MR:  'Middle Relief',
    LONG: 'Long Relief',
};

type RotationPanelProps = {
    rotation: PitcherAssignment[];
    cardMap: Record<string, CardDatabaseRecord | null>;
    onRoleClick: (role: string, current: PitcherAssignment | null) => void;
    readOnly?: boolean;
};

export function RotationPanel({ rotation, cardMap, onRoleClick, readOnly = false }: RotationPanelProps) {
    const byRole = Object.fromEntries(rotation.map(r => [r.role, r]));

    function renderSlot(role: string) {
        const assignment = byRole[role] ?? null;
        const card = assignment ? cardMap[assignment.card_id] : null;

        return (
            <div key={role} className="flex items-center gap-2">
                <div className="w-20 shrink-0 text-right">
                    <div className="text-[12px] font-black text-(--text-primary)">{role}</div>
                    <div className="text-[10px] text-(--text-tertiary)">{ROLE_LABELS[role]}</div>
                </div>
                {card ? (
                    <CardItemCompactFromCardDatabaseRecord
                        card={card}
                        className="flex-1"
                        onClick={readOnly ? undefined : () => onRoleClick(role, assignment)}
                    />
                ) : (
                    <button
                        type="button"
                        onClick={readOnly ? undefined : () => onRoleClick(role, null)}
                        className={`
                            flex-1 flex items-center gap-1.5 px-2 py-1.5
                            rounded-lg border-2 border-dashed border-(--divider)
                            text-[11px] text-(--text-tertiary)
                            ${!readOnly ? 'hover:border-(--secondary)/50 hover:text-(--secondary) cursor-pointer' : 'cursor-default'}
                        `}
                    >
                        <FaPlus className="text-[9px]" /> Assign
                    </button>
                )}
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-5">
            <div>
                <div className="text-[11px] font-semibold text-(--text-secondary) uppercase tracking-wide mb-2">
                    Starting Rotation
                </div>
                <div className="flex flex-col gap-2">
                    {ROTATION_ROLES.map(role => renderSlot(role))}
                </div>
            </div>

            <div>
                <div className="text-[11px] font-semibold text-(--text-secondary) uppercase tracking-wide mb-2">
                    Bullpen
                </div>
                <div className="flex flex-col gap-2">
                    {BULLPEN_ROLES.map(role => renderSlot(role))}
                </div>
            </div>
        </div>
    );
}
