import { FaCompass, FaMagnifyingGlass, FaWandMagicSparkles } from 'react-icons/fa6';
import type { IconType } from 'react-icons';

import { Modal } from '../shared/Modal';
import { NewBadge } from '../shared/NewBadge';

/** How the drafter adds players: search the card pool freely, or one Guided Draft round at a time. */
export type DraftMode = 'search' | 'guided';

/** What the draft-start chooser can hand back — a draft mode, or "run autofill". */
export type DraftStartChoice = DraftMode | 'autofill';

const START_CHOICES: { value: DraftStartChoice; icon: IconType; title: string; description: string; isNew?: boolean }[] = [
    { value: 'search', icon: FaMagnifyingGlass, title: 'Search & Pick', description: 'Search the full card pool and fill any slot with any card.' },
    { value: 'guided', icon: FaCompass, title: 'Guided Draft', description: 'Pick from a few similarly priced cards each round — starting with your Ace, Star, and Closer.', isNew: true },
    { value: 'autofill', icon: FaWandMagicSparkles, title: 'Autofill', description: 'Set a strategy and let the bot draft a full roster for you to review.' },
];

/** Shown once when drafting starts on an empty roster: how does the drafter want to build it? */
export function DraftModeChooser({ onChoose, onClose }: { onChoose: (choice: DraftStartChoice) => void; onClose: () => void }) {
    return (
        <Modal title="How do you want to draft?" subtitle="You can switch any time from the banner." onClose={onClose} size="md">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 p-4">
                {START_CHOICES.map(({ value, icon: Icon, title, description, isNew }) => (
                    <button
                        key={value}
                        type="button"
                        onClick={() => onChoose(value)}
                        className="flex sm:flex-col items-start gap-3 sm:gap-2 rounded-xl border border-(--divider) bg-(--background-secondary) p-3 text-left cursor-pointer transition-colors hover:border-(--showdown-red)"
                    >
                        <span className="flex items-center justify-center w-9 h-9 shrink-0 rounded-full bg-(--showdown-red)/10 text-(--showdown-red)">
                            <Icon className="text-[15px]" />
                        </span>
                        <span className="flex flex-col gap-1 min-w-0">
                            <span className="flex items-center gap-1.5 text-[13px] font-bold text-(--text-primary)">
                                {title}
                                {isNew && <NewBadge />}
                            </span>
                            <span className="text-[11px] leading-snug text-(--text-secondary)">{description}</span>
                        </span>
                    </button>
                ))}
            </div>
        </Modal>
    );
}

/** Search | Guided switch for the team-colored drafting banner. `btnClass` comes from
 *  `bannerTokens` so it reads against the team's colors; the inactive side is dimmed. Labels
 *  collapse to icons on small screens unless `alwaysShowLabels` (the banner has room to spare). */
export function DraftModeBannerToggle({ mode, onChange, btnClass, alwaysShowLabels = false }: {
    mode: DraftMode;
    onChange: (mode: DraftMode) => void;
    btnClass: string;
    alwaysShowLabels?: boolean;
}) {
    const option = (value: DraftMode, Icon: IconType, label: string) => (
        <button
            type="button"
            role="radio"
            aria-checked={mode === value}
            onClick={() => onChange(value)}
            title={value === 'guided' ? 'Guided Draft — pick from a few options each round' : 'Search the card pool'}
            className={`flex items-center gap-1 px-2 h-full text-[11px] font-bold cursor-pointer transition-opacity ${mode === value ? 'bg-black/20' : 'opacity-60 hover:opacity-100'}`}
        >
            <Icon className="text-[10px]" />
            <span className={alwaysShowLabels ? 'inline' : 'hidden sm:inline'}>{label}</span>
        </button>
    );
    return (
        <div role="radiogroup" aria-label="Draft mode" className={`flex items-stretch h-7 rounded-lg overflow-hidden ${btnClass}`}>
            {option('search', FaMagnifyingGlass, 'Search')}
            {option('guided', FaCompass, 'Guided')}
        </div>
    );
}
