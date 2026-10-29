import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

/** The first-build tour, in the order tips get their turn. `welcome` is the opening modal. */
export const RELEASE_TIP_ORDER = ['welcome', 'buildMethod', 'savePreview', 'cardStyle', 'imagesStep', 'imageLibraries', 'render', 'publish'] as const;
export type ReleaseTipId = typeof RELEASE_TIP_ORDER[number];

export const RELEASE_TIP_COPY: Record<Exclude<ReleaseTipId, 'welcome'>, { title: string; body: string }> = {
    buildMethod: {
        title: 'Start with the player pool',
        body: 'Pick how to fill this edition. Algorithm builds a balanced set from points and position targets, Manual searches for players one at a time, and Customs adds cards you made in the Card Builder.',
    },
    savePreview: {
        title: "Nothing's saved yet",
        body: "This is a preview of the algorithm's picks. Check it with the Summary and Cutoff tabs, then save it as your pool. You can rerun it as often as you like.",
    },
    cardStyle: {
        title: 'Pick a card style',
        body: 'Set the default look for every card in this edition. You can still restyle single cards from their detail view.',
    },
    imagesStep: {
        title: 'Next: card images',
        body: 'When the pool looks right, render an image for every card in step 2.',
    },
    imageLibraries: {
        title: 'Bring your own player images',
        body: "Connect a Google Drive folder of player images and your cards use them automatically. Without one, only players with an official Showdown Bot image get a photo. Connect it before rendering so you don't have to render twice.",
    },
    render: {
        title: 'Render your cards',
        body: 'Rendering runs in the background, so you can keep working while images come in. Changing cards or the style later marks the affected images out of date.',
    },
    publish: {
        title: 'Ready to go public?',
        body: 'Publish opens the Review step, which checks the release for problems before anything goes live. Until you publish, only you can see it.',
    },
};

/** Per-viewer, so the tour runs once per browser. */
const ONBOARDING_STORAGE_KEY = 'releaseBuilder.onboarding';

type StoredOnboarding = { seen: ReleaseTipId[]; done: boolean };

function isTipId(value: unknown): value is ReleaseTipId {
    return RELEASE_TIP_ORDER.includes(value as ReleaseTipId);
}

function loadOnboarding(): StoredOnboarding {
    try {
        const parsed = JSON.parse(localStorage.getItem(ONBOARDING_STORAGE_KEY) ?? 'null');
        if (parsed && typeof parsed === 'object') {
            return { seen: Array.isArray(parsed.seen) ? parsed.seen.filter(isTipId) : [], done: parsed.done === true };
        }
    } catch { /* storage unavailable or malformed */ }
    return { seen: [], done: false };
}

function saveOnboarding(state: StoredOnboarding) {
    try { localStorage.setItem(ONBOARDING_STORAGE_KEY, JSON.stringify(state)); } catch { /* storage unavailable */ }
}

export type ReleaseOnboarding = {
    /** False while browsing, reviewing, after the tour, or in an edition tab that isn't on screen. */
    enabled: boolean;
    /** The one tip showing right now: the first unseen tip in order whose moment has come. */
    current: ReleaseTipId | null;
    hasSeen: (id: ReleaseTipId) => boolean;
    /** Marks a tip's moment as come (while its condition holds). Returns the cleanup. */
    register: (id: ReleaseTipId) => () => void;
    markSeen: (id: ReleaseTipId) => void;
    /** Ends the tour for good: "Skip tips", or the first publish. */
    finish: () => void;
};

export const ReleaseOnboardingContext = createContext<ReleaseOnboarding | null>(null);

/** The tour's state, for the provider in ReleaseDetail. */
export function useReleaseOnboardingState(enabled: boolean): ReleaseOnboarding {
    const [stored, setStored] = useState(loadOnboarding);
    const [eligibleCounts, setEligibleCounts] = useState<Partial<Record<ReleaseTipId, number>>>({});

    const update = useCallback((change: (prev: StoredOnboarding) => StoredOnboarding) => {
        setStored(prev => {
            const next = change(prev);
            saveOnboarding(next);
            return next;
        });
    }, []);
    const markSeen = useCallback((id: ReleaseTipId) => {
        update(prev => prev.seen.includes(id) ? prev : { ...prev, seen: [...prev.seen, id] });
    }, [update]);
    const finish = useCallback(() => update(prev => ({ ...prev, done: true })), [update]);
    const register = useCallback((id: ReleaseTipId) => {
        setEligibleCounts(prev => ({ ...prev, [id]: (prev[id] ?? 0) + 1 }));
        return () => setEligibleCounts(prev => ({ ...prev, [id]: (prev[id] ?? 1) - 1 }));
    }, []);

    const isOn = enabled && !stored.done;
    const current = isOn ? RELEASE_TIP_ORDER.find(id => !stored.seen.includes(id) && (eligibleCounts[id] ?? 0) > 0) ?? null : null;
    const hasSeen = useCallback((id: ReleaseTipId) => stored.seen.includes(id), [stored.seen]);

    return useMemo(
        () => ({ enabled: isOn, current, hasSeen, register, markSeen, finish }),
        [isOn, current, hasSeen, register, markSeen, finish]
    );
}

/**
 * One tip's place in the tour. `show` is the tip's moment (e.g. "a preview is on screen"). A tip
 * counts as seen once the user clicks Got it, or once it has shown and its moment passes because
 * they did the thing it pointed at.
 */
export function useReleaseTip(id: ReleaseTipId, show: boolean) {
    const onboarding = useContext(ReleaseOnboardingContext);
    const enabled = !!onboarding?.enabled;
    const register = onboarding?.register;
    const markSeen = onboarding?.markSeen;

    useEffect(() => {
        if (!enabled || !show || !register) return;
        return register(id);
    }, [enabled, show, register, id]);

    const isOpen = enabled && show && onboarding?.current === id;
    const hasOpened = useRef(false);
    useEffect(() => {
        if (isOpen) hasOpened.current = true;
        else if (hasOpened.current && enabled && !show) {
            hasOpened.current = false;
            markSeen?.(id);
        }
    }, [isOpen, enabled, show, markSeen, id]);

    const tipNumber = RELEASE_TIP_ORDER.indexOf(id);
    return {
        isOpen,
        progress: `Tip ${tipNumber} of ${RELEASE_TIP_ORDER.length - 1}`,
        dismiss: () => markSeen?.(id),
        skipAll: () => onboarding?.finish(),
    };
}
