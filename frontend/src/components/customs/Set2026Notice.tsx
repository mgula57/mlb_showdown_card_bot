import React from 'react';
import { Link } from 'react-router-dom';
import { FaGoogleDrive } from 'react-icons/fa';
import { FaCheck, FaXmark } from 'react-icons/fa6';
import { IMAGE_LIBRARIES_PATH } from '../account/useImageLibraries';
import { NewBadge } from '../shared/NewBadge';

type PhaseStatus = 'complete' | 'current';

const PHASES: { marker: string; label: string; title: string; detail: string; status: PhaseStatus }[] = [
    { marker: '1', label: 'Phase 1', title: 'Initial adjustments', detail: 'First pass on 2026 charts', status: 'complete' },
    { marker: '2', label: 'Phase 2', title: 'Sim balancing', detail: 'Simulations + WOTC set comparisons', status: 'complete' },
    { marker: '10/15', label: 'Phase 3', title: 'Final QA', detail: 'Weights locked in. Curated V1s chosen.', status: 'current' },
];

const PhaseStep: React.FC<{ phase: typeof PHASES[number]; isLast: boolean }> = ({ phase, isLast }) => {
    const isComplete = phase.status === 'complete';
    return (
        <li className="relative flex-1 flex flex-col items-center text-center">
            {/* Connector to the next phase */}
            {!isLast && (
                <span className={`absolute top-3 left-1/2 w-full h-0.5 ${isComplete ? 'bg-(--warning)' : 'bg-(--warning)/30'}`} />
            )}
            <span
                className={`
                    relative z-10 flex items-center justify-center h-6 min-w-6 px-1 rounded-full text-[10px] font-black
                    ${isComplete
                        ? 'bg-(--warning) text-yellow-950'
                        : 'bg-secondary text-(--warning) ring-2 ring-(--warning) '}
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
            <span className={`mt-1.5 text-[11px] font-bold ${isComplete ? 'text-(--warning)' : 'text-primary'}`}>
                {phase.label}
            </span>
            <span className="text-[10px] font-semibold text-secondary leading-tight">{phase.title}</span>
            <span className="mt-0.5 text-[10px] text-gray-500 leading-tight">{phase.detail}</span>
        </li>
    );
};

/** Dismissible notice on the Custom Card Builder covering 2026 set balancing progress and new features. */
export const Set2026Notice: React.FC<{ onDismiss: () => void }> = ({ onDismiss }) => (
    <div className="relative rounded-xl border-2 border-(--warning)/40 bg-background-secondary px-3 py-2.5 text-xs leading-snug shadow-md">
        <button
            onClick={onDismiss}
            aria-label="Dismiss"
            className="absolute top-2 right-2 text-gray-500 hover:text-primary transition-colors cursor-pointer"
        >
            <FaXmark size={18} />
        </button>

        <p className="pr-6 font-bold text-primary">2026 Set Adjustments</p>
        <p className="mt-0.5 pr-6 text-secondary">
            Phase 2 is complete. Onto Phase 3.
        </p>

        <ol className="flex mt-3">
            {PHASES.map((phase, index) => (
                <PhaseStep key={phase.marker} phase={phase} isLast={index === PHASES.length - 1} />
            ))}
        </ol>

        <div className="mt-3 pt-2.5 border-t border-(--warning)/20">
            <p className="flex items-center gap-1.5 font-bold text-primary">
                <FaGoogleDrive className="text-(--warning)" />
                Google Drive Image Libraries
                <NewBadge />
            </p>
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
