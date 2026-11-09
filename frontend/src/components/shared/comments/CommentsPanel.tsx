import { SideDrawer } from '../SideDrawer';
import { SlideOver } from '../SlideOver';
import { useMediaQuery } from '../../../hooks/useMediaQuery';
import { CommentsSection, type CommentsSectionProps } from './CommentsSection';

type CommentsPanelProps = Omit<CommentsSectionProps, 'active'> & {
    isOpen: boolean;
    onClose: () => void;
    /** What's being discussed, under the title on desktop. */
    subtitle?: string;
};

/** Comments beside the page: a docked `SideDrawer` on desktop, a `SlideOver` below lg. Stays mounted while
 *  closed, so reopening it is instant; it loads the first time it opens. */
export function CommentsPanel({ isOpen, onClose, subtitle, ...section }: CommentsPanelProps) {
    const isDesktop = useMediaQuery('(min-width: 1024px)');
    const body = <CommentsSection {...section} active={isOpen} />;

    if (isDesktop) {
        return (
            <SideDrawer isOpen={isOpen} onClose={onClose} title="Comments" subtitle={subtitle}>
                <div className="px-4 py-4">{body}</div>
            </SideDrawer>
        );
    }
    return (
        <SlideOver isOpen={isOpen} onClose={onClose} title="Comments">
            {/* Room at the bottom for the floating close button */}
            <div className="px-4 pt-2 pb-28">{body}</div>
        </SlideOver>
    );
}
