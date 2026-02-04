/**
 * @fileoverview Login Modal Component
 * 
 * Modal dialog for user authentication with email/password or OAuth providers.
 * Provides a clean interface for:
 * - Sign in with email/password
 * - Sign up for new accounts
 * - OAuth authentication (Google, GitHub)
 * - Password reset (future enhancement)
 * 
 * **Features:**
 * - Toggle between sign in and sign up modes
 * - Form validation
 * - Error handling
 * - OAuth provider buttons
 * - Responsive design
 * 
 * @component
 */

import React, { useState } from 'react';
import { useAuth } from './AuthContext';
import { FaGoogle } from 'react-icons/fa';

import { Modal } from '../shared/Modal';

/**
 * Props for LoginModal component
 */
interface LoginModalProps {
    /** Callback to close the modal */
    onClose: () => void;
}

/**
 * Login Modal Component
 * 
 * Displays authentication modal with sign in/up forms and OAuth options.
 * Handles all authentication flows through the AuthContext.
 * 
 * @param props - Component props
 * @returns Modal dialog for authentication
 */
export const LoginModal: React.FC<LoginModalProps> = ({ onClose }) => {
    const { signIn, signUp, signInWithProvider } = useAuth();
    const [isSignUp, setIsSignUp] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    /**
     * Handle form submission
     */
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        // Validate passwords match for sign up
        if (isSignUp && password !== confirmPassword) {
            setError('Passwords do not match');
            setLoading(false);
            return;
        }

        try {
            const result = isSignUp 
                ? await signUp(email, password)
                : await signIn(email, password);

            if (result.error) {
                setError(result.error.message);
            } else {
                // Success - close modal and reset form
                onClose();
                setEmail('');
                setPassword('');
                setConfirmPassword('');
                setIsSignUp(false);
            }
        } catch (err) {
            setError('An unexpected error occurred');
        } finally {
            setLoading(false);
        }
    };

    /**
     * Handle OAuth sign in
     */
    const handleOAuthSignIn = async (provider: 'google') => {
        setError(null);
        setLoading(true);
        
        const result = await signInWithProvider(provider);
        
        if (result.error) {
            setError(result.error.message);
            setLoading(false);
        }
        // Note: OAuth redirect will happen automatically
    };

    /**
     * Toggle between sign in and sign up
     */
    const toggleMode = () => {
        setIsSignUp(!isSignUp);
        setError(null);
        setPassword('');
        setConfirmPassword('');
    };

    return (
        <Modal onClose={onClose} size='sm' title={isSignUp ? 'Sign Up' : 'Sign In'}>

            <div className='p-6'>
                {/* Error Message */}
                {error && (
                    <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                        {error}
                    </div>
                )}

                {/* OAuth Buttons */}
                <div className="space-y-3 mb-6">
                    <button
                        onClick={() => handleOAuthSignIn('google')}
                        disabled={loading}
                        className="
                            w-full flex items-center justify-center space-x-2
                            py-2.5 px-4
                            bg-white text-gray-700
                            border border-gray-300
                            rounded-lg
                            hover:bg-gray-50
                            cursor-pointer
                            disabled:opacity-50 disabled:cursor-not-allowed
                            transition-colors duration-150
                            font-medium
                        "
                    >
                        <FaGoogle className="w-5 h-5" />
                        <span>Continue with Google</span>
                    </button>

                </div>

                {/* Divider */}
                <div className="relative mb-6">
                    <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-form-element"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                        <span className="px-2 bg-background-secondary text-gray-500">
                            Or continue with email
                        </span>
                    </div>
                </div>

                {/* Email/Password Form */}
                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Email Input */}
                    <div>
                        <label htmlFor="email" className="block text-sm font-medium text-secondary mb-1">
                            Email
                        </label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            disabled={loading}
                            className="
                                w-full px-3 py-2
                                bg-background-primary
                                border border-form-element
                                rounded-lg
                                text-secondary
                                focus:outline-none focus:ring-2 focus:ring-accent
                                disabled:opacity-50 disabled:cursor-not-allowed
                            "
                            placeholder="you@example.com"
                        />
                    </div>

                    {/* Password Input */}
                    <div>
                        <label htmlFor="password" className="block text-sm font-medium text-secondary mb-1">
                            Password
                        </label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            disabled={loading}
                            minLength={6}
                            className="
                                w-full px-3 py-2
                                bg-background-primary
                                border border-form-element
                                rounded-lg
                                text-secondary
                                focus:outline-none focus:ring-2 focus:ring-accent
                                disabled:opacity-50 disabled:cursor-not-allowed
                            "
                            placeholder="••••••••"
                        />
                    </div>

                    {/* Confirm Password (Sign Up only) */}
                    {isSignUp && (
                        <div>
                            <label htmlFor="confirmPassword" className="block text-sm font-medium text-secondary mb-1">
                                Confirm Password
                            </label>
                            <input
                                id="confirmPassword"
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                                disabled={loading}
                                minLength={6}
                                className="
                                    w-full px-3 py-2
                                    bg-background-primary
                                    border border-form-element
                                    rounded-lg
                                    text-secondary
                                    focus:outline-none focus:ring-2 focus:ring-accent
                                    disabled:opacity-50 disabled:cursor-not-allowed
                                "
                                placeholder="••••••••"
                            />
                        </div>
                    )}

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={loading}
                        className="
                            w-full py-2.5
                            bg-tertiary text-primary
                            rounded-lg
                            hover:bg-quaternary cursor-pointer
                            disabled:opacity-50 disabled:cursor-not-allowed
                            transition-colors duration-150
                            font-semibold
                        "
                    >
                        {loading ? 'Processing...' : (isSignUp ? 'Sign Up' : 'Sign In')}
                    </button>
                </form>

                {/* Toggle Sign In/Up */}
                <div className="mt-6 text-center text-sm text-gray-500">
                    {isSignUp ? 'Already have an account?' : "Don't have an account?"}
                    {' '}
                    <button
                        onClick={toggleMode}
                        disabled={loading}
                        className="text-accent hover:underline font-medium disabled:opacity-50 cursor-pointer"
                    >
                        {isSignUp ? 'Sign In' : 'Sign Up'}
                    </button>
                </div>
            </div>
        </Modal>
    );
};
