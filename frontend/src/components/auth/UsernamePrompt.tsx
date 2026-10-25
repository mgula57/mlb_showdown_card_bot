/**
 * @fileoverview Username Prompt Modal
 * 
 * Modal that prompts OAuth users to choose a username after signing up.
 * Appears automatically for new OAuth users who don't have a username set.
 * 
 * **Features:**
 * - Username validation
 * - Availability checking
 * - Cannot be dismissed until username is set
 * - Updates profile table directly
 * 
 * @component
 */

import React, { useState } from 'react';
import { useAuth } from './AuthContext';
import { supabase } from '../../api/supabase';
import { Modal } from '../shared/Modal';

import { FIELD_LABEL_CLASS, fieldClass } from '../shared/fieldStyles';
import { buttonClass } from '../shared/buttonStyles';
/**
 * Props for UsernamePrompt component
 */
interface UsernamePromptProps {
    /** User ID to update */
    userId: string;
    /** Callback when username is successfully set */
    onComplete: () => void;
}

/**
 * Username Prompt Modal Component
 * 
 * Forces OAuth users to choose a username before accessing the app.
 * Validates format and checks availability.
 * 
 * @param props - Component props
 * @returns Modal dialog for username selection
 */
export const UsernamePrompt: React.FC<UsernamePromptProps> = ({ userId, onComplete }) => {
    const { checkUsernameAvailability } = useAuth();
    const [username, setUsername] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [checking, setChecking] = useState(false);
    const [saving, setSaving] = useState(false);

    /**
     * Handle username submission
     */
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        // Validate format
        if (username.length < 3) {
            setError('Username must be at least 3 characters');
            return;
        }
        if (!/^[a-zA-Z0-9_]+$/.test(username)) {
            setError('Username can only contain letters, numbers, and underscores');
            return;
        }

        // Check availability
        // setChecking(true);
        const isAvailable = await checkUsernameAvailability(username);
        setChecking(false);

        if (!isAvailable) {
            setError('Username is already taken');
            return;
        }

        // Update profile
        setSaving(true);
        try {
            const { error: updateError } = await supabase
                .from('profiles')
                .update({ username })
                .eq('id', userId);

            if (updateError) {
                setError('Failed to save username. Please try again.');
                setSaving(false);
                return;
            }

            onComplete();
        } catch (err) {
            setError('An unexpected error occurred');
            setSaving(false);
        }
    };

    /**
     * Handle username blur - check availability
     */
    const handleUsernameCheck = async () => {
        if (!username || username.length < 3) return;
        if (!/^[a-zA-Z0-9_]+$/.test(username)) return;

        setChecking(true);
        const isAvailable = await checkUsernameAvailability(username);
        setChecking(false);

        if (!isAvailable) {
            setError('Username is already taken');
        } else {
            setError(null);
        }
    };

    return (
        <Modal 
            onClose={() => {}} // Cannot be dismissed
            size="sm" 
            title="Choose Your Username"
            disableCloseButton={true}
        >
            <div className="p-6">
                <p className="text-secondary mb-4">
                    Please choose a username to complete your account setup.
                </p>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Username Input */}
                    <div>
                        <label htmlFor="username" className={`${FIELD_LABEL_CLASS} mb-1`}>
                            Username <span className="text-(--red)">*</span>
                        </label>
                        <input
                            id="username"
                            type="text"
                            value={username}
                            onChange={(e) => {
                                setUsername(e.target.value);
                                setError(null);
                                handleUsernameCheck();
                            }}
                            required
                            disabled={saving}
                            minLength={3}
                            pattern="[a-zA-Z0-9_]+"
                            autoFocus
                            className={fieldClass('md', `w-full focus:outline-none ${error ? 'border-(--red)!' : ''}`)}
                            placeholder="e.g. brianjordangoat"
                        />
                        
                        {checking && (
                            <p className="text-xs text-(--text-tertiary) mt-1">
                                Checking availability...
                            </p>
                        )}
                        {error && (
                            <p className="text-xs text-(--red) mt-1">
                                {error}
                            </p>
                        )}
                        {!error && username && !checking && username.length >= 3 && /^[a-zA-Z0-9_]+$/.test(username) && (
                            <p className="text-xs text-(--green) mt-1">
                                Username is available!
                            </p>
                        )}
                        <p className="text-xs text-(--text-tertiary) mt-1">
                            Letters, numbers, and underscores only. Min 3 characters.
                        </p>
                    </div>

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={saving || checking || !!error || !username}
                        className={buttonClass('primary', 'md', 'w-full')}
                    >
                        {saving ? 'Saving...' : 'Continue'}
                    </button>
                </form>
            </div>
        </Modal>
    );
};
