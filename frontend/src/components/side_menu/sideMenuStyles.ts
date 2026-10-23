/**
 * @fileoverview Shared class strings for side menu rows (nav links and the theme toggle).
 * Kept in a .ts file so component files only export components (fast refresh).
 */

/** Shared easing with the nav width / content padding so everything moves as one. */
export const SIDE_MENU_MOTION = 'duration-300 ease-(--side-menu-ease) motion-reduce:transition-none';

/**
 * Outer row classes. The selected background is the sliding indicator rendered by SideMenu,
 * so a row only paints a (lighter) hover state when it isn't the active tab.
 */
export const sideMenuRowClassName = (isSelected: boolean) => `
    group relative z-10 flex items-center h-12 w-full rounded-md cursor-pointer
    transition-colors duration-150
    ${isSelected ? 'text-primary' : 'text-(--quaternary) hover:text-(--primary) hover:bg-(--background-primary)'}
`;
