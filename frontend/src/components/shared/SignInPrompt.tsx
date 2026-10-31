import React, { useState } from 'react';
import { buttonClass } from './buttonStyles';
import { FaLock } from 'react-icons/fa';
import { LoginModal } from '../auth/LoginModal';

import { Heading } from './Heading';
import { EmptyState } from './EmptyState';

interface SignInPromptProps {
    /** Icon to display above the message. Defaults to FaLock. */
    icon?: React.ReactNode;
    /** Heading text. Defaults to "Sign in required". */
    title?: string;
    /** Supporting description text. */
    message?: string;
    /** Additional CSS classes for the wrapper (e.g. sizing / spacing). */
    className?: string;
    /** `page` (default) is the full-screen lock prompt; `panel` is a compact bordered panel for one gated part of a screen. */
    size?: 'page' | 'panel';
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
    size = 'page',
}) => {
    const [showLoginModal, setShowLoginModal] = useState(false);

    const loginModal = showLoginModal && <LoginModal onClose={() => setShowLoginModal(false)} />;

    if (size === 'panel') {
        return (
            <>
                <EmptyState
                    size="panel"
                    title={title}
                    className={`rounded-card border border-(--divider) bg-(--background-secondary) ${className}`}
                    action={
                        <button type="button" onClick={() => setShowLoginModal(true)} className={`${buttonClass('primary')} cursor-pointer`}>
                            Sign in / Sign up
                        </button>
                    }
                >
                    {message}
                </EmptyState>
                {loginModal}
            </>
        );
    }

    return (
        <div className={`flex flex-col items-center justify-center gap-4 text-center px-6 ${className}`}>
            <div className="text-secondary opacity-40">
                {icon ?? <FaLock size={36} />}
            </div>

            <div className="flex flex-col gap-1">
                <Heading level="section">{title}</Heading>
                {message && <p className="text-sm text-secondary">{message}</p>}
            </div>

            <button
                onClick={() => setShowLoginModal(true)}
                className={buttonClass('primary')}
            >
                Sign in / Sign up
            </button>

            {loginModal}
        </div>
    );
};
