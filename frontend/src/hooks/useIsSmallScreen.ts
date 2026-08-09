import { useState, useEffect } from "react";

export function useIsSmallScreen() {
    const [isSmall, setIsSmall] = useState(() => window.matchMedia("(max-width: 639px)").matches);
    useEffect(() => {
        const mq = window.matchMedia("(max-width: 639px)");
        const handler = (e: MediaQueryListEvent) => setIsSmall(e.matches);
        mq.addEventListener("change", handler);
        return () => mq.removeEventListener("change", handler);
    }, []);
    return isSmall;
}
