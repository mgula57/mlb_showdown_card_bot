import { useContext, useState } from 'react';
import { FaLightbulb } from 'react-icons/fa6';
import { RELEASE_GUIDE, RELEASE_GUIDE_SECTIONS, type ReleaseGuideSectionId } from './releaseGuideContent';
import { ReleaseOnboardingContext } from './releaseOnboardingState';
import { SideDrawer } from '../shared/SideDrawer';
import { SlideOver } from '../shared/SlideOver';
import { Heading } from '../shared/Heading';
import { Eyebrow } from '../shared/Eyebrow';
import { choiceClass } from '../shared/choiceStyles';
import { buttonClass } from '../shared/buttonStyles';
import { headingClass } from '../shared/headingStyles';
import { useMediaQuery } from '../../hooks/useMediaQuery';

type ReleaseGuideProps = {
    /** The section to show, or null while closed. A new value (e.g. from the current step) switches to it. */
    section: ReleaseGuideSectionId | null;
    onClose: () => void;
};

/**
 * Tips and best practices for building a release, on demand: a docked panel beside the builder on
 * desktop, a slide-over on phones. Opens on the section for the step the user is on; the switcher
 * reaches the rest. The first-build tour (ReleaseOnboarding) covers the controls themselves.
 */
export function ReleaseGuide({ section, onClose }: ReleaseGuideProps) {
    const isOpen = section !== null;
    const [shown, setShown] = useState<ReleaseGuideSectionId>(section ?? 'plan');
    // A new section from the caller (opening, or the step changing while open) switches to it
    const [requested, setRequested] = useState(section);
    if (section !== requested) {
        setRequested(section);
        if (section) setShown(section);
    }
    const isDesktop = useMediaQuery('(min-width: 1024px)');

    const onboarding = useContext(ReleaseOnboardingContext);
    const canReplayTour = !!onboarding?.canRestart;
    function replayTour() {
        onboarding?.restart();
        onClose();
    }

    const switcher = (
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Guide sections">
            {RELEASE_GUIDE_SECTIONS.map((id, i) => (
                <button
                    key={id}
                    type="button"
                    aria-pressed={shown === id}
                    onClick={() => setShown(id)}
                    className={choiceClass(shown === id, 'sm', 'max-sm:min-h-11')}
                >
                    {i > 0 && <span className="tabular-nums text-(--text-tertiary)">{i}</span>}
                    {RELEASE_GUIDE[id].label}
                </button>
            ))}
        </div>
    );

    const guide = RELEASE_GUIDE[shown];
    const stepNumber = RELEASE_GUIDE_SECTIONS.indexOf(shown);
    const body = (
        <div className="flex flex-col gap-4 px-4 py-4">
            <div className="flex flex-col gap-1">
                {stepNumber > 0 && <Eyebrow>Step {stepNumber} of {RELEASE_GUIDE_SECTIONS.length - 1}</Eyebrow>}
                <Heading level="section" as="h3">{guide.title}</Heading>
            </div>
            <ul className="flex flex-col gap-3.5">
                {guide.tips.map(tip => (
                    <li key={tip.title} className="flex flex-col gap-0.5">
                        <span className={headingClass('panel')}>{tip.title}</span>
                        <span className="text-[13px] text-(--text-secondary)">{tip.body}</span>
                    </li>
                ))}
            </ul>
        </div>
    );

    const replay = canReplayTour && (
        <button type="button" onClick={replayTour} className={buttonClass('secondary', 'sm', 'w-full max-sm:min-h-11')}>
            Replay the tour
        </button>
    );

    if (isDesktop) {
        return (
            <SideDrawer
                isOpen={isOpen}
                onClose={onClose}
                title="Release Builder Tips"
                subtitle="Best practices for building a set"
                headerContent={switcher}
                footer={replay || undefined}
            >
                {body}
            </SideDrawer>
        );
    }
    return (
        <SlideOver isOpen={isOpen} onClose={onClose} title="Release Builder Tips" handleContent={<div className="px-4 pb-2">{switcher}</div>}>
            {body}
            {replay && <div className="px-4 pb-24">{replay}</div>}
        </SlideOver>
    );
}

/** Opens the guide. Sized to sit beside the other secondary actions in a header or step bar. */
export function ReleaseGuideButton({ onClick, className = '' }: { onClick: () => void; className?: string }) {
    return (
        <button type="button" onClick={onClick} title="Tips and best practices" aria-label="Tips" className={buttonClass('secondary', 'sm', className)}>
            <FaLightbulb className="text-[12px] shrink-0" />
            <span className="hidden sm:inline">Tips</span>
        </button>
    );
}
