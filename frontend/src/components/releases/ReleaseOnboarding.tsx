import { useContext, useMemo, type ReactNode } from 'react';
import type { Placement } from '@floating-ui/react';
import { ReleaseOnboardingContext, RELEASE_TIP_COPY, useReleaseTip, type ReleaseTipId } from './releaseOnboardingState';
import { Coachmark } from '../shared/Coachmark';
import { Modal } from '../shared/Modal';
import { Plate } from '../shared/Plate';
import { buttonClass } from '../shared/buttonStyles';
import { headingClass } from '../shared/headingStyles';

type ReleaseTipProps = {
    id: Exclude<ReleaseTipId, 'welcome'>;
    /** The tip's moment, e.g. "the pool is empty". */
    show: boolean;
    anchor: HTMLElement | null;
    placement?: Placement;
};

/** One step of the first-build tour, pointing at `anchor` when its turn comes. */
export function ReleaseTip({ id, show, anchor, placement }: ReleaseTipProps) {
    const tip = useReleaseTip(id, show);
    if (!tip.isOpen) return null;
    const copy = RELEASE_TIP_COPY[id];
    return (
        <Coachmark anchor={anchor} placement={placement} eyebrow={tip.progress} title={copy.title} onDismiss={tip.dismiss} onSkipAll={tip.skipAll}>
            {copy.body}
        </Coachmark>
    );
}

const WELCOME_STEPS = [
    { label: 'Player Pool', detail: 'Pick the players with the algorithm, a search, or your own custom cards.' },
    { label: 'Images', detail: 'Choose a card style and render an image for every card.' },
    { label: 'Review & Publish', detail: 'Check for problems, then publish so anyone can browse it.' },
];

/** Opens the tour the first time an owner edits a release that has never been published. */
export function ReleaseOnboardingWelcome() {
    const tip = useReleaseTip('welcome', true);
    if (!tip.isOpen) return null;

    const footer = (
        <div className="flex gap-2">
            <button type="button" onClick={tip.skipAll} className={buttonClass('secondary', 'md', 'flex-1 py-2.5!')}>
                Skip tips
            </button>
            <button type="button" onClick={tip.dismiss} className={buttonClass('primary', 'md', 'flex-1 py-2.5!')}>
                Show me around
            </button>
        </div>
    );

    return (
        <Modal title="Build your first release" subtitle="A quick tour of the Release Builder" size="sm" onClose={tip.dismiss} footer={footer}>
            <div className="px-4 py-4 flex flex-col gap-3">
                <p className="text-[13px] text-(--text-secondary)">
                    A release is your own card set. It holds one or more editions, and you build each one in three steps:
                </p>
                <ol className="flex flex-col gap-2.5">
                    {WELCOME_STEPS.map((step, i) => (
                        <li key={step.label} className="flex items-start gap-2.5">
                            <Plate variant="navy" size="sm" className="mt-0.5 tabular-nums">{i + 1}</Plate>
                            <div className="flex flex-col">
                                <span className={headingClass('panel')}>{step.label}</span>
                                <span className="text-[12px] text-(--text-secondary)">{step.detail}</span>
                            </div>
                        </li>
                    ))}
                </ol>
                <p className="text-[12px] text-(--text-tertiary)">
                    Nothing is public until you publish.
                </p>
            </div>
        </Modal>
    );
}

/** Pauses the tour inside an edition tab that isn't on screen (tabs stay mounted while hidden). */
export function ReleaseOnboardingScope({ active, children }: { active: boolean; children: ReactNode }) {
    const onboarding = useContext(ReleaseOnboardingContext);
    const value = useMemo(
        () => onboarding && !active ? { ...onboarding, enabled: false } : onboarding,
        [onboarding, active]
    );
    return <ReleaseOnboardingContext.Provider value={value}>{children}</ReleaseOnboardingContext.Provider>;
}
