/**
 * @fileoverview ToastMessage Component
 * 
 * A toast notification component for displaying loading status, success, and error messages.
 * Displays at the top-right corner with custom background colors and icons.
 * 
 * **Features:**
 * - Animated slide-in/slide-out transitions
 * - Customizable background color
 * - Optional submessage
 * - Icon support
 * - Auto-dismiss after configurable duration
 * 
 * @component
 */

import React from 'react';

/**
 * Props for ToastMessage component
 */
interface ToastMessageProps {
    /** Status content to display */
    loadingStatus: {
        message: string;
        subMessage?: string;
        icon?: React.ReactNode;
        backgroundColor?: string;
        removeAfterSeconds?: number;
    } | null;
    /** Whether the toast is currently exiting */
    isExiting?: boolean;
}

/**
 * Loading Status Toast Component
 * 
 * Displays a floating toast notification in the top-right corner with
 * loading, success, or error status. Supports custom icons, colors, and messages.
 * 
 * @param props - Component props
 * @returns Toast notification element
 */
export const ToastMessage: React.FC<ToastMessageProps> = ({ 
    loadingStatus, 
    isExiting = false 
}) => {
    if (!loadingStatus) return null;

    return (
        <div
            className={`
                fixed top-15 right-5 z-50 rounded-xl px-4 py-3 text-sm
                text-black shadow-xl
                max-w-56
                ${isExiting ? 'slide-out' : 'slide-in'}
            `}
            style={{
                backgroundColor: loadingStatus.backgroundColor || 'rgb(255, 193, 7)', // Default Amber
            }}
        >
            <button className="flex flex-col gap-1 items-center">
                <div className='flex items-center gap-1'>
                    {loadingStatus.icon}
                    <b className='inline font-bold'>{loadingStatus.message}</b>
                </div>
                {loadingStatus.subMessage && (
                    <span className='text-xs' style={{ textTransform: 'capitalize' }}>
                        {loadingStatus.subMessage}
                    </span>
                )}
            </button>
        </div>
    );
};
