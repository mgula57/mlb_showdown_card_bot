/**
 * @fileoverview SideMenu Component
 * 
 * A responsive navigation sidebar that adapts between desktop and mobile layouts:
 * - Desktop: Collapsible sidebar that can expand/collapse while preserving content access
 * - Mobile: Full-screen overlay with scroll lock to prevent background interaction
 * - Smart active item detection based on current route
 * - Scroll lock mechanism with reference counting for overlay scenarios
 * - Smooth animations and transitions for state changes
 * - Integration with theme toggle and logo components
 * 
 * Features include:
 * - Intelligent route-based active item highlighting
 * - Mobile-first responsive design with desktop enhancements
 * - Body scroll locking for mobile overlay mode
 * - Animated expand/collapse with smooth transitions
 * - Accessibility-conscious design with proper focus management
 * 
 * @component
 * @example
 * ```tsx
 * <SideMenu 
 *   isOpen={menuOpen} 
 *   setIsOpen={setMenuOpen} 
 *   isMobile={isMobileView}
 *   className="z-40" 
 * />
 * ```
 */

import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import { FaChevronRight, FaChevronLeft } from "react-icons/fa";
import { FaXmark } from "react-icons/fa6";
import { SideMenuItem, sideMenuItems } from "./SideMenuItem";
import { type SideMenuItem as SideMenuItemType } from "../../types/SideMenuItem";
import ShowdownBotLogo from "../shared/ShowdownBotLogo";
import ThemeToggleButton from "./ThemeToggleButton";

/**
 * Props for the SideMenu component
 */
type SideMenuProps = {
    /** Controls whether the side menu is expanded (true) or collapsed (false) */
    isOpen: boolean;
    /** State setter function to control menu open/closed state */
    setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
    /** Optional CSS classes for additional styling */
    className?: string;
    /** Indicates if the menu should behave as mobile overlay (scroll lock enabled) */
    isMobile?: boolean;
};

// Global reference counter for body scroll lock to handle multiple concurrent overlays
let bodyScrollLockCount = 0;
    
/**
 * Responsive navigation sidebar with mobile overlay and desktop collapsible modes
 * 
 * This component provides sophisticated navigation behavior that adapts to different
 * screen sizes and user interaction patterns:
 * 
 * **Desktop Mode:**
 * - Collapsible sidebar that can expand/collapse in place
 * - Icons remain visible when collapsed for quick access
 * - Smooth width transitions without affecting layout
 * 
 * **Mobile Mode:**
 * - Full-screen overlay with backdrop
 * - Body scroll locking to prevent background interaction
 * - Automatic menu closure after navigation for better UX
 * 
 * **Smart Active Detection:**
 * - Route-based highlighting with prefix matching for nested routes
 * - Fallback logic for consistent active state indication
 * 
 * @param props - Component props
 * @returns Responsive navigation sidebar with adaptive behavior
 */
const SideMenu: React.FC<SideMenuProps> = ({ isOpen, setIsOpen, className, isMobile }) => {

    // Get current route for active menu item detection
    const location = useLocation();

    /**
     * Determines the currently active menu item based on the current route
     * - Exact path matching takes priority
     * - Prefix matching for nested routes (except root '/')
     * - Fallback to home item if no match found
     */
    const selectedMenuItem = sideMenuItems.find(item => 
        location.pathname === item.path || 
        (item.path !== '/' && location.pathname.startsWith(item.path))
    ) || sideMenuItems.find(item => item.path === '/'); // Fallback to home

    /**
     * Toggles the menu's open/closed state
     * Connected to parent component state for coordinated behavior
     */
    const handleToggle = () => {
        setIsOpen(!isOpen);
    };

    /**
     * Handles menu item selection and navigation
     * - Logs selection for debugging/analytics
     * - Auto-closes menu on mobile for better UX after navigation
     * 
     * @param item - The selected menu item
     */
    const handleMenuItemClick = (item: SideMenuItemType) => {
        console.log(`Selected menu item: ${item.text}`);
        if (isMobile) setIsOpen(false); // Close menu on mobile after selection
    };

    // Refs for scroll lock mechanism
    const scrollYRef = React.useRef(0);              // Stores scroll position for restoration
    const didAcquireLockRef = React.useRef(false);   // Tracks if this component holds a lock

    /**
     * Effect: Advanced body scroll lock mechanism for mobile overlay mode
     * 
     * Implements sophisticated scroll locking that:
     * - Uses reference counting to handle multiple concurrent overlays
     * - Preserves exact scroll position during lock/unlock cycles
     * - Compensates for scrollbar width to prevent layout shifts
     * - Only applies to mobile overlay mode (not desktop sidebar)
     * - Ensures proper cleanup on component unmount
     * 
     * The lock mechanism works by:
     * 1. Storing current scroll position
     * 2. Setting body to fixed position at negative top offset
     * 3. Adding padding to compensate for hidden scrollbar
     * 4. Restoring exact position when unlocking
     */
    React.useEffect(() => {
        if (typeof window === 'undefined') return;

        /**
         * Acquires a scroll lock if not already held by this component
         * Only the first lock request globally applies the actual body styles
         */
        const acquireLock = () => {
            if (didAcquireLockRef.current) return;
            
            bodyScrollLockCount += 1;
            if (bodyScrollLockCount === 1) {
                const body = document.body;
                const docEl = document.documentElement;
                
                // Calculate scrollbar width to prevent layout shift
                const scrollbarWidth = Math.max(0, window.innerWidth - docEl.clientWidth);

                // Store current scroll position for restoration
                scrollYRef.current = window.scrollY;
                
                // Apply scroll lock styles
                body.style.position = 'fixed';
                body.style.top = `-${scrollYRef.current}px`;
                body.style.width = '100%';
                if (scrollbarWidth) body.style.paddingRight = `${scrollbarWidth}px`;
            }
            didAcquireLockRef.current = true;
        };

        /**
         * Releases the scroll lock held by this component
         * Only removes body styles when no other components hold locks
         */
        const releaseLock = () => {
            if (!didAcquireLockRef.current) return;
            
            didAcquireLockRef.current = false;
            if (bodyScrollLockCount > 0) bodyScrollLockCount -= 1;
            
            // Only restore scroll when all locks are released
            if (bodyScrollLockCount === 0) {
                const body = document.body;
                
                // Remove lock styles
                body.style.position = '';
                body.style.top = '';
                body.style.width = '';
                body.style.paddingRight = '';
                
                // Restore exact scroll position
                const y = scrollYRef.current || 0;
                window.scrollTo(0, y);
            }
        };

        // Only apply scroll lock for mobile overlay mode (not desktop sidebar)
        const shouldLock = isOpen && (isMobile === true);

        if (shouldLock) acquireLock();
        else releaseLock();

        return () => {
            // Ensure cleanup releases any held lock
            releaseLock();
        };
    }, [isOpen, isMobile]);

    return (
        <aside className={`min-h-dvh fixed left-0 top-0 ${className}`}>
            {/* Main navigation container with responsive width and smooth transitions */}
            <nav className={`
                min-h-dvh ${isOpen ? 'w-64 md:w-48' : 'w-14'} space-y-4
                bg-secondary border-r-divider shadow-sm
                transition-all duration-300 ease-in-out
                flex flex-col
                ${isOpen ? '' : 'items-center justify-center'}
            `}>
                {/* Header Section: Logo and Toggle Button */}
                <div className={`${isOpen ? 'flex space-x-2' : ''} h-12 p-4 pb-2 w-full items-center cursor-pointer`}>
                    
                    {/* Logo - Only visible when menu is expanded */}
                    {isOpen && 
                        <NavLink to="/" className={`${isOpen ? 'w-7/8' : 'w-full'} flex items-center`}>
                            <ShowdownBotLogo/>
                        </NavLink>
                    }

                    {/* Menu Toggle Button - Adaptive icon based on state and device type */}
                    <button 
                        onClick={handleToggle} 
                        className="hover:text-secondary transition-colors duration-200 cursor-pointer"
                        aria-label={isOpen ? 'Close menu' : 'Open menu'}
                    >
                        {isOpen ? (isMobile ? <FaXmark className="h-8 w-8" /> : <FaChevronLeft />) : <FaChevronRight className="w-6" />}
                    </button>
                    
                </div>

                {/* Navigation Items - Scrollable list with responsive spacing */}
                <ul className="flex-1 space-y-2 overflow-y-auto px-2 w-full">
                    {sideMenuItems.map((item) => (
                        <li key={item.path}>
                            <SideMenuItem
                                item={item}
                                isSideMenuOpen={isOpen}
                                selectedItem={selectedMenuItem}
                                onClick={handleMenuItemClick}
                            />
                        </li>
                    ))}
                </ul>

                {/* Footer Section: Theme Toggle with Responsive Padding */}
                <div className="p-2 pb-10 sm:pb-auto">
                    <ThemeToggleButton />
                </div>

            </nav>

        </aside>
    );
};

export default SideMenu;