import type { IconType } from "react-icons";

/**
 * Represents a menu item in the sidebar.
*/
export interface SideMenuItem {
  /** The path to navigate to (used in React Router). */
  path: string;
  /** The FA icon to display for the menu item. */
  icon: IconType;
  /** The text to display for the menu item. */
  text: string;
}