/**
 * @fileoverview Account Page Component
 * 
 * User account management page displaying user information and application settings.
 * Provides interfaces for:
 * - Viewing account details (email, join date)
 * - Managing account settings (future: email preferences, notifications)
 * - Application preferences (theme, default set)
 * - Account actions (sign out, delete account)
 * 
 * **Features:**
 * - User profile information display
 * - Settings management
 * - Theme preference controls
 * - Account management actions
 * 
 * @component
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useSiteSettings, useTheme, showdownSets } from '../shared/SiteSettingsContext';
import { FaEnvelope, FaClock, FaPalette, FaSignOutAlt, FaTrash, FaCog } from 'react-icons/fa';
import CustomSelect from '../shared/CustomSelect';

/**
 * Account Page Component
 * 
 * Main account management interface where authenticated users can:
 * - View their profile information
 * - Manage application settings
 * - Control theme preferences
 * - Sign out or delete their account
 * 
 * @returns Account page with user information and settings
 */
const AccountPage: React.FC = () => {
    const { user, signOut, loading } = useAuth();
    const navigate = useNavigate();
    const { isDark, setTheme, theme } = useTheme();
    const { userShowdownSet, setUserShowdownSet } = useSiteSettings();
    const [isSigningOut, setIsSigningOut] = useState(false);

    // Redirect to home if not authenticated
    useEffect(() => {
        if (!loading && !user) {
            navigate('/');
        }
    }, [user, loading, navigate]);

    // Loading state
    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-secondary text-xl">Loading...</div>
            </div>
        );
    }

    // Not authenticated (shouldn't reach here due to useEffect redirect)
    if (!user) {
        return null;
    }

    /**
     * Handle sign out action
     */
    const handleSignOut = async () => {
        setIsSigningOut(true);
        await signOut();
        navigate('/');
    };

    /**
     * Format date for display
     */
    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    /**
     * Get user initials for avatar
     */
    const getUserInitials = () => {
        if (!user?.email) return '?';
        const email = user.email;
        const parts = email.split('@')[0].split('.');
        if (parts.length > 1) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return email.substring(0, 2).toUpperCase();
    };

    return (
        <div className="min-h-screen bg-primary p-4 md:p-8">
            <div className="max-w-4xl mx-auto space-y-6">
                
                {/* Page Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-secondary mb-2">Account Settings</h1>
                    <p className="text-gray-500">Manage your account information and preferences</p>
                </div>

                {/* User Profile Card */}
                <div className={`rounded-lg border border-form-element p-6 ${isDark ? 'bg-background-secondary' : 'bg-white'}`}>
                    <div className="flex items-start space-x-4">
                        {/* Avatar */}
                        <div className="shrink-0">
                            <div className="
                                w-20 h-20 rounded-full
                                bg-accent text-primary
                                flex items-center justify-center
                                text-2xl font-bold
                                border-2 border-accent-dark
                            ">
                                {getUserInitials()}
                            </div>
                        </div>

                        {/* User Info */}
                        <div className="flex-1">                            
                            <div className="space-y-3">
                                {/* Email */}
                                <div className="flex items-center space-x-3">
                                    <FaEnvelope className="text-gray-500 shrink-0" />
                                    <div>
                                        <p className="text-sm text-gray-500">Email</p>
                                        <p className="text-secondary font-medium">{user.email}</p>
                                    </div>
                                </div>

                                {/* Account Created */}
                                <div className="flex items-center space-x-3">
                                    <FaClock className="text-gray-500 shrink-0" />
                                    <div>
                                        <p className="text-sm text-gray-500">Member Since</p>
                                        <p className="text-secondary font-medium">
                                            {user.created_at ? formatDate(user.created_at) : 'Unknown'}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Application Settings */}
                <div className={`rounded-lg border border-form-element p-6 ${isDark ? 'bg-background-secondary' : 'bg-white'}`}>
                    <div className="flex items-center space-x-2 mb-4">
                        <FaCog className="text-secondary" />
                        <h2 className="text-2xl font-semibold text-secondary">Application Settings</h2>
                    </div>

                    <div className="space-y-6">
                        {/* Theme Setting */}
                        <div>
                            <div className="flex items-center space-x-2 mb-2">
                                <FaPalette className="text-gray-500" />
                                <label className="text-sm font-medium text-secondary">Theme</label>
                            </div>
                            <div className="flex space-x-3">
                                <button
                                    onClick={() => setTheme('light')}
                                    className={`
                                        px-4 py-2 rounded-lg border
                                        transition-colors duration-150
                                        ${theme === 'light'
                                            ? 'bg-accent text-primary border-accent-dark font-semibold'
                                            : 'bg-background-primary text-secondary border-form-element hover:bg-background-tertiary'
                                        }
                                    `}
                                >
                                    Light
                                </button>
                                <button
                                    onClick={() => setTheme('dark')}
                                    className={`
                                        px-4 py-2 rounded-lg border
                                        transition-colors duration-150
                                        ${theme === 'dark'
                                            ? 'bg-accent text-primary border-accent-dark font-semibold'
                                            : 'bg-background-primary text-secondary border-form-element hover:bg-background-tertiary'
                                        }
                                    `}
                                >
                                    Dark
                                </button>
                                <button
                                    onClick={() => setTheme('system')}
                                    className={`
                                        px-4 py-2 rounded-lg border
                                        transition-colors duration-150
                                        ${theme === 'system'
                                            ? 'bg-accent text-primary border-accent-dark font-semibold'
                                            : 'bg-background-primary text-secondary border-form-element hover:bg-background-tertiary'
                                        }
                                    `}
                                >
                                    System
                                </button>
                            </div>
                            <p className="text-xs text-gray-500 mt-2">
                                Choose how the application appears to you
                            </p>
                        </div>

                        {/* Default Showdown Set */}
                        <div>
                            <CustomSelect
                                className="font-showdown-set-italic w-20 text-xl"
                                buttonClassName="flex justify-center cursor-pointer select-none p-2 rounded-lg border"
                                imageClassName="object-contain object-center"
                                value={userShowdownSet}
                                onChange={setUserShowdownSet}
                                options={showdownSets}
                            />
                            
                            <p className="text-xs text-gray-500 mt-2">
                                Your preferred Showdown set for card generation
                            </p>
                        </div>
                    </div>
                </div>

                {/* Account Actions */}
                <div className={`rounded-lg border border-form-element p-6 ${isDark ? 'bg-background-secondary' : 'bg-white'}`}>
                    <h2 className="text-2xl font-semibold text-secondary mb-4">Account Actions</h2>
                    
                    <div className="space-y-3">
                        {/* Sign Out Button */}
                        <button
                            onClick={handleSignOut}
                            disabled={isSigningOut}
                            className="
                                w-full md:w-auto
                                flex items-center justify-center space-x-2
                                px-6 py-3
                                bg-gray-600 text-white
                                rounded-lg
                                hover:bg-gray-700
                                disabled:opacity-50 disabled:cursor-not-allowed
                                transition-colors duration-150
                                font-medium
                            "
                        >
                            <FaSignOutAlt />
                            <span>{isSigningOut ? 'Signing Out...' : 'Sign Out'}</span>
                        </button>

                        {/* Delete Account Button (placeholder for future implementation) */}
                        <button
                            disabled
                            className="
                                w-full md:w-auto
                                flex items-center justify-center space-x-2
                                px-6 py-3
                                bg-red-600/50 text-white
                                rounded-lg
                                cursor-not-allowed
                                opacity-50
                                font-medium
                            "
                            title="Account deletion coming soon"
                        >
                            <FaTrash />
                            <span>Delete Account</span>
                        </button>
                        <p className="text-xs text-gray-500">
                            Account deletion will be available in a future update
                        </p>
                    </div>
                </div>

                {/* Footer Info */}
                <div className="text-center text-sm text-gray-500 py-4">
                    <p>Your data is securely stored and managed through Supabase</p>
                </div>
            </div>
        </div>
    );
};

export default AccountPage;
