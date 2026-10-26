import React from 'react';
import { Link } from 'react-router-dom';
import { FaGoogleDrive } from 'react-icons/fa';
import { FaCheck, FaXmark } from 'react-icons/fa6';
import { IMAGE_LIBRARIES_PATH } from '../account/useImageLibraries';
import { NewBadge } from '../shared/NewBadge';
import { Heading } from '../shared/Heading';
import { CAPS_LABEL_CLASS } from '../shared/fieldStyles';

type PhaseStatus = 'complete' | 'current';

const PHASES: { marker: string; label: string; title: string; detail: string; status: PhaseStatus }[] = [
    { marker: '1', label: 'Phase 1', title: 'Initial adjustments', detail: 'First pass on 2026 charts', status: 'complete' },
    { marker: '2', label: 'Phase 2', title: 'Sim balancing', detail: 'Simulations + WOTC set comparisons', status: 'complete' },
    { marker: '3', label: 'Phase 3', title: 'Final QA', detail: 'Weights locked in. Curated V1s chosen.', status: 'complete' },
];

const RELEASE_NOTES_URL = 'https://github.com/mgula57/mlb_showdown_card_bot/releases/tag/v4.43';

const PhaseStep: React.FC<{ phase: typeof PHASES[number]; isLast: boolean }> = ({ phase, isLast }) => {
    const isComplete = phase.status === 'complete';
    return (
        <li className="relative flex-1 flex flex-col items-center text-center">
            {/* Connector to the next phase */}
            {!isLast && (
                <span className={`absolute top-3 left-1/2 w-full h-0.5 ${isComplete ? 'bg-(--success)' : 'bg-(--warning)/30'}`} />
            )}
            <span
                // design-ok: numbered step marker on a timeline, a circle by design
                className={`
                    relative z-10 flex items-center justify-center h-6 min-w-6 px-1 rounded-full text-[10px] font-bold
                    ${isComplete
                        ? 'bg-(--success) text-white'
                        : 'bg-secondary text-(--warning) border-2 border-dotted border-(--warning)'}
                `}
            >
                {isComplete 
                    ? <FaCheck size={10} /> 
                    : 
                    <div className="flex items-center">
                        {/* Animating Live Circle */}
                        <span className="w-2 h-2 bg-(--warning) rounded-full animate-pulse" />
                        <span className="ml-1">{phase.marker}</span>
                    </div>
                }
            </span>
            <span className={`mt-1.5 ${CAPS_LABEL_CLASS} ${isComplete ? 'text-(--success)' : 'text-(--text-primary)'}`}>
                {phase.label}
            </span>
            <span className="text-[10px] font-semibold text-secondary leading-tight">{phase.title}</span>
            <span className="mt-0.5 text-[10px] text-(--text-tertiary) leading-tight">{phase.detail}</span>
        </li>
    );
};

/** Dismissible notice on the Custom Card Builder covering 2026 set balancing progress and new features. */
export const Set2026Notice: React.FC<{ onDismiss: () => void }> = ({ onDismiss }) => (
    <div className="relative rounded-card border border-(--success)/50 bg-(--background-secondary) px-3 py-2.5 text-xs leading-snug">
        <button
            onClick={onDismiss}
            aria-label="Dismiss"
            className="absolute top-2 right-2 text-(--text-tertiary) hover:text-(--text-primary) transition-colors cursor-pointer"
        >
            <FaXmark size={18} />
        </button>

        <Heading level="panel" as="h3" className="pr-6">2026 Set Adjustments</Heading>
        <p className="mt-0.5 pr-6 text-secondary">
            All phases are complete! Curations and adjustments are finalized for 2026 cards.{' '}
            <a href={RELEASE_NOTES_URL} target="_blank" rel="noopener noreferrer" className="text-tertiary underline cursor-pointer hover:opacity-80">
                Read the v4.43 release notes
            </a>
        </p>

        <ol className="flex mt-3">
            {PHASES.map((phase, index) => (
                <PhaseStep key={phase.marker} phase={phase} isLast={index === PHASES.length - 1} />
            ))}
        </ol>

        <div className="mt-3 pt-2.5 border-t border-(--success)/20">
            <Heading level="panel" as="h3" className="flex items-center gap-1.5">
                <FaGoogleDrive className="text-(--success)" />
                Google Drive Image Libraries
                <NewBadge />
            </Heading>
            <p className="mt-0.5 text-secondary">
                Link a Google Drive folder of your own player images and cards set to Auto will use them automatically. No more uploading an image for every card.{' '}
                <Link to={IMAGE_LIBRARIES_PATH} className="text-tertiary underline cursor-pointer hover:opacity-80">
                    Connect a folder
                </Link>
            </p>
        </div>
    </div>
);

export default Set2026Notice;
