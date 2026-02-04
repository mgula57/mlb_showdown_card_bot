
/**
 * @fileoverview App Component - Main Application Entry Point
 * 
 * The root component that orchestrates the entire MLB Showdown Bot application.
 * Implements a custom routing strategy that maintains component state across
 * navigation by keeping all major components mounted and using visibility
 * toggling instead of traditional route-based mounting/unmounting.
 * 
 * **Architecture Decisions:**
 * - Lazy mounting strategy: components load only when first visited
 * - State preservation via visibility toggling after initial mount
 * - Global context providers for site-wide settings and theme management
 * - Centralized layout management through AppLayout wrapper
 * 
 * **Benefits of This Approach:**
 * - Faster initial page load (only loads current route)
 * - Lower initial memory footprint
 * - Preserves component state across navigation (form inputs, scroll positions, etc.)
 * - Eliminates component re-initialization overhead after first visit
 * - Maintains complex UI state (modals, expanded sections) when switching routes
 * - Reduces unnecessary API calls and data fetching on route changes
 * 
 * **Trade-offs:**
 * - Slight delay on first visit to each route (mounting overhead)
 * - Memory grows as user explores more pages
 * - More complex visibility logic compared to standard routing
 * - Potential SEO considerations for single-page architecture
 * 
 * @component
 */

import { BrowserRouter, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import AppLayout from "./components/AppLayout";
import CustomCardBuilder from "./components/customs/CustomCardBuilder";
import { SiteSettingsProvider } from "./components/shared/SiteSettingsContext";
import { AuthProvider } from "./components/auth/AuthContext";
import Explore from "./components/explore/explore";
import Home from "./components/Home";

/**
 * Inner application content component that handles route-based visibility
 * 
 * This component implements a lazy mounting strategy with state preservation.
 * Components are only mounted when first visited, then remain mounted (but hidden)
 * to preserve their state across navigation.
 * 
 * **Routing Logic:**
 * - Components mount only on first visit (reduces initial load)
 * - Once mounted, they stay mounted but toggle visibility
 * - State is preserved across all subsequent navigations
 * 
 * **Lazy Mounting Benefits:**
 * - Faster initial page load (only loads current route)
 * - Reduced memory usage until pages are visited
 * - State still preserved after first visit
 * - Network requests only fire when user actually visits a page
 * 
 * **State Preservation Benefits:**
 * - Form inputs remain filled when navigating away and back
 * - Scroll positions are maintained within components
 * - Modal states and expanded sections persist across routes
 * - Search filters and table states are preserved
 * - Component initialization overhead is eliminated on repeat visits
 * 
 * @returns Application content with lazy mounting and route-based visibility management
 */
const AppContent = () => {
    const location = useLocation();
    
    // Initialize with current route only (don't mount home unless user is on home)
    const [mountedRoutes, setMountedRoutes] = useState<Set<string>>(() => {
        const initialPath = location.pathname === '/home' ? '/' : location.pathname;
        return new Set([initialPath]);
    });

    // Track which routes have been visited to enable lazy mounting
    useEffect(() => {
        const currentPath = location.pathname === '/home' ? '/' : location.pathname;
        setMountedRoutes(prev => new Set([...prev, currentPath]));
    }, [location.pathname]);

    const isActive = (path: string) => {
        if (path === '/') {
            return location.pathname === '/' || location.pathname === '/home';
        }
        return location.pathname === path;
    };

    return (
        <AppLayout>
            {/* Home Page - Mount on initial load */}
            {mountedRoutes.has('/') && (
                <div className={isActive('/') ? 'block' : 'hidden'}>
                    <Home />
                </div>
            )}

            {/* Custom Card Builder - Mount when first visited */}
            {mountedRoutes.has('/customs') && (
                <div className={isActive('/customs') ? 'block' : 'hidden'}>
                    <CustomCardBuilder isHidden={!isActive('/customs')} />
                </div>
            )}

            {/* Card Explorer - Mount when first visited */}
            {mountedRoutes.has('/explore') && (
                <div className={isActive('/explore') ? 'block' : 'hidden'}>
                    <Explore />
                </div>
            )}
        </AppLayout>
    );
};

/**
 * Root Application Component
 * 
 * The main App component that establishes the application's foundation by
 * providing essential context providers and routing infrastructure.
 * 
 * **Provider Hierarchy:**
 * 1. **BrowserRouter**: Enables client-side routing with HTML5 history API
 * 2. **SiteSettingsProvider**: Provides global state for user preferences
 *    - Theme management (light/dark/system)
 *    - MLB Showdown set selection
 *    - localStorage persistence for user settings
 * 3. **AppContent**: Custom routing logic with state preservation
 * 
 * **Architecture Pattern:**
 * This follows the "Provider > Router > App Content" pattern where:
 * - Global state is established at the highest level
 * - Routing context is provided to enable navigation
 * - Application content can access both global state and routing
 * 
 * **Context Access:**
 * Components within this hierarchy can access:
 * - `useLocation()`, `useNavigate()` from React Router
 * - `useSiteSettings()`, `useTheme()` from SiteSettingsContext
 * - All routing and global state management capabilities
 * 
 * @returns Complete application with routing and global state management
 */
function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <SiteSettingsProvider>
                    <AppContent />
                </SiteSettingsProvider>
            </AuthProvider>
        </BrowserRouter>
    );
}

export default App;
