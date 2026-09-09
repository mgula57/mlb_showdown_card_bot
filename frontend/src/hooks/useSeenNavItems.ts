/**
 * @fileoverview Shared "NEW" nav-item tracking.
 *
 * A nav destination flagged `isNew` shows a "NEW" badge until the user visits it
 * once — from the side menu or from the Home page's nav tiles. The seen paths live
 * in a single localStorage key so both surfaces agree, and a window event keeps
 * every mounted consumer in sync the moment one of them marks a path seen (the
 * side menu doesn't remount on navigation, so a plain re-read wouldn't cut it).
 */
import { useEffect, useState } from "react";

const SEEN_NAV_ITEMS_KEY = "seenNavItems";
const SEEN_NAV_ITEMS_EVENT = "seennavitemschange";

export const getSeenNavItems = (): Set<string> => {
    try {
        const stored = localStorage.getItem(SEEN_NAV_ITEMS_KEY);
        return new Set(stored ? JSON.parse(stored) : []);
    } catch {
        return new Set();
    }
};

/** Record a nav path as visited and notify every mounted `useNavItemIsNew` consumer. */
export const markNavItemSeen = (path: string): void => {
    try {
        const seen = getSeenNavItems();
        if (seen.has(path)) return;
        seen.add(path);
        localStorage.setItem(SEEN_NAV_ITEMS_KEY, JSON.stringify([...seen]));
    } catch {
        /* localStorage unavailable — still fire the event so the current session updates */
    }
    window.dispatchEvent(new CustomEvent(SEEN_NAV_ITEMS_EVENT));
};

/**
 * Whether a nav item should currently show its "NEW" badge: flagged new *and* not
 * yet seen. Re-evaluates when any surface marks a path seen, or another tab does.
 */
export const useNavItemIsNew = (path: string, isNew: boolean | undefined): boolean => {
    const [seen, setSeen] = useState(() => getSeenNavItems().has(path));

    useEffect(() => {
        const sync = () => setSeen(getSeenNavItems().has(path));
        sync();
        window.addEventListener(SEEN_NAV_ITEMS_EVENT, sync);
        window.addEventListener("storage", sync);
        return () => {
            window.removeEventListener(SEEN_NAV_ITEMS_EVENT, sync);
            window.removeEventListener("storage", sync);
        };
    }, [path]);

    return !!isNew && !seen;
};
