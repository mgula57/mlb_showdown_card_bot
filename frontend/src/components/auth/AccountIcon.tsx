import React, { useState, useRef, useEffect } from 'react';
import { FaUserCircle, FaSignOutAlt, FaSpinner, FaCog } from 'react-icons/fa';
import { FaCircleCheck } from 'react-icons/fa6';
import { useAuth } from './AuthContext';
import { useNavigate } from 'react-router-dom';
import { LoadingStatusToast } from '../shared/LoadingStatusToast';

// ---------------------------------------------------------------------------
// AccountAvatar — reusable avatar image / initials / fallback icon
// ---------------------------------------------------------------------------

interface AccountAvatarProps {
    className?: string;
    /** Button size in Tailwind units (applied as w-{size} h-{size}) */
    size?: number;
    showStatus?: boolean;
    onClick?: () => void;
    /** aria-label for the button */
    label?: string;
}

export const AccountAvatar: React.FC<AccountAvatarProps> = ({
    className = '',
    size = 9,
    showStatus = false,
    onClick,
    label,
}) => {
    const { user, username, userSettings } = useAuth();

    const getUserInitials = () => {
        if (!user) return '';
        const nameSource = username || user.email || '';
        const nameParts = nameSource.split(/[@._-]/).filter(Boolean);
        return nameParts.map(part => part[0].toUpperCase()).join('').slice(0, 2);
    };

    return (
        <div className={`relative inline-flex ${className}`}>
            <button
                onClick={onClick}
                style={user && !userSettings?.avatar_url ? { background: 'linear-gradient(to right, #3b82f6 15%, #ef4444 85%)' } : undefined}
                className={`
                    flex items-center justify-center
                    w-${size} h-${size} rounded-full
                    transition-colors duration-200
                    cursor-pointer
                    ${user
                        ? userSettings?.avatar_url
                            ? 'border-2 bg-transparent border-transparent hover:border-indigo-400 overflow-hidden'
                            : 'border-0'
                        : 'border-2 bg-transparent border-(--tertiary) hover:border-secondary opacity-60 hover:opacity-100'
                    }
                `}
                aria-label={label ?? (user ? (username || 'Account') : 'Sign in')}
            >
                {user ? (
                    userSettings?.avatar_url ? (
                        <img
                            src={userSettings.avatar_url}
                            alt="avatar"
                            className="w-full h-full rounded-full object-cover"
                        />
                    ) : (
                        <span
                            className="font-semibold text-white select-none"
                            style={{ fontSize: `${Math.round(size * 6 * 0.35)}px` }}
                        >
                            {getUserInitials()}
                        </span>
                    )
                ) : (
                    <FaUserCircle className="w-8 h-8 text-secondary" />
                )}
            </button>

            {user && showStatus && (
                <span className="
                    absolute bottom-0 right-0
                    w-2 h-2
                    bg-green-500
                    rounded-full
                    ring-2 ring-primary
                    pointer-events-none
                " />
            )}
        </div>
    );
};

// ---------------------------------------------------------------------------
// AccountIcon — header-specific: avatar + dropdown + sign-out toast
// ---------------------------------------------------------------------------

interface AccountIconProps {
    className?: string;
    onLoginClick?: () => void;
    showStatus?: boolean;
    size?: number;
}

export const AccountIcon: React.FC<AccountIconProps> = ({
    className = '',
    size = 9,
    onLoginClick,
    showStatus = true,
}) => {
    const { user, signOut, username, userSettings } = useAuth();
    const navigate = useNavigate();
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [hasSignedOut, setHasSignedOut] = useState(false);
    const [isSignOutExiting, setIsSignOutExiting] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsDropdownOpen(false);
            }
        };
        if (isDropdownOpen) document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [isDropdownOpen]);

    const handleAvatarClick = () => {
        if (user) {
            setIsDropdownOpen(prev => !prev);
        } else {
            onLoginClick?.();
        }
    };

    const handleSignOut = async () => {
        setIsProcessing(true);
        await signOut();
        setIsProcessing(false);
        setIsDropdownOpen(false);
        setHasSignedOut(true);
        setTimeout(() => {
            setIsSignOutExiting(true);
            setTimeout(() => setHasSignedOut(false), 300);
        }, 3000);
    };

    return (
        <div className={`relative z-50 ${className}`} ref={dropdownRef}>
            <AccountAvatar
                size={size}
                showStatus={showStatus}
                onClick={handleAvatarClick}
                label={user ? 'Open account menu' : 'Sign in'}
            />

            <LoadingStatusToast
                loadingStatus={hasSignedOut ? {
                    message: 'Logged Out!',
                    icon: <FaCircleCheck className="w-5 h-5" />,
                    backgroundColor: 'rgb(34, 197, 94)',
                    removeAfterSeconds: 3,
                } : null}
                isExiting={isSignOutExiting}
            />

            {user && isDropdownOpen && (
                <div className="
                    absolute right-0 mt-2
                    w-72 py-2
                    bg-(--background-secondary)
                    border border-form-element
                    rounded-lg shadow-xl
                    z-50
                    animate-fade-in
                ">
                    <div className='flex space-x-3 px-2 py-3 border-b border-form-element'>
                        <AccountAvatar size={10} showStatus={false} />
                        <div>
                            <p className="text-md font-bold text-primary truncate">{username}</p>
                            <p className="text-[11px] text-secondary truncate">{user.email}</p>
                        </div>
                    </div>

                    <div className="py-1">
                        <button
                            onClick={() => { setIsDropdownOpen(false); navigate('/account'); }}
                            className="
                                w-full px-4 py-2
                                text-left text-sm text-secondary
                                hover:bg-(--background-quaternary)
                                cursor-pointer transition-colors duration-150
                                flex items-center space-x-2
                            "
                        >
                            <FaCog className="w-4 h-4" />
                            <span>Account Settings</span>
                        </button>
                        <button
                            onClick={handleSignOut}
                            disabled={isProcessing}
                            className="
                                w-full px-4 py-2
                                text-left text-sm text-secondary
                                hover:bg-(--background-quaternary)
                                cursor-pointer transition-colors duration-150
                                flex items-center space-x-2
                            "
                        >
                            <FaSignOutAlt className="w-4 h-4" />
                            {isProcessing && <FaSpinner className="w-4 h-4 animate-spin" />}
                            <span>Sign out</span>
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};
