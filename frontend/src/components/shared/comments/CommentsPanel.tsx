import { RightPanel } from '../RightPanel';
import { CommentsSection, type CommentsSectionProps } from './CommentsSection';

type CommentsPanelProps = Omit<CommentsSectionProps, 'active'> & {
    isOpen: boolean;
    onClose: () => void;
    /** What's being discussed, under the title on desktop. */
    subtitle?: string;
};

/** Comments beside the page, in a `RightPanel`. Stays mounted while closed, so reopening it is
 *  instant; it loads the first time it opens. */
export function CommentsPanel({ isOpen, onClose, subtitle, ...section }: CommentsPanelProps) {
    return (
        <RightPanel isOpen={isOpen} onClose={onClose} title="Comments" subtitle={subtitle}>
            <CommentsSection {...section} active={isOpen} />
        </RightPanel>
    );
}
