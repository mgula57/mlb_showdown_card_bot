import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from './AuthContext';
import { FaDiscord, FaArrowLeft } from 'react-icons/fa';
import { Modal } from '../shared/Modal';

interface LoginModalProps {
    onClose: () => void;
    onSuccess?: () => void;
}

type Step = 'email' | 'signin' | 'signup' | 'forgot';

export const LoginModal: React.FC<LoginModalProps> = ({ onClose, onSuccess }) => {
    const { signIn, signUp, signInWithProvider, checkUsernameAvailability, checkEmailExists, resetPassword } = useAuth();

    const [step, setStep] = useState<Step>('email');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [username, setUsername] = useState('');
    const [usernameError, setUsernameError] = useState<string | null>(null);
    const [checkingUsername, setCheckingUsername] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [resetSent, setResetSent] = useState(false);

    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    // Username availability check (sign up step only)
    useEffect(() => {
        if (step !== 'signup') return;
        if (!username) { setUsernameError(null); setCheckingUsername(false); return; }
        if (username.length < 3) { setUsernameError('Username must be at least 3 characters'); setCheckingUsername(false); return; }
        if (!/^[a-zA-Z0-9_]+$/.test(username)) { setUsernameError('Username can only contain letters, numbers, and underscores'); setCheckingUsername(false); return; }

        setUsernameError(null);
        setCheckingUsername(true);
        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(async () => {
            const available = await checkUsernameAvailability(username);
            setCheckingUsername(false);
            setUsernameError(available ? null : 'Username is already taken');
        }, 500);

        return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
    }, [username, step]);

    const handleOAuthSignIn = async (provider: 'google' | 'discord') => {
        setError(null);
        setLoading(true);
        const result = await signInWithProvider(provider);
        if (result.error) { setError(result.error.message); setLoading(false); }
    };

    const handleEmailContinue = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setLoading(true);
        const exists = await checkEmailExists(email);
        setLoading(false);
        setStep(exists ? 'signin' : 'signup');
    };

    const handleSignIn = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setLoading(true);
        const result = await signIn(email, password);
        setLoading(false);
        if (result.error) { setError(result.error.message); return; }
        onSuccess?.();
        onClose();
    };

    const handleSignUp = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!username || username.length < 3) { setError('Username must be at least 3 characters'); return; }
        if (!/^[a-zA-Z0-9_]+$/.test(username)) { setError('Username can only contain letters, numbers, and underscores'); return; }
        if (usernameError) { setError('Please fix username errors before continuing'); return; }
        if (password !== confirmPassword) { setError('Passwords do not match'); return; }

        setLoading(true);
        const available = await checkUsernameAvailability(username);
        if (!available) { setError('Username is already taken'); setLoading(false); return; }

        const result = await signUp(email, password, username);
        setLoading(false);
        if (result.error) { setError(result.error.message); return; }
        onSuccess?.();
        onClose();
    };

    const handleForgotPassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setLoading(true);
        const result = await resetPassword(email);
        setLoading(false);
        if (result.error) { setError(result.error.message); return; }
        setResetSent(true);
    };

    const goBack = () => {
        setStep('email');
        setPassword('');
        setConfirmPassword('');
        setUsername('');
        setUsernameError(null);
        setError(null);
        setResetSent(false);
    };

    const titles: Record<Step, string> = {
        email: 'Sign In',
        signin: 'Welcome back',
        signup: 'Create account',
        forgot: 'Reset password',
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
        <Modal onClose={onClose} size='sm' title={titles[step]}>
            <div className='p-6'>

                {/* Error */}
                {error && (
                    <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">
                        {error}
                    </div>
                )}

                {/* ── Step: email ── */}
                {step === 'email' && (
                    <>
                        {/* OAuth */}
                        <div className="space-y-3 mb-6">
                            <button onClick={() => handleOAuthSignIn('google')} disabled={loading}
                                className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium">
                                <svg className="w-5 h-5" viewBox="0 0 24 24">
                                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
                                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                                </svg>
                                <span>Continue with Google</span>
                            </button>
                            <button onClick={() => handleOAuthSignIn('discord')} disabled={loading}
                                className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-[#5865F2] text-white rounded-lg hover:bg-[#4752c4] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium">
                                <FaDiscord className="w-5 h-5" />
                                <span>Continue with Discord</span>
                            </button>
                        </div>

                        <div className="relative mb-6">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-form-element" />
                            </div>
                            <div className="relative flex justify-center text-sm">
                                <span className="px-2 bg-background-secondary text-gray-500">Or continue with email</span>
                            </div>
                        </div>

                        <form onSubmit={handleEmailContinue} className="space-y-4">
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium text-secondary mb-1">Email</label>
                                <input
                                    id="email" type="email" value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required disabled={loading}
                                    className={inputCls}
                                    placeholder="you@example.com"
                                />
                            </div>
                            <button type="submit" disabled={loading || !email}
                                className="w-full py-2.5 bg-tertiary text-primary rounded-lg hover:bg-quaternary cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold">
                                {loading ? 'Checking...' : 'Continue'}
                            </button>
                        </form>
                    </>
                )}

                {/* ── Step: sign in ── */}
                {step === 'signin' && (
                    <>
                        <p className="text-sm text-secondary mb-4 break-all">{email}</p>
                        <form onSubmit={handleSignIn} className="space-y-4">
                            <div>
                                <div className="flex items-center justify-between mb-1">
                                    <label htmlFor="password" className="block text-sm font-medium text-secondary">Password</label>
                                    <button type="button" onClick={() => { setStep('forgot'); setError(null); }}
                                        className="text-xs text-accent hover:underline cursor-pointer">
                                        Forgot password?
                                    </button>
                                </div>
                                <input
                                    id="password" type="password" value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required disabled={loading} minLength={6}
                                    className={inputCls}
                                    placeholder="••••••••"
                                />
                            </div>
                            <button type="submit" disabled={loading}
                                className="w-full py-2.5 bg-tertiary text-primary rounded-lg hover:bg-quaternary cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold">
                                {loading ? 'Signing in...' : 'Sign In'}
                            </button>
                        </form>
                        <button onClick={goBack} disabled={loading}
                            className="mt-4 w-full flex items-center justify-center gap-2 py-2 text-sm text-secondary hover:text-primary transition-colors cursor-pointer disabled:opacity-50">
                            <FaArrowLeft className="text-xs" /> Use a different email
                        </button>
                    </>
                )}

                {/* ── Step: forgot password ── */}
                {step === 'forgot' && (
                    <>
                        {resetSent ? (
                            <div className="text-center space-y-4">
                                <p className="text-sm text-secondary">
                                    We sent a password reset link to <span className="font-medium text-primary break-all">{email}</span>.
                                    Check your inbox and follow the link to reset your password.
                                </p>
                                <button onClick={goBack}
                                    className="w-full py-2.5 bg-tertiary text-primary rounded-lg hover:bg-quaternary cursor-pointer transition-colors font-semibold">
                                    Back to Sign In
                                </button>
                            </div>
                        ) : (
                            <>
                                <p className="text-sm text-secondary mb-4">
                                    Enter your email and we'll send you a link to reset your password.
                                </p>
                                <form onSubmit={handleForgotPassword} className="space-y-4">
                                    <div>
                                        <label htmlFor="reset-email" className="block text-sm font-medium text-secondary mb-1">Email</label>
                                        <input
                                            id="reset-email" type="email" value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            required disabled={loading}
                                            className={inputCls}
                                            placeholder="you@example.com"
                                        />
                                    </div>
                                    <button type="submit" disabled={loading || !email}
                                        className="w-full py-2.5 bg-tertiary text-primary rounded-lg hover:bg-quaternary cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold">
                                        {loading ? 'Sending...' : 'Send Reset Link'}
                                    </button>
                                </form>
                                <button onClick={() => { setStep('signin'); setError(null); }} disabled={loading}
                                    className="mt-4 w-full flex items-center justify-center gap-2 py-2 text-sm text-secondary hover:text-primary transition-colors cursor-pointer disabled:opacity-50">
                                    <FaArrowLeft className="text-xs" /> Back to Sign In
                                </button>
                            </>
                        )}
                    </>
                )}

                {/* ── Step: sign up ── */}
                {step === 'signup' && (
                    <>
                        <p className="text-sm text-secondary mb-4 break-all">{email}</p>
                        <form onSubmit={handleSignUp} className="space-y-4">
                            <div>
                                <label htmlFor="username" className="block text-sm font-medium text-secondary mb-1">Username</label>
                                <input
                                    id="username" type="text" value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    required disabled={loading} minLength={3}
                                    className={`${inputCls} ${usernameError ? 'border-red-500' : ''}`}
                                    placeholder="e.g. brianjordangoat"
                                />
                                {checkingUsername && <p className="text-xs text-gray-500 mt-1">Checking availability...</p>}
                                {usernameError && <p className="text-xs text-red-500 mt-1">{usernameError}</p>}
                                {!usernameError && username && !checkingUsername && (
                                    <p className="text-xs text-green-500 mt-1">Username is available!</p>
                                )}
                                <p className="text-xs text-gray-500 mt-1">Letters, numbers, and underscores only. Min 3 characters.</p>
                            </div>
                            <div>
                                <label htmlFor="new-password" className="block text-sm font-medium text-secondary mb-1">Password</label>
                                <input
                                    id="new-password" type="password" value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required disabled={loading} minLength={6}
                                    className={inputCls}
                                    placeholder="••••••••"
                                />
                            </div>
                            <div>
                                <label htmlFor="confirmPassword" className="block text-sm font-medium text-secondary mb-1">Confirm Password</label>
                                <input
                                    id="confirmPassword" type="password" value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    required disabled={loading} minLength={6}
                                    className={inputCls}
                                    placeholder="••••••••"
                                />
                            </div>
                            <button type="submit" disabled={loading || !!usernameError || checkingUsername}
                                className="w-full py-2.5 bg-tertiary text-primary rounded-lg hover:bg-quaternary cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold">
                                {loading ? 'Creating account...' : 'Create Account'}
                            </button>
                        </form>
                        <button onClick={goBack} disabled={loading}
                            className="mt-4 w-full flex items-center justify-center gap-2 py-2 text-sm text-secondary hover:text-primary transition-colors cursor-pointer disabled:opacity-50">
                            <FaArrowLeft className="text-xs" /> Use a different email
                        </button>
                    </>
                )}

            </div>
        </Modal>
    );
};
