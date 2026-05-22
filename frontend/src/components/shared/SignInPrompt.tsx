import React, { useState } from 'react';
import { FaLock } from 'react-icons/fa';
import { LoginModal } from '../auth/LoginModal';

interface SignInPromptProps {
    /** Icon to display above the message. Defaults to FaLock. */
    icon?: React.ReactNode;
    /** Heading text. Defaults to "Sign in required". */
    title?: string;
    /** Supporting description text. */
    message?: string;
    /** Additional CSS classes for the wrapper (e.g. sizing / spacing). */
    className?: string;
}

/**
 * Reusable empty-state prompt shown when a feature requires authentication.
 * Manages its own LoginModal state so callers don't need to.
 */
export const SignInPrompt: React.FC<SignInPromptProps> = ({
    icon,
    title = 'Sign in required',
    message,
    className = '',
}) => {
    const [showLoginModal, setShowLoginModal] = useState(false);

    return (
        <div className={`flex flex-col items-center justify-center gap-4 text-center px-6 ${className}`}>
            <div className="text-secondary opacity-40">
                {icon ?? <FaLock size={36} />}
            </div>

            <div className="flex flex-col gap-1">
                <h2 className="text-lg font-bold text-primary">{title}</h2>
                {message && <p className="text-sm text-secondary">{message}</p>}
            </div>

            <button
                onClick={() => setShowLoginModal(true)}
                className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold transition-colors cursor-pointer"
            >
                Sign in / Sign up
            </button>

            {showLoginModal && (
                <LoginModal onClose={() => setShowLoginModal(false)} />
            )}
        </div>
    );
};
