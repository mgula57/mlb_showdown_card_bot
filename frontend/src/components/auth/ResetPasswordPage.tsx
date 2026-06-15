import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { supabase } from '../../api/supabase';
import { FaLock, FaCheckCircle } from 'react-icons/fa';

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

    const inputCls = `
        w-full px-3 py-2
        bg-background-primary
        border border-form-element
        rounded-lg text-secondary
        focus:outline-none focus:ring-2 focus:ring-accent
        disabled:opacity-50 disabled:cursor-not-allowed
    `;

    return (
        <div className="min-h-screen bg-primary flex items-center justify-center p-4">
            <div className="w-full max-w-sm">

                {/* Card */}
                <div className="rounded-xl border border-form-element bg-background-secondary p-8 shadow-lg">

                    {/* Loading */}
                    {pageState === 'loading' && (
                        <div className="text-center space-y-3">
                            <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto" />
                            <p className="text-sm text-secondary">Verifying reset link…</p>
                        </div>
                    )}

                    {/* Invalid / expired link */}
                    {pageState === 'invalid' && (
                        <div className="text-center space-y-4">
                            <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto">
                                <FaLock className="text-red-500 text-xl" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold text-secondary mb-1">Link expired</h1>
                                <p className="text-sm text-secondary opacity-70">
                                    This reset link is invalid or has expired. Request a new one from the sign-in screen.
                                </p>
                            </div>
                            <button
                                onClick={() => navigate('/')}
                                className="w-full py-2.5 bg-tertiary text-primary rounded-lg hover:bg-quaternary cursor-pointer transition-colors font-semibold">
                                Back to Sign In
                            </button>
                        </div>
                    )}

                    {/* Ready — set new password */}
                    {pageState === 'ready' && (
                        <>
                            <div className="text-center mb-6">
                                <div className="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-3">
                                    <FaLock className="text-accent text-xl" />
                                </div>
                                <h1 className="text-xl font-bold text-secondary">Set new password</h1>
                                <p className="text-sm text-secondary opacity-70 mt-1">Choose a strong password for your account.</p>
                            </div>

                            {error && (
                                <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">
                                    {error}
                                </div>
                            )}

                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div>
                                    <label htmlFor="new-password" className="block text-sm font-medium text-secondary mb-1">
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
                                    <label htmlFor="confirm-password" className="block text-sm font-medium text-secondary mb-1">
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
                                    className="w-full py-2.5 bg-tertiary text-primary rounded-lg hover:bg-quaternary cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold">
                                    {loading ? 'Updating…' : 'Update Password'}
                                </button>
                            </form>
                        </>
                    )}

                    {/* Success */}
                    {pageState === 'success' && (
                        <div className="text-center space-y-4">
                            <FaCheckCircle className="text-green-500 text-4xl mx-auto" />
                            <div>
                                <h1 className="text-xl font-bold text-secondary mb-1">Password updated!</h1>
                                <p className="text-sm text-secondary opacity-70">
                                    Your password has been changed. You're now signed in.
                                </p>
                            </div>
                            <button
                                onClick={() => navigate('/account')}
                                className="w-full py-2.5 bg-tertiary text-primary rounded-lg hover:bg-quaternary cursor-pointer transition-colors font-semibold">
                                Go to Account
                            </button>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
};
