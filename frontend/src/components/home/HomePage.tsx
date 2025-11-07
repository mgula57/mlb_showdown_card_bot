/**
 * @fileoverview Home page component displaying today's MLB games
 * 
 * The home page serves as the main landing page of the application, providing
 * users with immediate access to current MLB game information. This component
 * focuses on displaying today's games in a clean, accessible format.
 * 
 * Key features:
 * - Displays today's MLB games automatically
 * - Uses current system date for real-time relevance
 * - Integrates with the GamesForDate component for consistent game display
 * - Responsive design with proper spacing and typography
 * 
 * @author MLB Showdown Bot Team
 * @version 4.0
 */

import GamesForDate from "../games/GamesForDate";

/**
 * HomePage - Main landing page component
 * 
 * Displays today's MLB games as the primary content for users visiting
 * the application. The component automatically determines the current date
 * and displays relevant game information.
 * 
 * Features:
 * - **Current Date Detection**: Automatically uses today's date
 * - **Game Integration**: Leverages GamesForDate component for display
 * - **Clean Layout**: Simple, focused design with proper typography
 * - **Responsive**: Adapts to different screen sizes with appropriate padding
 * 
 * The page serves as a gateway to current baseball information, making it
 * easy for users to quickly see what games are happening today without
 * needing to navigate or set date parameters.
 * 
 * @returns {JSX.Element} The home page layout with today's games
 * 
 * @example
 * ```tsx
 * // Used in main app routing
 * <Route path="/" element={<HomePage />} />
 * ```
 */
function HomePage() {
    
    // Generate today's date in YYYY-MM-DD format for API compatibility
    const todayDate = new Date().toISOString().split('T')[0];

    return (
        <div className="px-4">
            {/* Page Header */}
            <span className="text-xl font-black w-full">Games</span>
            
            {/* Today's Games Display */}
            <GamesForDate date={todayDate} />
        </div>
    );
}

export default HomePage;
