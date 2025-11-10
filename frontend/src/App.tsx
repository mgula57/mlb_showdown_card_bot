
/**
 * @fileoverview App Component - Main Application Entry Point
 * 
 * The root component that orchestrates the entire MLB Showdown Bot application.
 * Implements a custom routing strategy that maintains component state across
 * navigation by keeping all major components mounted and using visibility
 * toggling instead of traditional route-based mounting/unmounting.
 * 
 * **Architecture Decisions:**
 * - Custom routing via visibility toggling instead of React Router's component mounting
 * - Always-mounted components for state preservation and faster navigation
 * - Global context providers for site-wide settings and theme management
 * - Centralized layout management through AppLayout wrapper
 * 
 * **Benefits of This Approach:**
 * - Preserves component state across navigation (form inputs, scroll positions, etc.)
 * - Eliminates component re-initialization overhead for faster navigation
 * - Maintains complex UI state (modals, expanded sections) when switching routes
 * - Reduces unnecessary API calls and data fetching on route changes
 * 
 * **Trade-offs:**
 * - Higher initial memory usage (all components loaded upfront)
 * - More complex visibility logic compared to standard routing
 * - Potential SEO considerations for single-page architecture
 * 
 * @component
 */

import { BrowserRouter, useLocation } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import CustomCardBuilder from "./components/customs/CustomCardBuilder";
import { SiteSettingsProvider } from "./components/shared/SiteSettingsContext";
import ShowdownCardExplore from "./components/cards/ShowdownCardExplore";

/**
 * Inner application content component that handles route-based visibility
 * 
 * This component implements a custom routing strategy where all major page
 * components remain mounted but have their visibility toggled based on the
 * current route. This approach preserves component state across navigation,
 * providing a smoother user experience and faster page transitions.
 * 
 * **Routing Logic:**
 * - `/` and `/customs` routes display the CustomCardBuilder
 * - `/explore` route displays the ShowdownCardExplore component
 * - Components use CSS visibility (`block`/`hidden`) instead of conditional rendering
 * - All components receive state about their visibility for internal optimizations
 * 
 * **State Preservation Benefits:**
 * - Form inputs remain filled when navigating away and back
 * - Scroll positions are maintained within components
 * - Modal states and expanded sections persist across routes
 * - Search filters and table states are preserved
 * - Component initialization overhead is eliminated on repeat visits
 * 
 * @returns Application content with route-based visibility management
 */
const AppContent = () => {
    const location = useLocation();

    return (
        <AppLayout>
            {/* Custom Card Builder - Visible on root and customs routes */}
            <div className={['/customs', '/'].includes(location.pathname) ? 'block' : 'hidden'}>
                <CustomCardBuilder isHidden={location.pathname !== '/customs'} />
            </div>
            
            {/* Card Explorer - Visible on explore route */}
            <div className={location.pathname === '/explore' ? 'block' : 'hidden'}>
                <ShowdownCardExplore />
            </div>
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
            <SiteSettingsProvider>
                <AppContent />
            </SiteSettingsProvider>
        </BrowserRouter>
    );
}

export default App;
