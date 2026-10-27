/**
 * @fileoverview "Download ZIP" for an edition's rendered images. Zips in the browser from the public
 * storage URLs (no backend work): files stream through `client-zip` uncompressed (JPEGs don't shrink
 * further) and, where the browser supports a save picker, straight to disk so memory stays flat.
 */

import { useCallback, useRef, useState } from 'react';
import { makeZip } from 'client-zip';
import type { ReleaseCardImage } from '../../api/releases';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import { cardImagePublicUrl } from '../../api/supabase';

/** Rough full-size image size, for warning before an in-memory ZIP gets large. */
const ESTIMATED_BYTES_PER_IMAGE = 1.1 * 1024 * 1024;
/** Above this, browsers without a save picker are warned that the ZIP is built in memory. */
const IN_MEMORY_WARNING_BYTES = 250 * 1024 * 1024;

export type ZipEntry = {
    name: string;
    url: string;
    lastModified: Date;
};

export type ZipDownloadStatus = 'idle' | 'downloading' | 'done' | 'cancelled' | 'error';

export type ZipDownloadState = {
    status: ZipDownloadStatus;
    completed: number;
    total: number;
    /** File names that couldn't be fetched (left out of the ZIP). */
    failedNames: string[];
    error: string | null;
};

const IDLE_STATE: ZipDownloadState = { status: 'idle', completed: 0, total: 0, failedNames: [], error: null };

/** File System Access API save picker (Chromium only), not yet in TypeScript's DOM lib. */
type SaveFilePickerWindow = Window & {
    showSaveFilePicker?: (options: {
        suggestedName: string;
        types: { description: string; accept: Record<string, string[]> }[];
    }) => Promise<{ createWritable: () => Promise<WritableStream<Uint8Array>> }>;
};

/** Characters most file systems reject in names. */
const sanitizeFileName = (name: string): string => name.replace(/[\\/:*?"<>|]+/g, '-').replace(/\s+/g, ' ').trim();

/** One entry per current (rendered) image, named "{set number} {player}.jpg" so the ZIP sorts in
 * set order. Out-of-date, failed, and missing images are left out. */
export function buildZipEntries(images: ReleaseCardImage[], snapshotsById: Map<string | null, CardDatabaseRecord>): ZipEntry[] {
    const usedNames = new Set<string>();
    return images
        .filter((image): image is ReleaseCardImage & { storage_path: string } => image.status === 'rendered' && !!image.storage_path)
        .map(image => {
            const extension = image.storage_path.split('.').pop() ?? 'jpg';
            const playerName = snapshotsById.get(image.source_card_id)?.name ?? image.source_card_id;
            const base = sanitizeFileName([image.set_number, playerName].filter(Boolean).join(' '));
            let name = `${base}.${extension}`;
            for (let copy = 2; usedNames.has(name.toLowerCase()); copy++) name = `${base} (${copy}).${extension}`;
            usedNames.add(name.toLowerCase());
            return {
                name,
                url: cardImagePublicUrl(image.storage_path),
                lastModified: image.rendered_at ? new Date(image.rendered_at) : new Date(),
            };
        });
}

export const editionZipFileName = (releaseName: string, editionName: string, suffix?: string): string =>
    `${sanitizeFileName([`${releaseName} - ${editionName}`, suffix].filter(Boolean).join(' '))}.zip`;

// Newest image time in the last complete ZIP of each edition, so the next download can be just the
// re-rendered images. Server render times (not the local clock) keep the comparison exact.
const lastZipStorageKey = (editionId: string) => `releaseEditionLastZip:${editionId}`;

export function loadLastZipRenderedAt(editionId: string): Date | null {
    try {
        const saved = localStorage.getItem(lastZipStorageKey(editionId));
        const time = saved ? Date.parse(saved) : NaN;
        return Number.isFinite(time) ? new Date(time) : null;
    } catch {
        return null;
    }
}

/** Records a ZIP that saved with every image, returning the stored time. */
export function saveLastZipRenderedAt(editionId: string, entries: ZipEntry[]): Date | null {
    if (entries.length === 0) return null;
    const newest = new Date(Math.max(...entries.map(entry => entry.lastModified.getTime())));
    try { localStorage.setItem(lastZipStorageKey(editionId), newest.toISOString()); } catch { /* storage unavailable */ }
    return newest;
}

export const entriesRenderedAfter = (entries: ZipEntry[], since: Date): ZipEntry[] =>
    entries.filter(entry => entry.lastModified.getTime() > since.getTime());

function saveBlob(blob: Blob, fileName: string) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    // Give the browser a moment to start the download before freeing the blob
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

const isAbortError = (err: unknown) => err instanceof DOMException && err.name === 'AbortError';

export function useEditionZipDownload() {
    const [state, setState] = useState<ZipDownloadState>(IDLE_STATE);
    const abortRef = useRef<AbortController | null>(null);

    /** Must be called straight from a click: the save picker needs the user gesture. Resolves true
     * when the ZIP saved with every image. */
    const start = useCallback(async (entries: ZipEntry[], zipFileName: string): Promise<boolean> => {
        if (entries.length === 0 || abortRef.current) return false;

        const savePicker = (window as SaveFilePickerWindow).showSaveFilePicker;
        if (!savePicker) {
            const estimatedBytes = entries.length * ESTIMATED_BYTES_PER_IMAGE;
            if (estimatedBytes > IN_MEMORY_WARNING_BYTES) {
                const sizeMb = Math.round(estimatedBytes / (1024 * 1024) / 10) * 10;
                const proceed = window.confirm(
                    `This is a big download (about ${sizeMb} MB) and may take a while.\n\n` +
                    "On a phone or tablet it might not finish. For large sets, Chrome or Edge on a computer works best.\n\nDownload anyway?"
                );
                if (!proceed) return false;
            }
        }

        let writable: WritableStream<Uint8Array> | null = null;
        if (savePicker) {
            try {
                const handle = await savePicker({
                    suggestedName: zipFileName,
                    types: [{ description: 'ZIP archive', accept: { 'application/zip': ['.zip'] } }],
                });
                writable = await handle.createWritable();
            } catch (err) {
                if (isAbortError(err)) return false; // User closed the picker
                writable = null; // Picker unavailable (e.g. in an iframe): fall back to an in-memory download
            }
        }

        const controller = new AbortController();
        abortRef.current = controller;
        const failedNames: string[] = [];
        setState({ status: 'downloading', completed: 0, total: entries.length, failedNames: [], error: null });

        // client-zip pulls the next file only after it has fully read the previous one, so each
        // resume of this generator means one more file is done.
        async function* files() {
            for (const entry of entries) {
                if (controller.signal.aborted) return;
                try {
                    const response = await fetch(entry.url, { signal: controller.signal });
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    yield { input: response, name: entry.name, lastModified: entry.lastModified };
                } catch (err) {
                    if (controller.signal.aborted) return;
                    console.error(`ZIP: failed to fetch ${entry.name}`, err);
                    failedNames.push(entry.name);
                }
                setState(prev => ({ ...prev, completed: prev.completed + 1, failedNames: [...failedNames] }));
            }
        }

        try {
            const zipStream = makeZip(files());
            if (writable) {
                // Aborting cancels the write, which discards the partial file
                await zipStream.pipeTo(writable, { signal: controller.signal });
            } else {
                const blob = await new Response(zipStream).blob();
                if (controller.signal.aborted) throw new DOMException('Cancelled', 'AbortError');
                saveBlob(blob, zipFileName);
            }
            setState(prev => ({ ...prev, status: 'done', failedNames: [...failedNames] }));
            return failedNames.length === 0;
        } catch (err) {
            if (controller.signal.aborted || isAbortError(err)) {
                setState(prev => ({ ...prev, status: 'cancelled' }));
            } else {
                console.error('ZIP download failed', err);
                setState(prev => ({ ...prev, status: 'error', error: err instanceof Error ? err.message : 'ZIP download failed.' }));
            }
            return false;
        } finally {
            abortRef.current = null;
        }
    }, []);

    const cancel = useCallback(() => abortRef.current?.abort(), []);
    const reset = useCallback(() => setState(IDLE_STATE), []);

    return { state, start, cancel, reset };
}
