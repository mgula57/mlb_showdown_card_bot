/**
 * @fileoverview ToastMessage Component
 *
 * The app's one toast: a status message pinned top-right (building a card, a login, a saved
 * filter). A flat panel with an overlay shadow and a 3px edge in the tone's color (see
 * frontend/DESIGN.md), sliding in and out.
 */

import React from 'react';

/** `loading`: work in progress; `success`, `error`: the outcome; `neutral`: a quiet notice. */
export type ToastTone = 'loading' | 'success' | 'error' | 'neutral';

export type ToastStatus = {
    message: string;
    subMessage?: string;
    icon?: React.ReactNode;
    tone?: ToastTone;
    /** Read by the caller's dismiss timer. */
    removeAfterSeconds?: number;
};

const TONE_CLASSES: Record<ToastTone, { edge: string; icon: string }> = {
    loading: { edge: 'border-l-(--showdown-blue)', icon: 'text-(--showdown-blue)' },
    success: { edge: 'border-l-(--success)', icon: 'text-(--success)' },
    error: { edge: 'border-l-(--error)', icon: 'text-(--error)' },
    neutral: { edge: 'border-l-(--rule-strong)', icon: 'text-(--text-tertiary)' },
};

interface ToastMessageProps {
    loadingStatus: ToastStatus | null;
    /** Whether the toast is currently exiting (plays the slide-out) */
    isExiting?: boolean;
}

export const ToastMessage: React.FC<ToastMessageProps> = ({ loadingStatus, isExiting = false }) => {
    if (!loadingStatus) return null;
    const tone = TONE_CLASSES[loadingStatus.tone ?? 'success'];

    return (
        <div
            role="status"
            className={`
                fixed top-15 right-5 z-50 max-w-56 px-4 py-3 text-sm
                rounded-card border border-(--divider) border-l-3 ${tone.edge}
                bg-(--background-secondary) text-(--text-primary) shadow-overlay
                ${isExiting ? 'slide-out' : 'slide-in'}
            `}
        >
            <div className="flex flex-col gap-1 items-center">
                <div className="flex items-center gap-1.5">
                    {loadingStatus.icon && <span className={tone.icon}>{loadingStatus.icon}</span>}
                    <b className="font-bold">{loadingStatus.message}</b>
                </div>
                {loadingStatus.subMessage && (
                    <span className="text-xs text-(--text-secondary) capitalize">
                        {loadingStatus.subMessage}
                    </span>
                )}
            </div>
        </div>
    );
};
