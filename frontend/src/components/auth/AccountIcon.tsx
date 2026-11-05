import React, { useState, useRef, useEffect } from 'react';
import { FaUserCircle, FaSignOutAlt, FaSpinner, FaCog } from 'react-icons/fa';
import { FaCircleCheck } from 'react-icons/fa6';
import { useAuth } from './AuthContext';
import { useNavigate } from 'react-router-dom';
import { ToastMessage } from '../shared/ToastMessage';
import { UserAvatar } from '../shared/UserAvatar';
import { Heading } from '../shared/Heading';

// ---------------------------------------------------------------------------
// AccountAvatar — reusable avatar image / initials / fallback icon
// ---------------------------------------------------------------------------

interface AccountAvatarProps {
    className?: string;
    /** Diameter in Tailwind spacing units (9 = 36px) */
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
    const px = size * 4;

    return (
        <div className={`relative inline-flex ${className}`}>
            <button
                type="button"
                onClick={onClick}
                style={{ width: px, height: px }}
                className={`
                    flex items-center justify-center rounded-full
                    transition-colors duration-200 cursor-pointer
                    ${user
                        ? 'border-2 border-transparent hover:border-(--showdown-blue)'
                        : 'border-2 border-(--tertiary) hover:border-(--rule-strong) opacity-60 hover:opacity-100'
                    }
                `}
                aria-label={label ?? (user ? (username || 'Account') : 'Sign in')}
            >
                {user ? (
                    <UserAvatar
                        name={username || user.email}
                        avatarUrl={userSettings?.avatar_url}
                        primaryColor={userSettings?.default_primary_color}
                        size={px - 4}
                    />
                ) : (
                    <FaUserCircle className="w-full h-full text-secondary" />
                )}
            </button>

            {user && showStatus && (
                <span className="
                    absolute bottom-0 right-0
                    w-2 h-2
                    bg-(--green)
                    rounded-full
                    ring-2 ring-(--background-primary)
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
    size = 8,
    onLoginClick,
    showStatus = true,
}) => {
    const { user, signOut, username } = useAuth();
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
        <div className={`relative z-50 flex items-center ${className}`} ref={dropdownRef}>
            <AccountAvatar
                size={size}
                showStatus={showStatus}
                onClick={handleAvatarClick}
                label={user ? 'Open account menu' : 'Sign in'}
            />

            <ToastMessage
                loadingStatus={hasSignedOut ? {
                    message: 'Signed out',
                    icon: <FaCircleCheck className="w-5 h-5" />,
                    tone: 'success',
                    removeAfterSeconds: 3,
                } : null}
                isExiting={isSignOutExiting}
            />

            {user && isDropdownOpen && (
                <div className="
                    absolute right-0 top-full mt-2
                    w-72 py-2
                    bg-(--background-secondary)
                    border border-form-element
                    rounded-card shadow-overlay
                    z-50
                    animate-fade-in
                ">
                    <div className='flex space-x-3 px-2 py-3 border-b border-form-element'>
                        <AccountAvatar size={10} showStatus={false} />
                        <div>
                            <Heading level="panel" as="div" className="truncate">{username}</Heading>
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
                            <span>Account settings</span>
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
