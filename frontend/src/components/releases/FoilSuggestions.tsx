/**
 * @fileoverview Release Builder foil suggestions: picks about 15% of an edition's saved cards to tag
 * FOIL the way WOTC chose foils (`FoilSuggester` on the backend), shown as an unsaved preview on the
 * pool grid that the owner applies or discards. Suggest only: nothing is tagged until applied.
 */

import { useEffect, useRef, useState } from 'react';
import { FaSpinner, FaWandMagicSparkles } from 'react-icons/fa6';
import type { FoilSetType } from '../../api/releases';
import { buttonClass } from '../shared/buttonStyles';
import { choiceClass } from '../shared/choiceStyles';
import { FIELD_LABEL_CLASS } from '../shared/fieldStyles';
import { InlineError } from '../shared/InlineError';
import FormEnabler from '../customs/FormEnabler';
import { PoolPreviewBanner } from './PoolPreviewBanner';
import type { FoilSuggestionsState } from './useFoilSuggestions';

/** The floating settings panel under a pool toolbar button (numbering, foils). */
export const POOL_TOOLBAR_POPOVER_CLASS = 'absolute right-0 top-full mt-2 w-80 max-w-[calc(100vw-2rem)] p-3 bg-(--background-secondary) border border-(--divider) rounded-card shadow-overlay z-50 flex flex-col gap-4';

const SET_TYPE_OPTIONS: { value: FoilSetType; label: string; description: string }[] = [
    {
        value: 'BASE',
        label: 'Base set',
        description: 'Every team gets a foil, usually its best card, and stronger teams get a few more. Closers, award winners and legends can beat higher points.',
    },
    {
        value: 'EXPANSION',
        label: 'Expansion',
        description: "The edition's standouts wherever they play: big seasons, award winners and stat leaders.",
    },
];

type FoilSuggestControlProps = {
    foils: FoilSuggestionsState;
    /** Waits out in-flight saves, since suggestions are picked from the saved cards. */
    disabled: boolean;
};

/** The pool toolbar's "Suggest foils" button and its set type settings. */
export function FoilSuggestControl({ foils, disabled }: FoilSuggestControlProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [setType, setSetType] = useState<FoilSetType>('BASE');
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!isOpen) return;
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) setIsOpen(false);
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [isOpen]);

    async function handleSuggest() {
        if (await foils.run(setType)) setIsOpen(false);
    }

    return (
        <div className="relative shrink-0" ref={containerRef}>
            <button
                type="button"
                onClick={() => setIsOpen(v => !v)}
                className={buttonClass('secondary', 'sm', 'min-h-9')}
            >
                <FaWandMagicSparkles className="text-[12px]" /> Suggest foils
            </button>

            {isOpen && (
                <div className={POOL_TOOLBAR_POPOVER_CLASS}>
                    <div className="flex flex-col gap-2">
                        <span className={FIELD_LABEL_CLASS}>This edition is</span>
                        <div className="flex gap-1.5">
                            {SET_TYPE_OPTIONS.map(option => (
                                <button
                                    key={option.value}
                                    type="button"
                                    onClick={() => setSetType(option.value)}
                                    className={choiceClass(setType === option.value)}
                                >
                                    {option.label}
                                </button>
                            ))}
                        </div>
                        <p className="text-[12px] text-(--text-secondary)">
                            {SET_TYPE_OPTIONS.find(option => option.value === setType)?.description}
                        </p>
                    </div>
                    <p className="text-[12px] text-(--text-tertiary)">
                        Picks about 15% of the edition as foils, counting cards already tagged FOIL. You review the picks before anything is tagged.
                    </p>
                    {foils.error && <InlineError size="sm">{foils.error}</InlineError>}
                    <button
                        type="button"
                        onClick={handleSuggest}
                        disabled={disabled || foils.isLoading}
                        className={buttonClass('primary', 'sm', 'self-start')}
                    >
                        {foils.isLoading ? <><FaSpinner className="animate-spin text-[12px]" /> Suggesting…</> : 'Suggest foils'}
                    </button>
                </div>
            )}
        </div>
    );
}

type FoilSuggestionBannerProps = {
    foils: FoilSuggestionsState;
    /** Picks still waiting: on a card in the pool that isn't tagged FOIL yet. */
    count: number;
    onApply: () => void;
};

/** Above the pool grid while suggestions are showing. */
export function FoilSuggestionBanner({ foils, count, onApply }: FoilSuggestionBannerProps) {
    if (!foils.result) return null;
    const { existing_count: existingCount, target } = foils.result;
    return (
        <PoolPreviewBanner
            title={`Foil suggestions — ${count} card${count === 1 ? '' : 's'}`}
            description={
                <>
                    Not saved yet. Suggested cards show a dashed FOIL? tag: hover it to see why, or skip it with ×.
                    {existingCount > 0 && ` Keeps the ${existingCount} card${existingCount === 1 ? '' : 's'} already tagged FOIL, for ${existingCount + count} of ${target}.`}
                    {count === 0 && existingCount >= target && ' This edition already has enough foils.'}
                </>
            }
        >
            <div className="flex flex-wrap items-center gap-2">
                <button
                    type="button"
                    onClick={onApply}
                    disabled={count === 0}
                    className={buttonClass('primary', 'sm')}
                >
                    Tag {count} as FOIL
                </button>
                <FormEnabler
                    label="Only suggested"
                    size="sm"
                    isEnabled={foils.onlySuggested}
                    onChange={enabled => foils.setOnlySuggested(!enabled)}
                />
                <button
                    type="button"
                    onClick={foils.clear}
                    className={buttonClass('ghost', 'sm')}
                >
                    Discard
                </button>
            </div>
        </PoolPreviewBanner>
    );
}
