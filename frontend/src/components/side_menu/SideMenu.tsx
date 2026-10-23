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
import { FaChevronRight } from "react-icons/fa";
import { FaXmark } from "react-icons/fa6";
import { SideMenuItem } from "./SideMenuItem";
import { sideMenuItems, sideMenuSections, accountMenuItem } from "./sideMenuConfig";
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

    /**
     * Sliding active-tab indicator
     *
     * A single highlight is positioned under the selected item and glides between items on
     * route change, instead of each item toggling its own background. It lives on the nav
     * (not the item list) so it can travel down to Account in the footer. The first
     * measurement snaps into place (no slide in from the top on mount); later ones animate.
     */
    const navRef = React.useRef<HTMLElement>(null);
    const [indicator, setIndicator] = React.useState<{ top: number; height: number } | null>(null);
    const [indicatorCanAnimate, setIndicatorCanAnimate] = React.useState(false);

    React.useLayoutEffect(() => {
        const nav = navRef.current;
        if (!nav) return;
        const measure = () => {
            const el = nav.querySelector<HTMLElement>('[data-selected="true"]');
            if (!el) return setIndicator(null);
            const top = el.getBoundingClientRect().top - nav.getBoundingClientRect().top;
            setIndicator({ top, height: el.offsetHeight });
        };
        measure();
        const observer = new ResizeObserver(measure);
        observer.observe(nav);
        return () => observer.disconnect();
    }, [selectedMenuItem?.path]);

    React.useEffect(() => {
        if (!indicator || indicatorCanAnimate) return;
        const frame = requestAnimationFrame(() => setIndicatorCanAnimate(true));
        return () => cancelAnimationFrame(frame);
    }, [indicator, indicatorCanAnimate]);

    return (
        // min-h-lvh (not dvh) — dvh shrinks/grows live as Safari's URL bar animates,
        // and since this is a top-anchored full-screen mobile overlay, that live
        // resize can lag a frame and expose a gap (a black bar) at the bottom edge.
        // lvh is fixed to the large/max viewport, so it always overshoots past the
        // visible area and bleeds under the URL bar instead of leaving a gap.
        <aside className={`min-h-lvh fixed left-0 top-0 ${className}`}>
            {/* Main navigation container. Only the width animates; inner layout is identical in
                both states so content clips/fades rather than reflowing mid-transition. */}
            <nav ref={navRef} className={`
                relative min-h-lvh ${isOpen ? 'w-64 md:w-52' : 'w-16'} space-y-4
                bg-secondary shadow-sm overflow-hidden
                transition-[width] duration-300 ease-(--side-menu-ease) motion-reduce:transition-none
                flex flex-col
                border-r-2 border-form-element
            `}>
                {/* Header Section: Logo and Toggle Button */}
                <div className="flex items-center h-12 px-2 pt-2 w-full">

                    {/* Logo - fixed width inside a shrinking, clipped slot so it fades rather than squishes */}
                    <div
                        className={`
                            min-w-0 flex-1 overflow-hidden
                            transition-opacity duration-300 ease-(--side-menu-ease) motion-reduce:transition-none
                            ${isOpen ? 'opacity-100 delay-100' : 'opacity-0 duration-100! pointer-events-none'}
                        `}
                        aria-hidden={!isOpen}
                    >
                        <NavLink to="/" tabIndex={isOpen ? 0 : -1} className="flex items-center w-32 pl-2">
                            <ShowdownBotLogo/>
                        </NavLink>
                    </div>

                    {/* Menu Toggle Button - one chevron that rotates; X on mobile */}
                    <button 
                        onClick={handleToggle} 
                        className="flex items-center justify-center w-12 h-10 shrink-0 rounded-md text-(--quaternary) hover:text-(--primary) hover:bg-(--background-primary) transition-colors duration-150 cursor-pointer"
                        aria-label={isOpen ? 'Close menu' : 'Open menu'}
                        aria-expanded={isOpen}
                    >
                        {isMobile 
                            ? <FaXmark className="h-6 w-6" />
                            : <FaChevronRight className={`transition-transform duration-300 ease-(--side-menu-ease) motion-reduce:transition-none ${isOpen ? 'rotate-180' : ''}`} />
                        }
                    </button>
                    
                </div>

                {/* Sliding active-tab indicator: filled pill + accent bar on the leading edge */}
                {indicator && (
                    <div
                        aria-hidden="true"
                        className={`
                            absolute left-2 right-2 top-0 z-0 m-0! rounded-md bg-tertiary pointer-events-none
                            ${indicatorCanAnimate ? 'transition-[transform,height] duration-300 ease-(--side-menu-ease) motion-reduce:transition-none' : ''}
                        `}
                        style={{ transform: `translateY(${indicator.top}px)`, height: indicator.height }}
                    >
                        {/* Accent bar only when expanded — in the narrow rail the pill alone reads clearly */}
                        <span className={`
                            absolute left-0 top-1/2 -translate-y-1/2 h-6 w-1 rounded-r-full bg-(--showdown-blue)
                            transition-opacity duration-300 ease-(--side-menu-ease) motion-reduce:transition-none
                            ${isOpen ? 'opacity-100' : 'opacity-0'}
                        `} />
                    </div>
                )}

                {/* Navigation Sections - Scrollable list */}
                <ul className="flex-1 space-y-3 overflow-y-auto overflow-x-hidden px-2 w-full">
                    {sideMenuSections.map((section, index) => (
                        <li key={section.title ?? index}>
                            {section.title && (
                                // Fixed height in both states so items don't shift while the menu animates:
                                // the label and the collapsed-rail divider just cross-fade in place.
                                <div className="relative h-5 mb-1">
                                    <span
                                        aria-hidden={!isOpen}
                                        className={`
                                            absolute inset-0 flex items-center pl-3 whitespace-nowrap overflow-hidden
                                            text-[10px] font-semibold uppercase tracking-wider text-(--quaternary)
                                            transition-opacity duration-300 ease-(--side-menu-ease) motion-reduce:transition-none
                                            ${isOpen ? 'opacity-100 delay-100' : 'opacity-0 duration-100!'}
                                        `}
                                    >
                                        {section.title}
                                    </span>
                                    <span
                                        aria-hidden="true"
                                        className={`
                                            absolute left-1/2 top-1/2 -translate-x-1/2 h-px w-8 bg-(--divider)
                                            transition-opacity duration-300 ease-(--side-menu-ease) motion-reduce:transition-none
                                            ${isOpen ? 'opacity-0 duration-100!' : 'opacity-100'}
                                        `}
                                    />
                                </div>
                            )}
                            <ul className="space-y-2">
                                {section.items.map((item) => (
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
                        </li>
                    ))}
                </ul>

                {/* Footer Section: Account + Theme Toggle, pinned below the sections */}
                <div className="px-2 pt-2 pb-10 sm:pb-auto space-y-2 border-t border-form-element">
                    <SideMenuItem
                        item={accountMenuItem}
                        isSideMenuOpen={isOpen}
                        selectedItem={selectedMenuItem}
                        onClick={handleMenuItemClick}
                    />
                    <ThemeToggleButton isSideMenuOpen={isOpen} />
                </div>

            </nav>

        </aside>
    );
};

export default SideMenu;