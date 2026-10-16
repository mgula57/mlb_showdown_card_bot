import { FaChevronDown, FaChevronUp, FaHandPointer, FaRegBookmark, FaXmark } from 'react-icons/fa6';
import { CardItemCompactFromCardDatabaseRecord } from '../../cards/CardItemCompact';
import type { CardDatabaseRecord } from '../../../api/card_db/cardDatabase';
import { SECTION_LABEL_CLASS } from '../leagueUi';

type Props = {
    queue: CardDatabaseRecord[];
    onMove: (cardId: string, direction: -1 | 1) => void;
    onRemove: (cardId: string) => void;
    onDraft: (card: CardDatabaseRecord) => void;
    /** It's the drafter's pick and nothing is saving. */
    canDraft: boolean;
    /** Whether a card still has an open roster spot - one that doesn't is dimmed. */
    fitsRoster: (card: CardDatabaseRecord) => boolean;
};

const ICON_BUTTON_CLASS = 'flex items-center justify-center text-(--text-tertiary) hover:text-(--text-primary) disabled:opacity-20 disabled:pointer-events-none cursor-pointer';

/** The drafter's ranked queue: draft straight from it, reorder it, or drop players. */
export function DraftQueuePanel({ queue, onMove, onRemove, onDraft, canDraft, fitsRoster }: Props) {
    return (
        <section className="flex flex-col gap-2">
            <div className={SECTION_LABEL_CLASS}>Queue{queue.length ? ` · ${queue.length}` : ''}</div>
            {queue.length === 0 ? (
                <p className="flex items-center gap-1.5 rounded-xl border border-dashed border-(--divider) px-3 py-3 text-[12px] text-(--text-tertiary)">
                    <FaRegBookmark className="shrink-0" />
                    Bookmark players in the pool to line up your next picks.
                </p>
            ) : (
                <ol className="flex flex-col gap-2 pt-2">
                    {queue.map((card, index) => {
                        const fits = fitsRoster(card);
                        return (
                            <li key={card.id} className="flex items-center gap-1.5">
                                <span className="w-5 shrink-0 text-right text-[11px] font-black tabular-nums text-(--text-tertiary)">{index + 1}</span>
                                <div className={`flex-1 min-w-0 ${fits ? '' : 'opacity-50'}`} title={fits ? undefined : 'No open spot on your roster fits this card'}>
                                    <CardItemCompactFromCardDatabaseRecord card={card} />
                                </div>
                                <div className="flex flex-col shrink-0">
                                    <button type="button" onClick={() => onMove(card.id, -1)} disabled={index === 0} className={ICON_BUTTON_CLASS} aria-label="Move up">
                                        <FaChevronUp className="text-[9px]" />
                                    </button>
                                    <button type="button" onClick={() => onMove(card.id, 1)} disabled={index === queue.length - 1} className={ICON_BUTTON_CLASS} aria-label="Move down">
                                        <FaChevronDown className="text-[9px]" />
                                    </button>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => onDraft(card)}
                                    disabled={!canDraft}
                                    title={canDraft ? `Draft ${card.name}` : 'Not your pick'}
                                    // The gradient is unlayered CSS, so it's swapped out rather than overridden with `disabled:`
                                    className={`shrink-0 flex items-center gap-1 rounded-full px-2.5 py-1.5 text-[10px] font-black uppercase tracking-wide ${canDraft
                                        ? 'animated-showdown-gradient text-white shadow-md hover:brightness-110 cursor-pointer'
                                        : 'bg-(--background-tertiary) text-(--text-tertiary) cursor-not-allowed'}`}
                                >
                                    <FaHandPointer /> <span className="hidden sm:inline">Draft</span>
                                </button>
                                <button type="button" onClick={() => onRemove(card.id)} className={`${ICON_BUTTON_CLASS} shrink-0 p-1`} aria-label={`Remove ${card.name} from queue`}>
                                    <FaXmark className="text-[11px]" />
                                </button>
                            </li>
                        );
                    })}
                </ol>
            )}
        </section>
    );
}
