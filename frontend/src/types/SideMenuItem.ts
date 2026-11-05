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
  /** If true, shows a NEW badge on the item. */
  isNew?: boolean;
}
/**
 * A group of menu items in the sidebar. Untitled sections render without a header.
 */
export interface SideMenuSection {
  /** Header shown above the group when the menu is expanded (a divider when collapsed). */
  title?: string;
  /** Items in the group, rendered in order. */
  items: SideMenuItem[];
}
