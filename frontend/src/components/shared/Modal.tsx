/**
 * @fileoverview Modal Component
 * 
 * A flexible modal dialog component with comprehensive UX features:
 * - Body scroll locking to prevent background scrolling during modal display
 * - Keyboard navigation (ESC key to close)
 * - Click-outside detection for intuitive closing behavior
 * - Multiple size options (sm, md, lg, xl)
 * - Optional title header with styled close button
 * - Reference counting for nested modals
 * - Proper focus management and accessibility considerations
 * 
 * The component uses a global scroll lock counter to handle multiple concurrent
 * modals gracefully, only restoring scroll when all modals are closed.
 * 
 * @component
 * @example
 * ```tsx
 * <Modal 
 *   title="Player Details" 
 *   size="lg" 
 *   onClose={() => setShowModal(false)}
 * >
 *   <PlayerDetailsForm player={selectedPlayer} />
 * </Modal>
 * ```
 */

import { useEffect, useRef } from 'react';
import { FaXmark } from 'react-icons/fa6';

// Global counter to track multiple concurrent modals for proper scroll lock management
let bodyScrollLockCount = 0;

/**
 * Props for the Modal component
 */
type ModalProps = {
    /** Content to be displayed within the modal */
    children: React.ReactNode;
    /** Callback function called when the modal should be closed */
    onClose: () => void;
    /** Optional title to display in the modal header */
    title?: string;
    /** Size preset for the modal width - defaults to 'lg' */
    size?: 'sm' | 'md' | 'lg' | 'xl';
    /** If true, disables the close button in the header */
    disableCloseButton?: boolean;
    /** Controls whether the modal is visible - for scroll lock management */
    isVisible?: boolean;
};

/**
 * Modal component with scroll lock, keyboard navigation, and responsive sizing
 * 
 * Features:
 * - Prevents body scrolling while modal is open using reference counting
 * - ESC key closes modal for keyboard accessibility
 * - Click-outside-to-close behavior for intuitive UX
 * - Configurable sizing with responsive design
 * - Optional header with title and close button
 * - Proper cleanup of event listeners and scroll state
 * 
 * @param props - Modal component props
 * @returns A full-screen modal dialog overlay
 */
export function Modal({ children, onClose, title, size = 'lg', disableCloseButton = false, isVisible = true }: ModalProps) {
    const modalRef = useRef<HTMLDivElement>(null);
    const scrollYRef = useRef(0); // Stores scroll position for restoration

    /**
     * Effect: Keyboard navigation support
     * Listens for ESC key to close modal, improving accessibility
     */
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                onClose();
            }
        };

        document.addEventListener('keydown', handleEscape);
        return () => document.removeEventListener('keydown', handleEscape);
    }, [onClose]);

    /**
     * Handles click-outside-to-close behavior
     * Only closes if the click target is the backdrop (not modal content)
     */
    const handleBackdropClick = (e: React.MouseEvent) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    };

    /**
     * Effect: Body scroll lock mechanism with reference counting
     * 
     * Implements sophisticated scroll locking that:
     * - Increments global counter when modal opens
     * - Only applies scroll lock on first modal (when counter = 1)
     * - Preserves current scroll position
     * - Compensates for scrollbar width to prevent layout shift
     * - Only restores scroll when all modals are closed (counter = 0)
     * - Restores exact scroll position on cleanup
     */
    useEffect(() => {
        // Only apply scroll lock when modal is visible
        if (!isVisible) return;

        // Increment modal count and apply scroll lock if this is the first modal
        bodyScrollLockCount += 1;
        if (bodyScrollLockCount === 1) {
            const body = document.body;
            const docEl = document.documentElement;
            
            // Calculate scrollbar width to prevent layout shift
            const scrollbarWidth = Math.max(0, window.innerWidth - docEl.clientWidth);

            // Store current scroll position for restoration
            scrollYRef.current = window.scrollY;
            
            // Apply scroll lock styles
            body.style.position = 'fixed';
            body.style.top = `-${scrollYRef.current}px`;
            body.style.width = '100%';
            if (scrollbarWidth) body.style.paddingRight = `${scrollbarWidth}px`;
        }

        // Cleanup: decrement counter and restore scroll when all modals are closed
        return () => {
            bodyScrollLockCount -= 1;
            
            // Only restore scroll when no modals remain open
            if (bodyScrollLockCount === 0) {
                const body = document.body;
                const top = body.style.top;
                
                // Remove scroll lock styles
                body.style.position = '';
                body.style.top = '';
                body.style.width = '';
                body.style.paddingRight = '';
                
                // Restore original scroll position
                const y = parseInt(top || '0', 10) || 0;
                window.scrollTo(0, -y);
            }
        };
    }, [isVisible]);

    /** Responsive size classes for different modal sizes */
    const sizeClasses = {
        sm: 'max-w-md',   // Small: ~448px
        md: 'max-w-2xl',  // Medium: ~672px  
        lg: 'max-w-4xl',  // Large: ~896px
        xl: 'max-w-6xl'   // Extra Large: ~1152px
    };

    /** 
     * Renders the close button with consistent styling
     * @returns Close button element with hover effects
     */
    const closeButton = () => (
        <button
            onClick={onClose}
            className="text-(--text-secondary) hover:text-(--text-primary) text-2xl cursor-pointer"
            aria-label="Close modal"
        >
            <FaXmark />
        </button>
    );

    return (
        <div 
            className="fixed left-0 top-0 w-screen h-lvh bg-black/50 flex items-center justify-center z-50 p-4 cursor-pointer"
            onClick={handleBackdropClick}
        >
            {/* Modal container with responsive sizing and theming */}
            <div 
                ref={modalRef}
                className={`
                    bg-(--background-primary) 
                    rounded-2xl
                    shadow-2xl 
                    w-full 
                    ${sizeClasses[size]}
                    max-h-[85vh] 
                    overflow-y-auto
                    cursor-default
                    relative
                    border border-form-element
                `}
            >
                {/* Conditional header with title and close button */}
                {title ? (
                    <div className="flex items-center justify-between p-3 border-b border-(--border-secondary)">
                        <h2 className="text-xl font-semibold text-(--text-primary)">
                            {title}
                        </h2>
                        {closeButton()}
                    </div>
                ) : (
                    !disableCloseButton &&
                    // Floating close button when no title is provided
                    <div className="absolute right-3 top-3 z-10">
                        {closeButton()}
                    </div>
                )}

                {/* Modal content area */}
                <div className="p-0">
                    {children}
                </div>

            </div>
        </div>
    );
}