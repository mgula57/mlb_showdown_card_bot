import type { ReactNode } from 'react';
import { FaSpinner } from 'react-icons/fa6';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { BULLPEN_ROLES, ROTATION_ROLES } from '../../api/userTeams';
import { CardItemFromCardDatabaseRecord } from '../cards/CardItem';
import { Modal } from '../shared/Modal';
import { CAPS_LABEL_CLASS } from '../shared/fieldStyles';

export type DraftPositionOption = {
    position: string;
    /** Team points before / after the pick — shown together as "current → projected". */
    currentPts?: number;
    projectedPts?: number;
    overLimit?: boolean;
    /** When set, this pick replaces an existing player — shown under the label. */
    replacingName?: string | null;
};

type Props = {
    card: CardDatabaseRecord;
    options: DraftPositionOption[];
    onSelect: (position: string) => void;
    onClose: () => void;
    /** The position whose pick is saving - shows a spinner there and blocks the other buttons. */
    savingPosition?: string | null;
    /** Blocks every position button (e.g. it's no longer the drafter's pick). */
    disabled?: boolean;
    /** Shown under the position buttons - notes, errors, or a fallback action. */
    children?: ReactNode;
};

/** "Choose a position" for a just-picked card: the card, then its eligible positions grouped
 *  into field / rotation / bullpen. Shared by the team builder and the league draft. */
export function DraftPositionModal({ card, options, onSelect, onClose, savingPosition = null, disabled = false, children }: Props) {
    const isPitcherRole = (pos: string) => ROTATION_ROLES.includes(pos) || BULLPEN_ROLES.includes(pos);
    const groups: { label: string | null; options: DraftPositionOption[]; layout: string }[] = [
        { label: null, options: options.filter(o => !isPitcherRole(o.position)), layout: 'grid grid-cols-2 lg:grid-cols-3' },
        { label: 'Rotation', options: options.filter(o => ROTATION_ROLES.includes(o.position)), layout: 'grid grid-cols-2 lg:grid-cols-3' },
        { label: 'Bullpen', options: options.filter(o => BULLPEN_ROLES.includes(o.position)), layout: 'flex flex-wrap' },
    ];

    return (
        <Modal
            size="sm"
            onClose={onClose}
            title="Choose a position"
            subtitle="Where should this card be placed?"
        >
            {/* Card preview */}
            <div className="px-4 py-3 border-b border-(--divider)">
                <CardItemFromCardDatabaseRecord card={card} />
            </div>

            {/* Position buttons */}
            <div className="px-4 py-3 flex flex-col gap-2">
                {groups.filter(g => g.options.length > 0).map(group => (
                    <div key={group.label ?? 'field'} className="flex flex-col gap-2">
                        {group.label && (
                            <div className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>{group.label}</div>
                        )}
                        <div className={`${group.layout} gap-1.5`}>
                            {group.options.map(option => (
                                <PositionButton
                                    key={option.position}
                                    option={option}
                                    onClick={() => onSelect(option.position)}
                                    isSaving={savingPosition === option.position}
                                    disabled={disabled || savingPosition !== null}
                                />
                            ))}
                        </div>
                    </div>
                ))}
                {children}
            </div>
        </Modal>
    );
}

function PositionButton({ option, onClick, isSaving, disabled }: {
    option: DraftPositionOption;
    onClick: () => void;
    isSaving: boolean;
    disabled: boolean;
}) {
    const { position, currentPts, projectedPts, overLimit, replacingName } = option;
    return (
        <button
            type="button"
            onClick={onClick}
            disabled={disabled}
            className="flex flex-col items-center justify-between gap-0.5 px-3 py-2 rounded-control text-[12px] font-bold
                bg-(--background-secondary) border border-(--divider)
                text-(--text-primary) hover:border-(--rule-strong)
                transition-colors cursor-pointer disabled:cursor-not-allowed disabled:opacity-60
                disabled:hover:border-(--divider)"
        >
            <span className="flex items-center gap-1">
                {isSaving && <FaSpinner className="animate-spin text-[10px]" />}
                {position}
            </span>
            {replacingName && (
                <span className="text-[9px] font-semibold text-(--text-tertiary) normal-case">
                    Replaces {replacingName}
                </span>
            )}
            {currentPts != null && projectedPts != null && (
                <span className={`text-[10px] font-semibold tabular-nums ${overLimit ? 'text-(--red)' : 'text-(--text-tertiary)'}`}>
                    {currentPts} → {projectedPts}
                </span>
            )}
        </button>
    );
}
