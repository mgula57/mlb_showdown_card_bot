/**
 * @fileoverview Authentication Context
 * 
 * Provides global authentication state management using Supabase Auth.
 * This context tracks the current user session and provides authentication methods
 * throughout the application.
 * 
 * **Features:**
 * - Automatic session persistence
 * - Real-time auth state changes
 * - Sign in/out methods
 * - User profile access
 * 
 * @example
 * ```tsx
 * const { user, signIn, signOut } = useAuth();
 * 
 * if (user) {
 *   return <div>Welcome, {user.email}</div>;
 * }
 * ```
 */

import React, { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { supabase } from '../../api/supabase';
import type { User, Session } from '@supabase/supabase-js';

/**
 * Authentication context interface
 */
interface AuthContextType {
    /** Current authenticated user, or null if not signed in */
    user: User | null;
    /** Current session object */
    session: Session | null;
    /** Whether auth state is being initialized */
    loading: boolean;
    /** Sign in with email and password */
    signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
    /** Sign up with email and password */
    signUp: (email: string, password: string) => Promise<{ error: Error | null }>;
    /** Sign out the current user */
    signOut: () => Promise<void>;
    /** Sign in with OAuth provider (Google, GitHub, etc.) */
    signInWithProvider: (provider: 'google') => Promise<{ error: Error | null }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Hook to access authentication context
 * @throws Error if used outside AuthProvider
 */
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

/**
 * Authentication Provider Props
 */
interface AuthProviderProps {
    children: ReactNode;
}

/**
 * Authentication Provider Component
 * 
 * Wraps the application to provide authentication state and methods.
 * Automatically syncs with Supabase auth state changes.
 * 
 * @param props - Component props
 * @returns Provider component with auth context
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [session, setSession] = useState<Session | null>(null);
    const [loading, setLoading] = useState(true);

    /**
     * Initialize auth state and listen for changes
     */
    useEffect(() => {
        // Get initial session
        supabase.auth.getSession().then(({ data: { session } }: { data: { session: Session | null } }) => {
            setSession(session);
            setUser(session?.user ?? null);
            setLoading(false);
        });

        // Listen for auth state changes
        const {
            data: { subscription },
        } = supabase.auth.onAuthStateChange((_event: string, session: Session | null) => {
            setSession(session);
            setUser(session?.user ?? null);
            setLoading(false);
        });

        return () => subscription.unsubscribe();
    }, []);

    /**
     * Sign in with email and password
     */
    const signIn = async (email: string, password: string) => {
        try {
            const { error } = await supabase.auth.signInWithPassword({
                email,
                password,
            });
            return { error: error as Error | null };
        } catch (error) {
            return { error: error as Error };
        }
    };

    /**
     * Sign up with email and password
     */
    const signUp = async (email: string, password: string) => {
        try {
            const { error } = await supabase.auth.signUp({
                email,
                password,
            });
            return { error: error as Error | null };
        } catch (error) {
            return { error: error as Error };
        }
    };

    /**
     * Sign out the current user
     */
    const signOut = async () => {
        await supabase.auth.signOut();
    };

    /**
     * Sign in with OAuth provider
     */
    const signInWithProvider = async (provider: 'google') => {
        try {
            const { error } = await supabase.auth.signInWithOAuth({
                provider,
                options: {
                    redirectTo: `${window.location.origin}/`,
                },
            });
            return { error: error as Error | null };
        } catch (error) {
            return { error: error as Error };
        }
    };

    const value = {
        user,
        session,
        loading,
        signIn,
        signUp,
        signOut,
        signInWithProvider,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
