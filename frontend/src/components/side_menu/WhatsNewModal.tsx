/**
 * @fileoverview WhatsNewModal Component and Version Management
 * 
 * A feature announcement modal system that informs users about new functionality
 * and improvements in the application. Includes sophisticated version tracking
 * to ensure users see announcements only once per version update.
 * 
 * **Core Features:**
 * - Version-based display logic with localStorage persistence
 * - Rich feature presentation with icons and descriptions
 * - Graceful error handling for localStorage failures
 * - Server-side rendering safe utilities
 * - Easy version management for development workflow
 * 
 * **Version Management System:**
 * - Simple version constant that controls modal display
 * - Automatic localStorage-based user tracking
 * - SSR-safe helper functions with fallback behavior
 * - Easy integration with release cycles
 * 
 * **Usage Pattern:**
 * 1. Update WHATS_NEW_VERSION constant for new releases
 * 2. Update features array with new functionality
 * 3. Modal automatically displays to users who haven't seen this version
 * 4. User acknowledgment prevents repeated displays
 * 
 * @component
 * @example
 * ```tsx
 * const [showWhatsNew, setShowWhatsNew] = useState(!hasSeenWhatsNew());
 * 
 * <WhatsNewModal 
 *   isOpen={showWhatsNew} 
 *   onClose={() => {
 *     markWhatsNewAsSeen();
 *     setShowWhatsNew(false);
 *   }} 
 * />
 * ```
 */

import { Modal } from '../shared/Modal';
import { FaCompass, FaDesktop, FaExclamationCircle } from 'react-icons/fa';
import { FaGear } from 'react-icons/fa6';

/**
 * Props for the WhatsNewModal component
 */
interface WhatsNewModalProps {
    /** Controls whether the modal is visible */
    isOpen: boolean;
    /** Callback function called when the modal should be closed */
    onClose: () => void;
}

/**
 * Version identifier that controls when the "What's New" modal is displayed
 * 
 * **Important:** Update this value whenever you want to show the modal to users again.
 * The modal will be displayed to any user who hasn't seen this specific version.
 * 
 * **Recommended Format:** Use semantic versioning (e.g., '4.0', '4.1', '2024.01')
 * or any consistent versioning scheme that fits your release process.
 */
const WHATS_NEW_VERSION = '4.0';

/**
 * Feature announcement modal that showcases new functionality to users
 * 
 * Displays a curated list of new features with:
 * - **Visual Icons**: Each feature has a representative icon for quick recognition
 * - **Clear Descriptions**: Concise explanations of new functionality
 * - **Version Display**: Shows current version for reference
 * - **Dismissal Action**: Simple acknowledgment button to close modal
 * 
 * The modal content is designed to be easily updated for each release cycle.
 * Simply modify the features array to reflect the latest improvements.
 * 
 * @param props - Component props
 * @returns Feature announcement modal or null if not open
 */
export const WhatsNewModal: React.FC<WhatsNewModalProps> = ({ isOpen, onClose }) => {
    if (!isOpen) return null;

    /**
     * Array of new features to highlight in the current version
     * 
     * Each feature includes:
     * - **icon**: React component with distinctive visual representation
     * - **title**: Brief, memorable feature name
     * - **description**: Clear explanation of the feature's value
     * 
     * **Maintenance Note:** Update this array for each release to reflect
     * the most important user-facing improvements and new functionality.
     */
    const features = [
        {
            icon: <FaDesktop className="text-accent" />,
            title: "New UI",
            description: "The entire app has been redesigned with a fresh new look, improved navigation, and a more intuitive user experience."
        },
        {
            icon: <FaCompass className="text-accent" />,
            title: "Built in Explore Page", 
            description: "The new Explore page makes it easy to find cards with advanced search, filtering, sorting. It's brand new UI is built from the ground up for speed and usability."
        },
        {
            icon: <FaGear className="text-accent" />,
            title: "Enhanced Custom Card Builder",
            description: "The Custom Card Builder has been revamped with a new interface, built in search, and additional customization options to create your perfect card."
        }
    ];

    return (
        <Modal onClose={onClose} size='md'>
            <div className="p-6">
                {/* Header Section with Attention-Getting Icon */}
                <div className="flex items-center gap-3 mb-6">
                    <FaExclamationCircle className="w-6 h-6" />
                    <h2 className="text-2xl font-bold text-secondary">What's New</h2>
                </div>

                {/* Features List with Rich Visual Layout */}
                <div className="space-y-4 mb-6">
                    {features.map((feature, index) => (
                        <div key={index} className="flex gap-1 p-2 bg-secondary rounded-lg">
                            {/* Feature Icon */}
                            <div className="flex-shrink-0 w-10 h-10 flex items-center justify-center">
                                {feature.icon}
                            </div>
                            {/* Feature Content */}
                            <div>
                                <h3 className="font-black text-secondary mb-1">{feature.title}</h3>
                                <p className="text-sm text-secondary/80">{feature.description}</p>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Footer with Version Info and Dismissal Button */}
                <div className="flex justify-between items-center pt-4 border-t border-form-element">
                    <p className="text-sm text-secondary/60">Version {WHATS_NEW_VERSION}</p>
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-secondary text-primary font-semibold rounded-lg hover:bg-secondary/50 transition-colors cursor-pointer"
                        aria-label="Acknowledge new features and close modal"
                    >
                        Got it!
                    </button>
                </div>
            </div>
        </Modal>
    );
};

// ============================================================================
// Version Management Utilities
// ============================================================================

/** localStorage key for tracking which version the user has acknowledged */
const WHATS_NEW_STORAGE_KEY = 'showdown-bot-whats-new-seen';

/**
 * Checks if the user has already seen the current version's "What's New" modal
 * 
 * This function handles several edge cases:
 * - **SSR Safety**: Returns true (seen) when window is undefined
 * - **localStorage Errors**: Gracefully handles storage access failures
 * - **Version Comparison**: Compares stored version with current version
 * 
 * The conservative approach of returning true on errors prevents
 * annoying users with repeated modals if storage is unavailable.
 * 
 * @returns true if user has seen current version, false if modal should be shown
 * 
 * @example
 * ```tsx
 * const [showModal, setShowModal] = useState(!hasSeenWhatsNew());
 * ```
 */
export const hasSeenWhatsNew = (): boolean => {
    // SSR safety: assume seen when server-side rendering
    if (typeof window === 'undefined') return true;
    
    try {
        const seenVersion = localStorage.getItem(WHATS_NEW_STORAGE_KEY);
        return seenVersion === WHATS_NEW_VERSION;
    } catch {
        // Conservative approach: assume seen if localStorage fails
        // This prevents repeated modal displays when storage is unavailable
        return true;
    }
};

/**
 * Marks the current version as seen by the user in localStorage
 * 
 * This function should be called when the user acknowledges the modal
 * (typically in the onClose handler). Includes comprehensive error handling
 * for environments where localStorage may be restricted or unavailable.
 * 
 * **Error Handling:**
 * - Silently fails on server-side (no window object)
 * - Logs warnings for localStorage failures without breaking the app
 * - Graceful degradation ensures app continues working
 * 
 * @example
 * ```tsx
 * const handleClose = () => {
 *   markWhatsNewAsSeen();
 *   setShowModal(false);
 * };
 * ```
 */
export const markWhatsNewAsSeen = (): void => {
    // SSR safety: no-op when server-side rendering
    if (typeof window === 'undefined') return;
    
    try {
        localStorage.setItem(WHATS_NEW_STORAGE_KEY, WHATS_NEW_VERSION);
    } catch (error) {
        // Log error for debugging but don't break the application
        console.warn('Failed to save whats new state to localStorage:', error);
    }
};