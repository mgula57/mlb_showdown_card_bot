import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { supabase } from '../../api/supabase';
import { FaLock, FaCheckCircle } from 'react-icons/fa';

import { Heading } from '../shared/Heading';
import { FIELD_LABEL_CLASS, fieldClass } from '../shared/fieldStyles';
import { buttonClass } from '../shared/buttonStyles';
import { InlineError } from '../shared/InlineError';
type PageState = 'loading' | 'ready' | 'success' | 'invalid';

export const ResetPasswordPage: React.FC = () => {
    const { updatePassword } = useAuth();
    const navigate = useNavigate();

    const [pageState, setPageState] = useState<PageState>('loading');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Supabase fires PASSWORD_RECOVERY when the user arrives via the email link.
        // The client parses the hash and establishes a temporary session automatically.
        const { data: { subscription } } = supabase.auth.onAuthStateChange((event) => {
            if (event === 'PASSWORD_RECOVERY') {
                setPageState('ready');
            }
        });

        // If the session is already set (page reloaded after hash was consumed), go ready.
        supabase.auth.getSession().then(({ data: { session } }) => {
            if (session) setPageState('ready');
            else {
                // Give Supabase a moment to process the hash before declaring invalid.
                setTimeout(() => {
                    setPageState(prev => prev === 'loading' ? 'invalid' : prev);
                }, 1500);
            }
        });

        return () => subscription.unsubscribe();
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (password.length < 6) { setError('Password must be at least 6 characters'); return; }
        if (password !== confirmPassword) { setError('Passwords do not match'); return; }

        setLoading(true);
        const result = await updatePassword(password);
        setLoading(false);

        if (result.error) { setError(result.error.message); return; }
        setPageState('success');
    };

    const inputCls = fieldClass('md', 'w-full focus:outline-none');

    return (
        <div className="min-h-screen bg-primary flex items-center justify-center p-4">
            <div className="w-full max-w-sm">

                {/* Card */}
                <div className="rounded-card border border-form-element bg-(--background-secondary) p-8 shadow-overlay">

                    {/* Loading */}
                    {pageState === 'loading' && (
                        <div className="text-center space-y-3">
                            <div className="w-8 h-8 border-2 border-(--showdown-blue) border-t-transparent rounded-full animate-spin mx-auto" />
                            <p className="text-sm text-secondary">Verifying reset link…</p>
                        </div>
                    )}

                    {/* Invalid / expired link */}
                    {pageState === 'invalid' && (
                        <div className="text-center space-y-4">
                            <div className="w-12 h-12 rounded-full bg-(--red)/15 flex items-center justify-center mx-auto">
                                <FaLock className="text-(--red) text-xl" />
                            </div>
                            <div>
                                <Heading level="page" className="mb-1">Link expired</Heading>
                                <p className="text-sm text-secondary opacity-70">
                                    This reset link is invalid or has expired. Request a new one from the sign-in screen.
                                </p>
                            </div>
                            <button
                                onClick={() => navigate('/')}
                                className={buttonClass('primary', 'md', 'w-full')}>
                                Back to sign in
                            </button>
                        </div>
                    )}

                    {/* Ready — set new password */}
                    {pageState === 'ready' && (
                        <>
                            <div className="text-center mb-6">
                                <div className="w-12 h-12 rounded-full bg-(--showdown-blue)/15 flex items-center justify-center mx-auto mb-3">
                                    <FaLock className="text-(--showdown-blue) text-xl" />
                                </div>
                                <Heading level="page">Set new password</Heading>
                                <p className="text-sm text-secondary opacity-70 mt-1">Choose a strong password for your account.</p>
                            </div>

                            {error && (
                                <InlineError size="md" className="mb-4">{error}</InlineError>
                            )}

                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div>
                                    <label htmlFor="new-password" className={`${FIELD_LABEL_CLASS} mb-1`}>
                                        New password
                                    </label>
                                    <input
                                        id="new-password" type="password" value={password} autoFocus
                                        onChange={(e) => setPassword(e.target.value)}
                                        required disabled={loading} minLength={6}
                                        className={inputCls}
                                        placeholder="••••••••"
                                    />
                                </div>
                                <div>
                                    <label htmlFor="confirm-password" className={`${FIELD_LABEL_CLASS} mb-1`}>
                                        Confirm password
                                    </label>
                                    <input
                                        id="confirm-password" type="password" value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        required disabled={loading} minLength={6}
                                        className={inputCls}
                                        placeholder="••••••••"
                                    />
                                </div>
                                <button
                                    type="submit" disabled={loading || !password || !confirmPassword}
                                    className={buttonClass('primary', 'md', 'w-full')}>
                                    {loading ? 'Updating…' : 'Update password'}
                                </button>
                            </form>
                        </>
                    )}

                    {/* Success */}
                    {pageState === 'success' && (
                        <div className="text-center space-y-4">
                            <FaCheckCircle className="text-(--green) text-4xl mx-auto" />
                            <div>
                                <Heading level="page" className="mb-1">Password updated</Heading>
                                <p className="text-sm text-secondary opacity-70">
                                    Your password has been changed. You're now signed in.
                                </p>
                            </div>
                            <button
                                onClick={() => navigate('/account')}
                                className={buttonClass('primary', 'md', 'w-full')}>
                                Go to account
                            </button>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
};
