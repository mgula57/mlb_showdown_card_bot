/**
 * @fileoverview LoadingStatusToast Component
 * 
 * Reusable toast notification component for displaying status messages
 * with optional icons, custom background colors, and auto-dismiss functionality.
 * 
 * **Features:**
 * - Fixed position top-right corner notification
 * - Custom background color support
 * - Optional icon display
 * - Message and optional submessage
 * - Smooth slide-in/slide-out animations
 * - Auto-dismiss after configurable duration
 * 
 * @component
 * @example
 * ```tsx
 * <LoadingStatusToast
 *   loadingStatus={{
 *     message: 'Loading...',
 *     subMessage: 'Please wait',
 *     icon: <FaSpinner className="animate-spin" />,
 *     backgroundColor: 'rgb(59, 130, 246)',
 *     removeAfterSeconds: 3
 *   }}
 *   isExiting={false}
 * />
 * ```
 */

import React from 'react';

/**
 * Props for LoadingStatusToast component
 */
interface LoadingStatusToastProps {
    /** Loading status object with message and styling */
    loadingStatus: {
        /** Primary message to display */
        message: string;
        /** Optional secondary message */
        subMessage?: string;
        /** Optional React icon component */
        icon?: React.ReactNode;
        /** Custom background color (CSS color value) */
        backgroundColor?: string;
        /** Duration before auto-dismiss in seconds */
        removeAfterSeconds?: number;
    } | null;
    /** Whether the toast is exiting (for animation) */
    isExiting?: boolean;
}

/**
 * Toast notification component for displaying status messages
 * 
 * Displays a fixed-position notification in the top-right corner with
 * optional icon, custom background color, and auto-dismiss functionality.
 * Supports smooth slide animations for entry and exit.
 * 
 * @param props - Component props
 * @returns Toast notification element or null if no status
 */
export const LoadingStatusToast: React.FC<LoadingStatusToastProps> = ({
    loadingStatus,
    isExiting = false
}) => {
    // Return nothing if there's no status to display
    if (!loadingStatus) return null;

    return (
        <div
            className={`
                fixed top-15 right-5 z-50 rounded-xl px-4 py-3 text-sm
                text-black shadow-xl
                max-w-56
                ${isExiting 
                    ? 'slide-out' 
                    : 'slide-in'
                }
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
