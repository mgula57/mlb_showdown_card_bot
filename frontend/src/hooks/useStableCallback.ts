import { useCallback, useLayoutEffect, useRef } from 'react';

/**
 * A callback whose identity never changes but always calls the latest `fn`, so memoized children
 * (e.g. long list rows) skip re-rendering when only the parent's closures changed.
 * Only call it from event handlers, not during render.
 */
export function useStableCallback<Args extends unknown[], Result>(fn: (...args: Args) => Result): (...args: Args) => Result {
    const fnRef = useRef(fn);
    useLayoutEffect(() => { fnRef.current = fn; });
    return useCallback((...args: Args) => fnRef.current(...args), []);
}
