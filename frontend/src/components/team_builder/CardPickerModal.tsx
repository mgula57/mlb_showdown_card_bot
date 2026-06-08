/**
 * @fileoverview CardPickerModal - Card search modal for selecting a card into a slot
 */

import { useState } from 'react';
import { Modal } from '../shared/Modal';
import ShowdownCardSearch from '../cards/ShowdownCardSearch';
import { CardSource } from '../../types/cardSource';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import type { TeamBuilderCardSnapshot } from '../../api/teamBuilder';

interface CardPickerModalProps {
    slotKey: string;
    onSelect: (snapshot: TeamBuilderCardSnapshot, cardId: string, source: 'bot' | 'wotc') => void;
    onClose: () => void;
    defaultSet?: string;
}

function isPitcherSlot(slotKey: string): boolean {
    return slotKey.startsWith('SP') || slotKey.startsWith('RP');
}

function getSlotLabel(slotKey: string): string {
    if (slotKey.startsWith('SP')) return `SP${slotKey.slice(2)}`;
    if (slotKey.startsWith('RP')) return `RP${slotKey.slice(2)}`;
    if (slotKey.startsWith('BE')) return `BE${slotKey.slice(2)}`;
    const labels: Record<string, string> = { CA: 'C', '1B': '1B', '2B': '2B', '3B': '3B', SS: 'SS', LF: 'LF', CF: 'CF', RF: 'RF', DH: 'DH' };
    return labels[slotKey] ?? slotKey;
}

function snapshotFromRecord(card: CardDatabaseRecord): TeamBuilderCardSnapshot {
    return {
        name: card.name,
        year: card.year,
        team: card.team || '',
        points: card.points || 0,
        command: card.command || 0,
        outs: card.outs || 0,
        is_pitcher: card.is_pitcher || false,
        color_primary: card.color_primary,
        color_secondary: card.color_secondary,
        positions_and_defense_string: card.positions_and_defense_string,
        ip: card.ip,
        speed: card.speed,
        showdown_set: card.showdown_set || '',
        card_year: card.card_year,
    };
}

export default function CardPickerModal({ slotKey, onSelect, onClose, defaultSet }: CardPickerModalProps) {
    const [activeSource, setActiveSource] = useState<'bot' | 'wotc'>('bot');
    const isPitcher = isPitcherSlot(slotKey);
    const label = getSlotLabel(slotKey);

    const defaultFilters = {
        ...(defaultSet ? { showdown_set: [defaultSet] } : {}),
        ...(isPitcher ? { player_type: ['Pitcher'] } : slotKey !== 'DH' && !slotKey.startsWith('BE') ? { player_type: ['Hitter'] } : {}),
    };

    const handleCardSelect = (card: CardDatabaseRecord) => {
        onSelect(snapshotFromRecord(card), card.id, activeSource);
    };

    const cardSource = activeSource === 'bot' ? CardSource.BOT : CardSource.WOTC;

    return (
        <Modal onClose={onClose} title={`Select card for ${label}`} size="xl" isVisible>
            {/* Source toggle */}
            <div className="flex gap-2 px-4 pt-3 pb-1 border-b border-(--divider)">
                {(['bot', 'wotc'] as const).map(src => (
                    <button
                        key={src}
                        type="button"
                        onClick={() => setActiveSource(src)}
                        className={`px-3 py-1 rounded-lg text-sm font-semibold transition-colors cursor-pointer ${
                            activeSource === src
                                ? 'bg-(--showdown-blue) text-white'
                                : 'bg-(--background-tertiary) text-(--text-secondary) hover:bg-(--background-quaternary)'
                        }`}
                    >
                        {src.toUpperCase()}
                    </button>
                ))}
            </div>
            <ShowdownCardSearch
                source={cardSource}
                defaultFilters={defaultFilters}
                disableLocalStorage
                onCardSelect={handleCardSelect}
                verticalOffset="0"
            />
        </Modal>
    );
}
