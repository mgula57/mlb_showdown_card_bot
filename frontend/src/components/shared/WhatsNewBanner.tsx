import { useState } from 'react';
import { FaXmark } from 'react-icons/fa6';
import { FaUser } from 'react-icons/fa';
import { useAuth } from '../auth/AuthContext';

interface WhatsNewFeature {
    icon: React.ReactNode;
    text: string;
}

interface WhatsNewBannerProps {
    storageKey: string;
    features: WhatsNewFeature[];
    onLoginClick?: () => void;
    textSize?: 'xs' | 'sm' | 'base';
    version?: string;
}

export const WhatsNewBanner: React.FC<WhatsNewBannerProps> = ({ storageKey, features, onLoginClick, textSize = 'sm', version }) => {
    const { user } = useAuth();
    const [isVisible, setIsVisible] = useState(() => localStorage.getItem(storageKey) !== 'true');
    const calculatedWidth = textSize === 'xs' ? 'w-48' : textSize === 'sm' ? 'w-64' : 'w-72';

    if (!isVisible) return null;

    const dismiss = () => {
        localStorage.setItem(storageKey, 'true');
        setIsVisible(false);
    };

    return (
        <div className={`fixed top-12 right-3 z-50 ${calculatedWidth} rounded-card bg-(--showdown-blue) border-b-2 border-(--showdown-red) text-white shadow-overlay overflow-hidden`}>
            <div className="flex items-center justify-between px-3 pt-2.5 pb-1">
                <span className="flex items-baseline gap-1.5">
                    <span className="font-display uppercase text-base leading-none">What's New</span>
                    {version && <span className="text-[11px] font-semibold tabular-nums text-white/70">v{version}</span>}
                </span>
                <button onClick={dismiss} aria-label="Dismiss" className="text-white/70 hover:text-white transition-colors cursor-pointer -mr-0.5">
                    <FaXmark size={13} />
                </button>
            </div>

            <div className="px-3 pb-2 flex flex-col gap-2">
                {features.map(({ icon, text }) => (
                    <span key={text} className={`flex items-center gap-1.5 text-${textSize} leading-tight text-white/90`}>
                        <span className="opacity-75">{icon}</span> {text}
                    </span>
                ))}
            </div>

            {!user && onLoginClick && (
                <div className="px-3 pb-3 pt-1 border-t border-white/20">
                    <button
                        onClick={onLoginClick}
                        className="w-full mt-1.5 flex items-center justify-center gap-1.5 bg-white/15 hover:bg-white/25 transition-colors rounded-control py-1.5 text-xs font-semibold cursor-pointer"
                    >
                        <FaUser size={10} /> Sign in to get started
                    </button>
                </div>
            )}
        </div>
    );
};
