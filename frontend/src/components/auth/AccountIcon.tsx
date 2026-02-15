/**
 * @fileoverview AccountIcon Component
 * 
 * Displays a circular user account icon in the header with login/logout functionality.
 * Shows different states based on authentication status:
 * - Logged out: Generic user icon that opens login modal
 * - Logged in: User avatar with dropdown menu for account actions
 * 
 * **Features:**
 * - Circular avatar display
 * - Dropdown menu with user info and sign out
 * - Click outside to close dropdown
 * - Smooth animations
 * 
 * @component
 */

import React, { useState, useRef, useEffect } from 'react';
import { FaUserCircle, FaSignOutAlt, FaSpinner, FaCog } from 'react-icons/fa';
import { FaCircleCheck } from 'react-icons/fa6';
import { useAuth } from './AuthContext';
import { useNavigate } from 'react-router-dom';
import { LoadingStatusToast } from '../shared/LoadingStatusToast';

/**
 * Props for AccountIcon component
 */
interface AccountIconProps {
    /** Optional CSS class name */
    className?: string;
    /** Callback when login is requested */
    onLoginClick: () => void;
}

/**
 * Account Icon Component
 * 
 * Displays user account status and provides access to authentication actions.
 * When logged out, shows a generic icon that opens the login modal.
 * When logged in, shows user avatar with dropdown menu.
 * 
 * @param props - Component props
 * @returns Account icon with dropdown functionality
 */
export const AccountIcon: React.FC<AccountIconProps> = ({ className = '', onLoginClick }) => {
    const { user, signOut, username } = useAuth();
    const navigate = useNavigate();
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [hasSignedOut, setHasSignedOut] = useState(false);
    const [isSignOutExiting, setIsSignOutExiting] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    /**
     * Close dropdown when clicking outside
     */
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsDropdownOpen(false);
            }
        };

        if (isDropdownOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isDropdownOpen]);

    /**
     * Handle icon click
     */
    const handleIconClick = () => {
        if (user) {
            setIsDropdownOpen(!isDropdownOpen);
        } else {
            onLoginClick();
        }
    };

    /**
     * Handle sign out
     */
    const handleSignOut = async () => {
        setIsProcessing(true);
        await signOut();
        setIsProcessing(false);
        setIsDropdownOpen(false);

        setHasSignedOut(true);

        // Reset sign out toast after it exits
        setTimeout(() => {
            setIsSignOutExiting(true);
            setTimeout(() => {
                setHasSignedOut(false);
            }, 300); // Match the toast exit animation duration
        }, 3000); // Match the toast duration
    };

    /**
     * Get user initials for avatar
     * Uses username or email to generate initials (e.g. "John Doe" -> "JD")
     */
    const getUserInitials = () => {
        if (!user) return '';

        const nameSource = username || user.email || '';
        const nameParts = nameSource.split(/[@._-]/).filter(Boolean);
        const initials = nameParts.map(part => part[0].toUpperCase()).join('');
        return initials.slice(0, 2); // Limit to 2 characters
    };

    return (
        <div className={`relative ${className}`} ref={dropdownRef}>
            {/* Account Icon/Avatar */}
            <button
                onClick={handleIconClick}
                className="
                    flex items-center justify-center
                    w-8 h-8 rounded-full
                    text-primary
                    transition-colors duration-200
                    cursor-pointer
                    border-2 border-(--tertiary)
                "
                aria-label={user ? 'Open account menu' : 'Sign in'}
                title={user ? 'Account' : 'Sign in'}
            >
                {user ? (
                    // Logged in: Show initials or avatar
                    <span className="font-semibold text-lg">
                        {getUserInitials()}
                    </span>
                ) : (
                    // Logged out: Show generic user icon with sign-in text
                    <FaUserCircle className="w-8 h-8 text-secondary" />
                )}
            </button>

            <LoadingStatusToast
                loadingStatus={hasSignedOut ? {
                    message: 'Logged Out!',
                    icon: <FaCircleCheck className="w-5 h-5" />,
                    backgroundColor: 'rgb(34, 197, 94)', // green-500
                    removeAfterSeconds: 3
                } : null}
                isExiting={isSignOutExiting}
            />

            {/* Dropdown Menu (only shown when logged in) */}
            {user && isDropdownOpen && (
                <div className="
                    absolute right-0 mt-2
                    w-64 py-2
                    bg-(--background-secondary)
                    border border-form-element
                    rounded-lg shadow-xl
                    z-50
                    animate-fade-in
                ">
                    {/* User Info Section */}
                    <div className="px-4 py-3 border-b border-form-element">
                        <p className="text-sm text-secondary truncate">
                            {user.email}
                        </p>
                    </div>

                    {/* Actions Section */}
                    <div className="py-1">
                        <button
                            onClick={() => {
                                setIsDropdownOpen(false);
                                navigate('/account');
                            }}
                            className="
                                w-full px-4 py-2
                                text-left text-sm text-secondary
                                hover:bg-(--background-quaternary)
                                cursor-pointer
                                transition-colors duration-150
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
                                cursor-pointer
                                transition-colors duration-150
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
