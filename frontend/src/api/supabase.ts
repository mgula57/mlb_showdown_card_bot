/**
 * @fileoverview Supabase Client Configuration
 * 
 * Initializes and exports the Supabase client for authentication and database operations.
 * This client is configured using environment variables for the Supabase project URL and API key.
 * 
 * @see https://supabase.com/docs/reference/javascript
 */

import { createClient } from '@supabase/supabase-js';

// Supabase project URL from environment variables
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
// Supabase anonymous/public API key from environment variables
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
    console.error('Missing Supabase environment variables. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your .env file.');
}

/**
 * Supabase client instance for authentication and database operations
 * 
 * This client provides access to:
 * - Authentication (supabase.auth)
 * - Database queries (supabase.from())
 * - Real-time subscriptions
 * - Storage operations
 * 
 * @example
 * ```typescript
 * // Sign in with email/password
 * const { data, error } = await supabase.auth.signInWithPassword({
 *   email: 'user@example.com',
 *   password: 'password123'
 * });
 * ```
 */
export const supabase = createClient(supabaseUrl, supabaseAnonKey);
