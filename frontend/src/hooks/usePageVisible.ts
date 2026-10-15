import { useSyncExternalStore } from 'react';

function subscribe(onChange: () => void): () => void {
    document.addEventListener('visibilitychange', onChange);
    return () => document.removeEventListener('visibilitychange', onChange);
}

const isVisible = () => document.visibilityState === 'visible';

/** Whether this tab is in view - false while it's in the background or the window is minimized. */
export function usePageVisible(): boolean {
    return useSyncExternalStore(subscribe, isVisible, () => true);
}
