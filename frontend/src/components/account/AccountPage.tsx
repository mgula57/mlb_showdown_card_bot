/**
 * @fileoverview Account Page Component
 * 
 * User account management page displaying user information and application settings.
 * Provides interfaces for:
 * - Viewing account details (email, join date)
 * - Managing account settings (future: email preferences, notifications)
 * - Application preferences (theme, default set)
 * - Image libraries (Google Drive folders used for Auto player images)
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
import { useSiteSettings, useTheme } from '../shared/SiteSettingsContext';
import { SET_SELECT_OPTIONS_LG } from '../shared/SetBadge';
import { FaEnvelope, FaClock, FaPalette, FaSignOutAlt, FaTrash, FaCog, FaUser, FaCamera, FaSpinner } from 'react-icons/fa';
import { SignInPrompt } from '../shared/SignInPrompt';
import CustomSelect from '../shared/CustomSelect';
import { uploadAvatar, removeAvatar, validateAvatarFile, AVATAR_ACCEPT } from '../../api/userAvatar';
import AvatarCropModal from './AvatarCropModal';
import { AccountAvatar } from '../auth/AccountIcon';
import ColorPicker from '../shared/ColorPicker';
import { DEFAULT_PRIMARY_COLOR, DEFAULT_SECONDARY_COLOR } from '../../api/userSettings';
import AccountSection from './AccountSection';
import ImageLibrarySettings from './ImageLibrarySettings';

import { buttonClass } from '../shared/buttonStyles';
import { Heading } from '../shared/Heading';
import { PinstripeBackdrop } from '../shared/PinstripeBackdrop';
import { FIELD_LABEL_CLASS, fieldClass } from '../shared/fieldStyles';
import { choiceClass } from '../shared/choiceStyles';
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
    const { setTheme, theme } = useTheme();
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
            <div className="min-h-screen bg-primary p-4 md:p-8">
                <div className="max-w-4xl mx-auto space-y-6 animate-pulse" aria-label="Loading account">
                    <div className="mb-8 space-y-2">
                        <div className="h-7 w-64 rounded-plate bg-(--background-tertiary)" />
                        <div className="h-4 w-80 rounded-plate bg-(--background-tertiary)" />
                    </div>
                    {[160, 280, 200].map(height => (
                        <div key={height} className="rounded-card border border-(--divider) bg-(--background-secondary)" style={{ height }} />
                    ))}
                </div>
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
            setUsernameError("Couldn't update your username. Try again.");
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
            setAvatarError("Upload failed. Try again.");
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
        <div className="min-h-screen relative isolate bg-primary p-4 md:p-8">
            {/* Card-back pinstripes behind the page header */}
            <PinstripeBackdrop heightClass="h-72" />
            <div className="max-w-4xl mx-auto space-y-6">
                
                {/* Page Header */}
                <div className="mb-8">
                    <Heading level="page" className="mb-2">Account Settings</Heading>
                    <p className="text-(--text-tertiary)">Manage your account information and preferences</p>
                </div>

                {/* User Profile Card */}
                <AccountSection>
                    <div className="flex items-start space-x-4">
                        {/* Avatar */}
                        <div className="shrink-0">
                            <label
                                htmlFor="avatar-upload"
                                className={`relative group block w-20 h-20 rounded-full focus-within:ring-2 focus-within:ring-(--showdown-blue) ${isUploadingAvatar ? 'cursor-not-allowed' : 'cursor-pointer'}`}
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
                                        bg-(--showdown-blue-fill) border-2 border-(--background-secondary)
                                        flex items-center justify-center
                                        group-hover:opacity-0 transition-opacity duration-200
                                    ">
                                        <FaCamera className="w-2.5 h-2.5 text-white" />
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
                                        className="text-xs text-tertiary hover:underline block w-full cursor-pointer"
                                    >
                                        Remove
                                    </button>
                                )}
                                {avatarError && (
                                    <p className="text-xs text-(--red)">{avatarError}</p>
                                )}
                            </div>

                            <input
                                ref={avatarInputRef}
                                id="avatar-upload"
                                type="file"
                                accept={AVATAR_ACCEPT}
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
                                    <FaUser className="text-(--text-tertiary) shrink-0 mt-1" />
                                    <div className="flex-1">
                                        <div className="flex items-end gap-5">
                                            <div>
                                                <p className={FIELD_LABEL_CLASS}>Username</p>
                                                <p className="text-secondary font-medium">{username ?? 'Not set'}</p>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={() => {
                                                    setIsEditingUsername(true);
                                                    setUsernameError(null);
                                                }}
                                                className="text-xs mb-1 text-tertiary hover:underline cursor-pointer"
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
                                                    className={fieldClass('md', `w-full focus:outline-none ${usernameError ? 'border-(--red)!' : ''}`)}
                                                    placeholder="e.g. brianjordangoat"
                                                />
                                                {isCheckingUsername && (
                                                    <p className="text-xs text-(--text-tertiary)">Checking availability…</p>
                                                )}
                                                {usernameError && !isCheckingUsername ? (
                                                    <p className="text-xs text-(--red)">{usernameError}</p>
                                                ) : (!usernameError && !isCheckingUsername ? (<p className="text-xs text-(--green)">Username available</p>) : null)}
                                                <div className="flex items-center gap-2">
                                                    <button
                                                        type="button"
                                                        onClick={handleSaveUsername}
                                                        disabled={isSavingUsername || isCheckingUsername}
                                                        className={buttonClass('primary', 'sm')}
                                                    >
                                                        {isSavingUsername ? 'Saving…' : 'Save'}
                                                    </button>
                                                    <button
                                                        type="button"
                                                        onClick={() => setIsEditingUsername(false)}
                                                        className={buttonClass('secondary', 'sm')}
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
                                    <FaEnvelope className="text-(--text-tertiary) shrink-0" />
                                    <div>
                                        <p className={FIELD_LABEL_CLASS}>Email</p>
                                        <p className="text-secondary font-medium">{user.email}</p>
                                    </div>
                                </div>

                                {/* Account Created */}
                                <div className="flex items-center space-x-3">
                                    <FaClock className="text-(--text-tertiary) shrink-0" />
                                    <div>
                                        <p className={FIELD_LABEL_CLASS}>Member Since</p>
                                        <p className="text-secondary font-medium">
                                            {user.created_at ? formatDate(user.created_at) : 'Unknown'}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </AccountSection>

                {/* Application Settings */}
                <AccountSection title="Application Settings" icon={<FaCog />}>
                    <div className="space-y-6">
                        {/* Theme Setting */}
                        <div>
                            <div className="flex items-center space-x-2 mb-2">
                                <FaPalette className="text-(--text-tertiary)" />
                                <label className={FIELD_LABEL_CLASS}>Theme</label>
                            </div>
                            <div className="flex gap-2">
                                {(['light', 'dark', 'system'] as const).map(option => (
                                    <button
                                        key={option}
                                        type="button"
                                        onClick={() => setTheme(option)}
                                        className={choiceClass(theme === option, 'md', 'capitalize')}
                                    >
                                        {option}
                                    </button>
                                ))}
                            </div>
                            <p className="text-xs text-(--text-tertiary) mt-2">
                                Choose how the application appears to you
                            </p>
                        </div>

                        {/* Default Showdown Set */}
                        <div>
                            <label className={`${FIELD_LABEL_CLASS} mb-2`}>Default Set</label>
                            <CustomSelect
                                className="w-44"
                                size="lg"
                                value={userShowdownSet}
                                onChange={setUserShowdownSet}
                                options={SET_SELECT_OPTIONS_LG}
                                showDropdownArrow={true}
                            />
                            
                            <p className="text-xs text-(--text-tertiary) mt-2">
                                Your preferred Showdown set for card generation
                            </p>
                        </div>

                        {/* Default Team Colors */}
                        <div>
                            <label className={`${FIELD_LABEL_CLASS} mb-2`}>Default Team Colors</label>
                            <div className="flex items-center gap-6">
                                <ColorPicker
                                    label="Primary Color"
                                    value={userSettings?.default_primary_color ?? DEFAULT_PRIMARY_COLOR}
                                    onChange={v => syncSetting({ default_primary_color: v })}
                                />
                                <ColorPicker
                                    label="Secondary Color"
                                    value={userSettings?.default_secondary_color ?? DEFAULT_SECONDARY_COLOR}
                                    onChange={v => syncSetting({ default_secondary_color: v })}
                                />
                            </div>
                            <p className="text-xs text-(--text-tertiary) mt-2">
                                Used as the starting colors when creating a new team
                            </p>
                        </div>
                    </div>
                </AccountSection>

                {/* Image Libraries */}
                <ImageLibrarySettings />

                {/* Account Actions */}
                <AccountSection title="Account Actions">
                    <div className="space-y-3">
                        {/* Sign Out Button */}
                        <button
                            onClick={handleSignOut}
                            disabled={isSigningOut}
                            className={buttonClass('secondary', 'md', 'w-full md:w-auto px-6! py-3!')}
                        >
                            <FaSignOutAlt />
                            <span>{isSigningOut ? 'Signing out…' : 'Sign out'}</span>
                        </button>

                        {/* Delete Account Button (placeholder for future implementation) */}
                        <button
                            disabled
                            className={buttonClass('danger', 'md', 'w-full md:w-auto px-6! py-3!')}
                            title="Account deletion coming soon"
                        >
                            <FaTrash />
                            <span>Delete account</span>
                        </button>
                        <p className="text-xs text-(--text-tertiary)">
                            Account deletion will be available in a future update. 
                            For help with your account, email <a href="mailto:mlbshowdownbot@gmail.com" className="text-tertiary hover:underline">mlbshowdownbot@gmail.com</a>.
                        </p>
                    </div>
                </AccountSection>

                {/* Footer Info */}
                <div className="text-center text-sm text-(--text-tertiary) py-4">
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
