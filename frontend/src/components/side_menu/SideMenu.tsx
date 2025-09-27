import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import { FaChevronRight, FaChevronLeft } from "react-icons/fa";
import { FaXmark } from "react-icons/fa6";
import { SideMenuItem, sideMenuItems } from "./SideMenuItem";
import { type SideMenuItem as SideMenuItemType } from "../../types/SideMenuItem";
import ShowdownBotLogo from "../shared/ShowdownBotLogo";
import ThemeToggleButton from "./ThemeToggleButton";

/** Interface for the side menu props. */
type SideMenuProps = {
    isOpen: boolean;
    setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
    className?: string;
    isMobile?: boolean;
};

// module-level lock so multiple overlays won't fight
let bodyScrollLockCount = 0;
    
/** Dynamic side menu component that displays navigation links. */
const SideMenu: React.FC<SideMenuProps> = ({ isOpen, setIsOpen, className, isMobile }) => {

    // State to manage the selected item
    const location = useLocation();

    // Find the currently selected menu item based on the current path
    const selectedMenuItem = sideMenuItems.find(item => 
        location.pathname === item.path || 
        (item.path !== '/' && location.pathname.startsWith(item.path))
    ) || sideMenuItems.find(item => item.path === '/'); // Fallback to home


    // Toggle side menu open/close state
    // Linked to parent component state
    const handleToggle = () => {
        setIsOpen(!isOpen);
    };

    // Set the selected menu item when clicked.
    const handleMenuItemClick = (item: SideMenuItemType) => {
        console.log(`Selected menu item: ${item.text}`);
        if (isMobile) setIsOpen(false); // Close menu on mobile after selection
    };

    // Preserve scroll position while side menu is open
    const scrollYRef = React.useRef(0);
    const didAcquireLockRef = React.useRef(false);

    React.useEffect(() => {
        if (typeof window === 'undefined') return;

        const acquireLock = () => {
            if (didAcquireLockRef.current) return;
            bodyScrollLockCount += 1;
            if (bodyScrollLockCount === 1) {
                const body = document.body;
                const docEl = document.documentElement;
                const scrollbarWidth = Math.max(0, window.innerWidth - docEl.clientWidth);

                scrollYRef.current = window.scrollY;
                body.style.position = 'fixed';
                body.style.top = `-${scrollYRef.current}px`;
                body.style.width = '100%';
                if (scrollbarWidth) body.style.paddingRight = `${scrollbarWidth}px`;
            }
            didAcquireLockRef.current = true;
        };

        const releaseLock = () => {
            if (!didAcquireLockRef.current) return;
            didAcquireLockRef.current = false;
            if (bodyScrollLockCount > 0) bodyScrollLockCount -= 1;
            if (bodyScrollLockCount === 0) {
                const body = document.body;
                body.style.position = '';
                body.style.top = '';
                body.style.width = '';
                body.style.paddingRight = '';
                const y = scrollYRef.current || 0;
                window.scrollTo(0, y);
            }
        };

        // Only lock when the menu behaves as an overlay.
        // If isMobile === false then the menu is a slide (not overlay) and we should not lock.
        const shouldLock = isOpen && (isMobile !== false);

        if (shouldLock) acquireLock();
        else releaseLock();

        return () => {
            // Ensure we release any lock held by this effect on cleanup.
            releaseLock();
        };
    }, [isOpen, isMobile]);

    return (
        // Container
        <aside className={`min-h-dvh fixed left-0 top-0 ${className}`}>

            {/* Navigation */}
            <nav className={`
                min-h-dvh ${isOpen ? 'w-64 md:w-48' : 'w-12'} space-y-4
                bg-secondary border-r-divider shadow-sm
                transition-all duration-300 ease-in-out
                flex flex-col
            `}>
                {/* Header: Logo and Menu Button */}
                <div className={`${isOpen ? 'flex space-x-2' : ''} h-12 p-4 pb-2 w-full items-center cursor-pointer`}>
                    
                    {/* Logo */}
                    {isOpen && 
                        <NavLink to="/" className={`${isOpen ? 'w-7/8' : 'w-full'} flex items-center`}>
                            <ShowdownBotLogo/>
                        </NavLink>
                    }

                    {/* Open/Close Button */}
                    <button onClick={handleToggle} className="hover:text-secondary transition-colors duration-200 cursor-pointer">
                        {isOpen ? (isMobile ? <FaXmark className="h-8 w-8" /> : <FaChevronLeft />) : <FaChevronRight />}
                    </button>
                    
                </div>

                {/* Menu Items */}
                <ul className="flex-1 space-y-2 overflow-y-auto px-2">
                    {sideMenuItems.map((item) => (
                        <li key={item.path}>
                            <SideMenuItem
                                item={item}
                                isSideMenuOpen={isOpen}
                                selectedItem={selectedMenuItem} // Replace with actual selected item logic if needed
                                onClick={handleMenuItemClick}
                            />
                        </li>
                    ))}
                </ul>

                {/* Footer: Theme Toggle Button */}
                <div className="p-2 pb-10 sm:pb-auto">
                    <ThemeToggleButton />
                </div>

            </nav>

        </aside>
    );
};

export default SideMenu;