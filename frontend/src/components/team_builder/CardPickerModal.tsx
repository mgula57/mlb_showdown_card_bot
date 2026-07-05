import { useState, useEffect, useRef } from 'react';
import { Modal } from '../shared/Modal';
import { fetchCardData, type CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { CardItemCompactFromCardDatabaseRecord } from '../cards/CardItemCompact';
import { CardSource } from '../../types/cardSource';
import type { CardSource as CardSourceType } from '../../types/cardSource';
import FormInput from '../customs/FormInput';
import { FaSpinner } from 'react-icons/fa6';

type CardPickerModalProps = {
    title?: string;
    showdownSet?: string;
    isPitcherOnly?: boolean;
    isHitterOnly?: boolean;
    onSelect: (card: CardDatabaseRecord, source: CardSourceType) => void;
    onClose: () => void;
};

const SOURCES = [
    { key: CardSource.BOT, label: 'Showdown Bot' },
    { key: CardSource.WOTC, label: 'WOTC' },
    { key: CardSource.WBC, label: 'WBC' },
] as const;

export function CardPickerModal({
    title = 'Pick a Card',
    showdownSet,
    isPitcherOnly = false,
    isHitterOnly = false,
    onSelect,
    onClose,
}: CardPickerModalProps) {
    const [source, setSource] = useState<CardSourceType>(CardSource.BOT);
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<CardDatabaseRecord[]>([]);
    const [loading, setLoading] = useState(false);
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        if (debounceRef.current) clearTimeout(debounceRef.current);
        if (query.trim().length < 2) {
            setResults([]);
            return;
        }
        debounceRef.current = setTimeout(async () => {
            setLoading(true);
            try {
                const payload: Record<string, unknown> = {
                    name: query.trim(),
                    limit: 30,
                };
                if (showdownSet) payload.showdown_set = showdownSet;
                if (isPitcherOnly) payload.player_type = 'Pitcher';
                if (isHitterOnly) payload.player_type = 'Hitter';

                const cards = await fetchCardData(source as any, payload);
                setResults(cards);
            } catch {
                setResults([]);
            } finally {
                setLoading(false);
            }
        }, 300);

        return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
    }, [query, source, showdownSet, isPitcherOnly, isHitterOnly]);

    return (
        <Modal title={title} onClose={onClose} size="md">
            <div className="flex flex-col gap-3 p-4 min-h-0">
                {/* Source tabs */}
                <div className="flex gap-1">
                    {SOURCES.map(s => (
                        <button
                            key={s.key}
                            type="button"
                            onClick={() => { setSource(s.key); setResults([]); }}
                            className={`text-[11px] font-semibold px-2.5 py-1 rounded border transition-colors
                                ${source === s.key
                                    ? 'border-(--secondary) text-(--secondary)'
                                    : 'border-(--divider) text-(--text-secondary) hover:border-(--secondary)/50'
                                }`}
                        >
                            {s.label}
                        </button>
                    ))}
                </div>

                {/* Search */}
                <FormInput
                    label="Player Name"
                    value={query}
                    onChange={v => setQuery(v ?? '')}
                    isClearable
                    showSearchIcon
                    placeholder="Search..."
                />

                {/* Results */}
                <div className="flex flex-col gap-1 overflow-y-auto max-h-96">
                    {loading && (
                        <div className="flex justify-center py-6">
                            <FaSpinner className="animate-spin text-(--text-tertiary)" />
                        </div>
                    )}
                    {!loading && results.length === 0 && query.trim().length >= 2 && (
                        <p className="text-center text-[12px] text-(--text-tertiary) py-4">No cards found.</p>
                    )}
                    {!loading && query.trim().length < 2 && (
                        <p className="text-center text-[12px] text-(--text-tertiary) py-4">Type at least 2 characters to search.</p>
                    )}
                    {results.map(card => (
                        <CardItemCompactFromCardDatabaseRecord
                            key={card.id}
                            card={card}
                            onClick={() => onSelect(card, source)}
                        />
                    ))}
                </div>
            </div>
        </Modal>
    );
}
