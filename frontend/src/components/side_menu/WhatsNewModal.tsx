import { Modal } from '../shared/Modal';
import { FaCompass, FaDesktop, FaExclamationCircle } from 'react-icons/fa';
import { FaGear } from 'react-icons/fa6';

interface WhatsNewModalProps {
    isOpen: boolean;
    onClose: () => void;
}

// Update this version number whenever you want to show the modal again
const WHATS_NEW_VERSION = '4.0'; // Format: YYYY.MM or any versioning scheme

export const WhatsNewModal: React.FC<WhatsNewModalProps> = ({ isOpen, onClose }) => {
    if (!isOpen) return null;

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
                {/* Header */}
                <div className="flex items-center gap-3 mb-6">
                    <FaExclamationCircle className="w-6 h-6" />
                    <h2 className="text-2xl font-bold text-secondary">What's New</h2>
                </div>

                {/* Features List */}
                <div className="space-y-4 mb-6">
                    {features.map((feature, index) => (
                        <div key={index} className="flex gap-1 p-2 bg-secondary rounded-lg">
                            <div className="flex-shrink-0 w-10 h-10 flex items-center justify-center">
                                {feature.icon}
                            </div>
                            <div>
                                <h3 className="font-black text-secondary mb-1">{feature.title}</h3>
                                <p className="text-sm text-secondary/80">{feature.description}</p>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Footer */}
                <div className="flex justify-between items-center pt-4 border-t border-form-element">
                    <p className="text-sm text-secondary/60">Version {WHATS_NEW_VERSION}</p>
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-secondary text-primary font-semibold rounded-lg hover:bg-secondary/50 transition-colors cursor-pointer"
                    >
                        Got it!
                    </button>
                </div>
            </div>
        </Modal>
    );
};

// Helper functions for localStorage management
const WHATS_NEW_STORAGE_KEY = 'showdown-bot-whats-new-seen';

export const hasSeenWhatsNew = (): boolean => {
    if (typeof window === 'undefined') return true;
    
    try {
        const seenVersion = localStorage.getItem(WHATS_NEW_STORAGE_KEY);
        return seenVersion === WHATS_NEW_VERSION;
    } catch {
        return true; // Assume seen if localStorage fails
    }
};

export const markWhatsNewAsSeen = (): void => {
    if (typeof window === 'undefined') return;
    
    try {
        localStorage.setItem(WHATS_NEW_STORAGE_KEY, WHATS_NEW_VERSION);
    } catch (error) {
        console.warn('Failed to save whats new state to localStorage:', error);
    }
};