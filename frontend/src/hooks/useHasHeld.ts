import { useEffect, useState } from "react";

/** Whether `key` has been current for `delayMs`. One already current on mount has. Null never has. */
export function useHasHeld(key: string | null, delayMs: number): boolean {
    const [heldKey, setHeldKey] = useState(key);
    useEffect(() => {
        if (key == null || key === heldKey) return;
        const timer = window.setTimeout(() => setHeldKey(key), delayMs);
        return () => window.clearTimeout(timer);
    }, [key, heldKey, delayMs]);
    return key != null && key === heldKey;
}
