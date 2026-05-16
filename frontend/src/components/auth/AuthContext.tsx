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

import React, { createContext, useContext, useEffect, useState, useRef, useCallback, type ReactNode } from 'react';
import { supabase } from '../../api/supabase';
import type { User, Session } from '@supabase/supabase-js';
import { getUserSettings, updateUserSettings, type UserSettingsDB } from '../../api/userSettings';

export type { UserSettingsDB };

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
    /** Whether user needs to set username (OAuth users) */
    needsUsername: boolean;
    /** Username from profiles table */
    username: string | null;
    /** Update username in profiles table */
    updateUsername: (username: string) => Promise<{ error: Error | null }>;
    /** Sign in with email and password */
    signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
    /** Sign up with email and password */
    signUp: (email: string, password: string, username: string) => Promise<{ error: Error | null }>;
    /** Sign out the current user */
    signOut: () => Promise<void>;
    /** Check if username is available */
    checkUsernameAvailability: (username: string) => Promise<boolean>;
    /** Sign in with OAuth provider (Google, GitHub, etc.) */
    signInWithProvider: (provider: 'google') => Promise<{ error: Error | null }>;
    /** Refresh username check (call after username is set) */
    refreshProfile: () => Promise<void>;
    /** Settings loaded from DB after login (null when logged out or not yet loaded) */
    userSettings: UserSettingsDB | null;
    /** True once the first settings fetch completes after login */
    settingsLoaded: boolean;
    /** Persist a partial settings update; optimistic local update + debounced API write */
    syncSetting: (partial: Partial<UserSettingsDB>) => void;
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
    const [needsUsername, setNeedsUsername] = useState(false);
    const [username, setUsername] = useState<string | null>(null);
    const [userSettings, setUserSettings] = useState<UserSettingsDB | null>(null);
    const [settingsLoaded, setSettingsLoaded] = useState(false);

    const sessionRef = useRef<Session | null>(null);
    const pendingSettings = useRef<Partial<UserSettingsDB>>({});
    const syncTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

    /**
     * Check if user has a username in their profile
     */
    const checkUserProfile = async (userId: string) => {
        try {
            const { data, error } = await supabase
                .from('profiles')
                .select('username')
                .eq('id', userId)
                .single();

            if (error || !data || !data.username) {
                setNeedsUsername(true);
                setUsername(null);
            } else {
                setNeedsUsername(false);
                setUsername(data.username);
            }
        } catch (err) {
            console.error('Error checking profile:', err);
            setNeedsUsername(true);
            setUsername(null);
        }
    };

    /**
     * Refresh profile check (call after username is set)
     */
    const refreshProfile = async () => {
        if (user) {
            await checkUserProfile(user.id);
        }
    };

    /**
     * Initialize auth state and listen for changes
     */
    useEffect(() => {
        // Get initial session
        supabase.auth.getSession().then(({ data: { session } }: { data: { session: Session | null } }) => {
            setSession(session);
            setUser(prev => { const next = session?.user ?? null; return prev?.id === next?.id ? prev : next; });
            if (session?.user) {
                checkUserProfile(session.user.id);
                loadUserSettings(session.access_token);
            }
            setLoading(false);
        });

        // Listen for auth state changes
        const {
            data: { subscription },
        } = supabase.auth.onAuthStateChange((_event: string, session: Session | null) => {
            setSession(session);
            setUser(prev => { const next = session?.user ?? null; return prev?.id === next?.id ? prev : next; });
            if (session?.user) {
                checkUserProfile(session.user.id);
                // Only fetch settings on actual sign-in, not on token refresh (tab focus)
                if (_event === 'SIGNED_IN') {
                    loadUserSettings(session.access_token);
                }
            } else {
                setNeedsUsername(false);
                setUsername(null);
                setUserSettings(null);
                setSettingsLoaded(false);
            }
            setLoading(false);
        });

        return () => subscription.unsubscribe();
    }, []);

    // Keep sessionRef current so the syncSetting debounce callback always has a fresh token
    useEffect(() => { sessionRef.current = session; }, [session]);

    const loadUserSettings = async (accessToken: string) => {
        const settings = await getUserSettings(accessToken);
        setUserSettings(settings);
        setSettingsLoaded(true);
    };

    const syncSetting = useCallback((partial: Partial<UserSettingsDB>) => {
        setUserSettings(prev => prev ? { ...prev, ...partial } : { ...partial });
        Object.assign(pendingSettings.current, partial);
        if (syncTimeout.current) clearTimeout(syncTimeout.current);
        syncTimeout.current = setTimeout(async () => {
            const token = sessionRef.current?.access_token;
            if (token && Object.keys(pendingSettings.current).length > 0) {
                await updateUserSettings(token, { ...pendingSettings.current });
            }
            pendingSettings.current = {};
        }, 1500);
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
    const signUp = async (email: string, password: string, username: string) => {
        try {
            const { error } = await supabase.auth.signUp({
                email,
                password,
                options: {
                    data: {
                        username: username,
                    }
                }
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

    /**
     * Check if username is available
     */
    const checkUsernameAvailability = async (username: string): Promise<boolean> => {
        try {
            const { data, error } = await supabase.rpc('is_username_available', {
                username_to_check: username
            });
            if (error) throw error;
            return data as boolean;
        } catch (error) {
            console.error('Error checking username:', error);
            return false;
        }
    };

    /**
     * Update username in profile
     */
    const updateUsername = async (newUsername: string) => {
        if (!user) {
            return { error: new Error('User not authenticated') };
        }

        try {
            const { error: updateError } = await supabase
                .from('profiles')
                .update({ username: newUsername })
                .eq('id', user.id);

            if (updateError) {
                return { error: updateError as Error };
            }

            setUsername(newUsername);
            setNeedsUsername(false);
            return { error: null };
        } catch (error) {
            return { error: error as Error };
        }
    };

    const value = {
        user,
        session,
        loading,
        needsUsername,
        username,
        userSettings,
        settingsLoaded,
        syncSetting,
        signIn,
        signUp,
        signOut,
        signInWithProvider,
        checkUsernameAvailability,
        updateUsername,
        refreshProfile,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
