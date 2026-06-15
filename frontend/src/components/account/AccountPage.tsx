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

import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../auth/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useSiteSettings, useTheme, showdownSets } from '../shared/SiteSettingsContext';
import { FaEnvelope, FaClock, FaPalette, FaSignOutAlt, FaTrash, FaCog, FaUser, FaCamera, FaSpinner } from 'react-icons/fa';
import { SignInPrompt } from '../shared/SignInPrompt';
import CustomSelect from '../shared/CustomSelect';
import { uploadAvatar, removeAvatar, validateAvatarFile } from '../../api/userAvatar';
import AvatarCropModal from './AvatarCropModal';
import { AccountAvatar } from '../auth/AccountIcon';

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
    const { user, signOut, loading, username, updateUsername, checkUsernameAvailability, userSettings, syncSetting } = useAuth();
    const navigate = useNavigate();
    const { isDark, setTheme, theme } = useTheme();
    const { userShowdownSet, setUserShowdownSet } = useSiteSettings();
    const [isSigningOut, setIsSigningOut] = useState(false);
    const [isEditingUsername, setIsEditingUsername] = useState(false);
    const [newUsername, setNewUsername] = useState('');
    const [usernameError, setUsernameError] = useState<string | null>(null);
    const [isCheckingUsername, setIsCheckingUsername] = useState(false);
    const [isSavingUsername, setIsSavingUsername] = useState(false);
    const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
    const [avatarError, setAvatarError] = useState<string | null>(null);
    const [cropSrc, setCropSrc] = useState<string | null>(null);
    const avatarInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (!isEditingUsername) {
            setNewUsername(username ?? '');
            setUsernameError(null);
        }
    }, [username, isEditingUsername]);

    // Loading state
    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-secondary text-xl">Loading...</div>
            </div>
        );
    }

    if (!user) {
        return (
            <SignInPrompt
                title="Sign in to view your account"
                message="Create an account to save cards, track your gallery, and manage settings."
                className="min-h-screen"
            />
        );
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

    const validateUsername = (value: string) => {
        if (value.length < 3) return 'Username must be at least 3 characters';
        if (!/^[a-zA-Z0-9_]+$/.test(value)) {
            return 'Username can only contain letters, numbers, and underscores';
        }
        return null;
    };

    const handleCheckUsername = async (value: string) => {
        const validationError = validateUsername(value);
        if (validationError) {
            setUsernameError(validationError);
            return false;
        }

        setIsCheckingUsername(true);
        const isAvailable = await checkUsernameAvailability(value);
        setIsCheckingUsername(false);

        if (!isAvailable) {
            setUsernameError('Username is already taken');
            return false;
        }

        setUsernameError(null);
        return true;
    };

    const handleSaveUsername = async () => {
        if (newUsername === (username ?? '')) {
            setIsEditingUsername(false);
            return;
        }

        const isValid = await handleCheckUsername(newUsername);
        if (!isValid) return;

        setIsSavingUsername(true);
        const { error } = await updateUsername(newUsername);
        setIsSavingUsername(false);

        if (error) {
            setUsernameError('Failed to update username. Please try again.');
            return;
        }

        setIsEditingUsername(false);
    };

    const handleAvatarFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const validationError = validateAvatarFile(file);
        if (validationError) {
            setAvatarError(validationError);
            if (avatarInputRef.current) avatarInputRef.current.value = '';
            return;
        }
        setAvatarError(null);
        const objectUrl = URL.createObjectURL(file);
        setCropSrc(objectUrl);
        if (avatarInputRef.current) avatarInputRef.current.value = '';
    };

    const handleCropApply = async (blob: Blob) => {
        if (!user) return;
        setIsUploadingAvatar(true);
        const file = new File([blob], 'avatar.jpg', { type: 'image/jpeg' });
        const url = await uploadAvatar(file, user.id);
        setIsUploadingAvatar(false);
        if (url) {
            syncSetting({ avatar_url: url });
        } else {
            setAvatarError('Upload failed. Please try again.');
        }
        setCropSrc(null);
    };

    const handleCropCancel = () => {
        if (cropSrc) URL.revokeObjectURL(cropSrc);
        setCropSrc(null);
    };

    const handleRemoveAvatar = async () => {
        if (!user) return;
        setIsUploadingAvatar(true);
        await removeAvatar(user.id);
        setIsUploadingAvatar(false);
        syncSetting({ avatar_url: '' });
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
                            <label
                                htmlFor="avatar-upload"
                                className={`relative group block w-20 h-20 rounded-full focus-within:ring-2 focus-within:ring-accent ${isUploadingAvatar ? 'cursor-not-allowed' : 'cursor-pointer'}`}
                                title="Change profile photo"
                            >
                                <AccountAvatar
                                    showStatus={false}
                                    size={20}
                                />

                                {/* Hover overlay */}
                                <span className="
                                    absolute inset-0 rounded-full
                                    bg-black/50
                                    flex items-center justify-center
                                    opacity-0 group-hover:opacity-100
                                    transition-opacity duration-200
                                ">
                                    {isUploadingAvatar
                                        ? <FaSpinner className="w-5 h-5 text-white animate-spin" />
                                        : <FaCamera className="w-5 h-5 text-white" />
                                    }
                                </span>

                                {/* Persistent camera badge */}
                                {!isUploadingAvatar && (
                                    <span className="
                                        absolute bottom-0 right-0
                                        w-6 h-6 rounded-full
                                        bg-accent border-2 border-background-secondary
                                        flex items-center justify-center
                                        group-hover:opacity-0 transition-opacity duration-200
                                    ">
                                        <FaCamera className="w-2.5 h-2.5 text-primary" />
                                    </span>
                                )}
                            </label>

                            {/* Change photo / remove / error below avatar */}
                            <div className="mt-1.5 text-center space-y-0.5">
                                <label
                                    htmlFor="avatar-upload"
                                    className={`text-xs text-tertiary block w-full ${isUploadingAvatar ? 'cursor-not-allowed opacity-50' : 'cursor-pointer hover:underline'}`}
                                >
                                    {isUploadingAvatar ? 'Uploading…' : 'Change photo'}
                                </label>
                                {userSettings?.avatar_url && !isUploadingAvatar && (
                                    <button
                                        type="button"
                                        onClick={handleRemoveAvatar}
                                        className="text-xs text-tertiary hover:underline block w-full"
                                    >
                                        Remove
                                    </button>
                                )}
                                {avatarError && (
                                    <p className="text-xs text-red-500">{avatarError}</p>
                                )}
                            </div>

                            <input
                                ref={avatarInputRef}
                                id="avatar-upload"
                                type="file"
                                accept="image/*"
                                disabled={isUploadingAvatar}
                                className="hidden"
                                onChange={handleAvatarFileChange}
                            />
                        </div>

                        {/* User Info */}
                        <div className="flex-1">                            
                            <div className="space-y-3">

                                {/* Username */}
                                <div className="flex items-start space-x-3">
                                    <FaUser className="text-gray-500 shrink-0 mt-1" />
                                    <div className="flex-1">
                                        <div className="flex items-end gap-5">
                                            <div>
                                                <p className="text-sm text-gray-500">Username</p>
                                                <p className="text-secondary font-medium">{username ?? 'Not set'}</p>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={() => {
                                                    setIsEditingUsername(true);
                                                    setUsernameError(null);
                                                }}
                                                className="text-xs mb-1 text-tertiary hover:underline"
                                            >
                                                {username ? 'Change' : 'Set'}
                                            </button>
                                        </div>

                                        {isEditingUsername && (
                                            <div className="mt-2 space-y-2">
                                                <input
                                                    type="text"
                                                    value={newUsername}
                                                    onChange={(e) => {
                                                        setNewUsername(e.target.value);
                                                        handleCheckUsername(e.target.value);
                                                    }}
                                                    minLength={3}
                                                    pattern="[a-zA-Z0-9_]+"
                                                    className={`
                                                        w-full px-3 py-2
                                                        bg-background-primary
                                                        border rounded-lg
                                                        text-secondary
                                                        focus:outline-none focus:ring-2 focus:ring-accent
                                                        ${usernameError ? 'border-red-500' : 'border-form-element'}
                                                    `}
                                                    placeholder="e.g. brianjordangoat"
                                                />
                                                {isCheckingUsername && (
                                                    <p className="text-xs text-gray-500">Checking availability...</p>
                                                )}
                                                {usernameError && !isCheckingUsername ? (
                                                    <p className="text-xs text-red-500">{usernameError}</p>
                                                ) : (!usernameError && !isCheckingUsername ? (<p className="text-xs text-green-500">Username is available!</p>) : null)}
                                                <div className="flex items-center gap-2">
                                                    <button
                                                        type="button"
                                                        onClick={handleSaveUsername}
                                                        disabled={isSavingUsername || isCheckingUsername}
                                                        className="px-3 py-1.5 rounded-md bg-accent text-primary text-xs font-semibold disabled:opacity-50"
                                                    >
                                                        {isSavingUsername ? 'Saving...' : 'Save'}
                                                    </button>
                                                    <button
                                                        type="button"
                                                        onClick={() => setIsEditingUsername(false)}
                                                        className="px-3 py-1.5 rounded-md border border-form-element text-xs text-secondary"
                                                    >
                                                        Cancel
                                                    </button>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>

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
                                className="font-showdown-set-italic w-26 text-xl"
                                buttonClassName="flex justify-center cursor-pointer select-none p-2 rounded-lg border"
                                imageClassName="object-contain object-center w-18"
                                value={userShowdownSet}
                                onChange={setUserShowdownSet}
                                options={showdownSets}
                                showDropdownArrow={true}
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
                            Account deletion will be available in a future update. 
                            If you need account assistance please email <a href="mailto:mlbshowdownbot@gmail.com" className="text-tertiary hover:underline">mlbshowdownbot@gmail.com</a>.
                        </p>
                    </div>
                </div>

                {/* Footer Info */}
                <div className="text-center text-sm text-gray-500 py-4">
                    <p>Your data is securely stored and managed through Supabase</p>
                </div>
            </div>

            {cropSrc && (
                <AvatarCropModal
                    imageSrc={cropSrc}
                    onApply={handleCropApply}
                    onCancel={handleCropCancel}
                    isUploading={isUploadingAvatar}
                />
            )}
        </div>
    );
};

export default AccountPage;
