import { useEffect, useState } from "react";

/** Mirrors `prefers-reduced-motion: reduce` into JS so timed logic (e.g. the playback phase
 *  machine) can match the CSS `--motion-scale` collapse instead of drifting out of sync with it. */
export function usePrefersReducedMotion(): boolean {
    const [prefersReduced, setPrefersReduced] = useState(
        () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    );

    useEffect(() => {
        const mql = window.matchMedia("(prefers-reduced-motion: reduce)");
        const onChange = () => setPrefersReduced(mql.matches);
        mql.addEventListener("change", onChange);
        return () => mql.removeEventListener("change", onChange);
    }, []);

    return prefersReduced;
}
