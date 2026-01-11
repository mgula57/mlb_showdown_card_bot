/**
 * @fileoverview AppLayout Component
 * 
 * The main application layout component that orchestrates the overall structure
 * and behavior of the MLB Showdown Bot interface. Provides:
 * 
 * **Layout Structure:**
 * - Responsive sidebar navigation (desktop collapsible, mobile overlay)
 * - Fixed/sticky header with adaptive behavior for iOS Safari
 * - Main content area with proper spacing and overflow handling
 * - Modal system integration for feature announcements
 * 
 * **Advanced Features:**
 * - Dual sidebar state management (desktop/mobile with separate localStorage)
 * - iOS Safari-specific viewport handling to prevent URL bar jitter
 * - Route-based header title and icon detection
 * - Global Showdown set selection in header
 * - Automatic "What's New" modal system with version tracking
 * 
 * **Responsive Behavior:**
 * - Desktop: Collapsible sidebar with content padding adjustment
 * - Mobile: Overlay sidebar with backdrop and scroll lock
 * - Header: Adaptive logo visibility based on sidebar state
 * - iOS: Special handling for Safari's dynamic viewport
 * 
 * **State Persistence:**
 * - Sidebar open/closed state saved to localStorage
 * - Separate mobile and desktop sidebar preferences
 * - User's Showdown set selection persistence
 * - "What's New" modal acknowledgment tracking
 * 
 * @component
 * @example
 * ```tsx
 * <AppLayout>
 *   <YourPageContent />
 * </AppLayout>
 * ```
 */

import React, { type ReactNode, useState, useEffect, useRef } from "react";
import SideMenu from "./side_menu/SideMenu";
import ShowdownBotLogo from "./shared/ShowdownBotLogo";
import { useLocation } from "react-router-dom";
import { useSiteSettings, showdownSets } from "./shared/SiteSettingsContext";
import CustomSelect from "./shared/CustomSelect";
import { FiMenu } from "react-icons/fi";
import { sideMenuItems } from "./side_menu/SideMenuItem";
import { WhatsNewModal, hasSeenWhatsNew, markWhatsNewAsSeen } from "./side_menu/WhatsNewModal";
import { fetchFeatureStatuses, type FeatureStatus } from "../api/status/feature_status";
import { FaExclamationCircle } from 'react-icons/fa';

/**
 * Props for the AppLayout component
 */
type AppLayoutProps = {
    /** React children to render in the main content area */
    children: ReactNode;
};

// localStorage keys for persisting sidebar state across sessions
/** Key for desktop sidebar open/closed state */
const SIDE_MENU_STORAGE_KEY = 'showdown-bot-side-menu-open';
/** Key for mobile sidebar open/closed state (separate from desktop) */
const SIDE_MENU_STORAGE_KEY_MOBILE = 'showdown-bot-side-menu-open-mobile';

/**
 * Main application layout component with responsive sidebar and adaptive header
 * 
 * This component serves as the primary layout shell for the entire application,
 * managing complex interactions between:
 * - Responsive navigation (desktop sidebar vs mobile overlay)
 * - Header behavior across different devices and browsers
 * - Global state management for user preferences
 * - Modal systems for feature announcements
 * - Route-based UI adaptations
 * 
 * **Key Responsibilities:**
 * - Coordinate sidebar behavior between desktop and mobile contexts
 * - Handle iOS Safari's dynamic viewport challenges
 * - Manage global user preferences (theme, Showdown set)
 * - Integrate feature announcement system
 * - Provide consistent layout structure for all pages
 * 
 * @param props - Component props
 * @returns Complete application layout structure
 */
const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {

    // Desktop sidebar state with localStorage persistence
    const [isSideMenuOpen, setIsSideMenuOpen] = useState(() => {
        try {
            const stored = localStorage.getItem(SIDE_MENU_STORAGE_KEY);
            return stored !== null ? JSON.parse(stored) : true; // Default to open on desktop
        } catch {
            return true; // Fallback to open if localStorage fails
        }
    });

    // Mobile sidebar state with separate localStorage tracking
    const [isSideMenuOpenMobile, setIsSideMenuOpenMobile] = useState(() => {
        try {
            const stored = localStorage.getItem(SIDE_MENU_STORAGE_KEY_MOBILE);
            return stored !== null ? JSON.parse(stored) : false; // Default to closed on mobile
        } catch {
            return false; // Fallback to closed if localStorage fails
        }
    });
    const hasCheckedFeatures = useRef(false);
    const featureStatuses = useRef<Record<string, FeatureStatus>>({});

    // When loaded, check feature statuses
    useEffect(() => {
        if (hasCheckedFeatures.current) return;
        
        const checkFeatures = async () => {
            hasCheckedFeatures.current = true;
            const statuses = await fetchFeatureStatuses();
            featureStatuses.current = statuses;
            console.log('Feature Statuses:', statuses);
        };
        checkFeatures();
    }, []);

    // Modal state for "What's New" feature announcements
    const [showWhatsNewModal, setShowWhatsNewModal] = useState(false);
    
    // Global site settings from context
    const { userShowdownSet, setUserShowdownSet } = useSiteSettings();

    // Calculate main content padding based on desktop sidebar state
    const contentPadding = isSideMenuOpen ? 'md:pl-48' : 'md:pl-14';
    
    // Get current route information for header title and icon
    const location = useLocation();
    const locationName = location.pathname.split('/')[1] || 'customs';

    // Find the corresponding menu item for the current route
    const selectedMenuItem = sideMenuItems.find(item => item.path.includes(locationName));
    const selectedMenuItemStatus = selectedMenuItem ? featureStatuses.current[selectedMenuItem.text.toLowerCase()] : null;

    /**
     * Effect: Persist desktop sidebar state to localStorage
     * Saves user's sidebar preference for consistent experience across sessions
     */
    useEffect(() => {
        try {
            localStorage.setItem(SIDE_MENU_STORAGE_KEY, JSON.stringify(isSideMenuOpen));
        } catch (error) {
            console.warn('Failed to save side menu state to localStorage:', error);
        }
    }, [isSideMenuOpen]);

    /**
     * Effect: Initialize "What's New" modal display
     * 
     * Checks if user has seen the current version's announcements and
     * displays the modal after a brief delay to allow the app to settle.
     * The delay prevents jarring modal appearance during initial load.
     */
    useEffect(() => {
        const timer = setTimeout(() => {
            if (!hasSeenWhatsNew()) {
                setShowWhatsNewModal(true);
            }
        }, 1000); // 1 second delay for smooth UX

        return () => clearTimeout(timer);
    }, []);

    /**
     * Handles closing of the "What's New" modal
     * Marks the current version as seen and closes the modal
     */
    const handleWhatsNewClose = () => {
        setShowWhatsNewModal(false);
        markWhatsNewAsSeen();
    };

    /**
     * iOS Safari Detection for Viewport Handling
     * 
     * Detects iOS Safari to apply special handling for the dynamic viewport
     * that changes when the URL bar collapses/expands. This prevents layout
     * jitter and provides a smoother user experience on iOS devices.
     * 
     * Detection criteria:
     * - iOS device (iPhone, iPad, iPod)
     * - Safari browser (not Chrome or Firefox on iOS)
     * - Client-side only (typeof window check)
     */
    const isIOSSafari =
        typeof window !== 'undefined' &&
        /iP(hone|od|ad)/.test(navigator.userAgent) &&
        /Safari/.test(navigator.userAgent) &&
        !/CriOS|FxiOS/.test(navigator.userAgent);

    return (
        <div className="bg-primary flex relative">
            {/* Desktop Sidebar - Hidden on mobile, collapsible on desktop */}
            <SideMenu 
                className="hidden md:block" 
                isOpen={isSideMenuOpen} 
                setIsOpen={setIsSideMenuOpen} 
            />

            {/* Mobile Overlay Sidebar - Full-screen overlay with backdrop */}
            {isSideMenuOpenMobile && (
                <div className="fixed inset-0 z-40 md:hidden">
                    {/* Backdrop - Click to close sidebar */}
                    <div
                        className="absolute inset-0 bg-black/40"
                        onClick={() => setIsSideMenuOpenMobile(false)}
                        aria-hidden="true"
                    />
                    {/* Sidebar with mobile-specific behavior */}
                    <SideMenu 
                        isOpen={true} 
                        setIsOpen={setIsSideMenuOpenMobile} 
                        isMobile={true} 
                    />
                </div>
            )}


            {/* Main Content Container with responsive padding for sidebar */}
            <div className={`flex flex-col h-full w-full transition-[padding-left] duration-300 ${contentPadding}`}>
                
                {/* Application Header - Adaptive positioning for iOS Safari */}
                <header
                    className={`
                        ${isIOSSafari ? 'fixed left-0 right-0 top-0' : 'sticky top-0'}
                        z-30 flex h-12 p-4 w-full items-center justify-between
                        border-b-gray-600 shadow-md bg-primary/95 backdrop-blur
                    `}
                    // Ensure header respects device notch and status bar on iOS
                    style={isIOSSafari ? { boxSizing: 'border-box' } : undefined}
                >
                    {/* Left Section: Menu Button, Logo, and Page Title */}
                    <div className="flex items-center space-x-4">

                        {/* Mobile Menu Button - Only visible on mobile */}
                        <button
                            type="button"
                            className="
                                md:hidden inline-flex items-center justify-center p-2 
                                rounded-md border border-form-element 
                                text-secondary hover:bg-background-secondary
                                cursor-pointer
                            "
                            aria-label="Open navigation menu"
                            onClick={() => setIsSideMenuOpenMobile(true)}
                        >
                            <FiMenu className="h-5 w-5" />
                        </button>
                        
                        {/* Logo Display Logic */}
                        {/* Always show on mobile */}
                        <ShowdownBotLogo className="max-w-48 md:hidden" />
                        {/* Show on desktop only when sidebar is collapsed */}
                        {!isSideMenuOpen && <ShowdownBotLogo className="max-w-48 hidden md:block" />}
                        
                        {/* Page Title with Icon - Route-based content */}
                        {(selectedMenuItem?.text || 'Home') !== 'Home' && (
                            <h1 className="hidden sm:flex sm:flex-row text-xl font-semibold text-secondary items-center">
                                {selectedMenuItem?.icon && <selectedMenuItem.icon className="w-5 h-5 mr-2" />}
                                {selectedMenuItem?.text || 'Home'}
                            </h1>
                        )}
                    </div>

                    {/* Right Section: Showdown Set Selector */}
                    <CustomSelect
                        className="font-showdown-set-italic w-20 text-xl"
                        buttonClassName="flex justify-center cursor-pointer select-none"
                        imageClassName="object-contain object-center"
                        value={userShowdownSet}
                        onChange={setUserShowdownSet}
                        options={showdownSets}
                    />
                    
                </header>

                {/* iOS Safari Spacer - Maintains layout when header is fixed */}
                {isIOSSafari && <div style={{ height: '3rem' /* matches h-12 */ }} aria-hidden="true" />}

                {/* Main Content Area - Scrollable container for page content */}
                <main className={`flex-1 overflow-auto w-full relative`}>
                    {/* Status Message */}
                    {selectedMenuItemStatus && (
                        <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 m-4 rounded" role="alert">
                            <div className="font-bold items-center flex">
                                <FaExclamationCircle className="inline mr-1" />
                                Update in Progress
                            </div>
                            <p>{selectedMenuItemStatus.message || 'This feature is currently disabled.'}</p>
                        </div>
                    )}
                    {/* Main Content */}
                    {children}
                </main>
            </div>

            {/* Feature Announcement Modal - Global modal for version updates */}
            <WhatsNewModal 
                isOpen={showWhatsNewModal} 
                onClose={handleWhatsNewClose} 
            />
            
        </div>
    );
};

export default AppLayout;
