/**
 * @fileoverview Image Libraries API
 *
 * Google Drive folders a user shares (Viewer) with the Showdown Bot service account. With "Auto"
 * player images, libraries are searched in the user's saved order and the first match is used.
 */

const API_BASE = import.meta.env.PROD ? '/api' : 'http://127.0.0.1:5000/api';

/** Built-in library id, always present in the search order. */
export const SHOWDOWN_BOT_LIBRARY_ID = 'SHOWDOWN_BOT';

export type ImageLibrary = {
    id: string;
    folder_id: string;
    name: string;
    image_count: number;
    recognized_image_count: number;
    verified_at: string | null;
    created_at: string | null;
};

export type ImageLibrariesOverview = {
    /** Email users share their folder with. Null when Drive libraries are unavailable server-side. */
    service_account_email: string | null;
    libraries: ImageLibrary[];
    /** Library ids in search order, including SHOWDOWN_BOT_LIBRARY_ID. */
    order: string[];
};

export type ImageLibraryTestResult = {
    folder_id: string;
    name: string;
    image_count: number;
    recognized_image_count: number;
    /** A few image names that don't follow the naming convention. */
    unrecognized_examples: string[];
    other_file_count: number;
};

/** Error thrown with the server's user-facing message. */
export class ImageLibraryError extends Error {}

async function request<T>(token: string, path: string, init: RequestInit = {}): Promise<T> {
    let res: Response;
    try {
        res = await fetch(`${API_BASE}/user/image_libraries${path}`, {
            ...init,
            headers: {
                Authorization: `Bearer ${token}`,
                ...(init.body ? { 'Content-Type': 'application/json' } : {}),
            },
        });
    } catch {
        throw new ImageLibraryError('Could not reach Showdown Bot. Check your connection and try again.');
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        throw new ImageLibraryError(data?.error || `Request failed (${res.status})`);
    }
    return data as T;
}

export function getImageLibraries(token: string): Promise<ImageLibrariesOverview> {
    return request(token, '');
}

/** Check the bot can read a folder (link or id) without saving it. */
export function testImageLibrary(token: string, folder: string): Promise<ImageLibraryTestResult> {
    return request(token, '/test', { method: 'POST', body: JSON.stringify({ folder }) });
}

/** Verify and save a folder. Re-saving a connected folder refreshes its name and image counts. */
export function saveImageLibrary(token: string, folder: string): Promise<ImageLibrariesOverview & { test: ImageLibraryTestResult }> {
    return request(token, '', { method: 'POST', body: JSON.stringify({ folder }) });
}

export function deleteImageLibrary(token: string, libraryId: string): Promise<ImageLibrariesOverview> {
    return request(token, `/${encodeURIComponent(libraryId)}`, { method: 'DELETE' });
}

export function updateImageLibraryOrder(token: string, order: string[]): Promise<ImageLibrariesOverview> {
    return request(token, '/order', { method: 'PUT', body: JSON.stringify({ order }) });
}
