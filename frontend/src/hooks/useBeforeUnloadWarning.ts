import { useEffect } from 'react';

/** While `active`, the browser asks for confirmation before a reload, tab close, or navigation away
 *  from the app, so unsaved work isn't lost silently. In-app route changes aren't affected. */
export function useBeforeUnloadWarning(active: boolean) {
    useEffect(() => {
        if (!active) return;
        const handleBeforeUnload = (event: BeforeUnloadEvent) => {
            event.preventDefault();
            // Older browsers only show the prompt when returnValue is set
            event.returnValue = '';
        };
        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [active]);
}
