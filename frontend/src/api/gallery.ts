const API_BASE = import.meta.env.PROD ? '/api' : 'http://127.0.0.1:5000/api';

export interface GalleryImageRecord {
    id: number;
    player_name: string | null;
    year: string | null;
    set_name: string | null;
    public_url: string | null;
    thumbnail_public_url: string | null;
    storage_path: string | null;
    thumbnail_storage_path: string | null;
    created_at: string;
    user_inputs: Record<string, unknown> | null;
}

export interface GalleryResponse {
    gallery: GalleryImageRecord[];
    has_more: boolean;
}

export interface GalleryFilters {
    set_name?: string;
    player_name?: string;
    year?: string;
    player_type?: string;
}

export async function fetchUserGallery(
    token: string,
    limit = 50,
    offset = 0,
    filters: GalleryFilters = {},
): Promise<GalleryResponse> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (filters.set_name) params.set('set_name', filters.set_name);
    if (filters.player_name) params.set('player_name', filters.player_name);
    if (filters.year) params.set('year', filters.year);
    if (filters.player_type) params.set('player_type', filters.player_type);
    const res = await fetch(`${API_BASE}/user/gallery?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Gallery fetch failed: ${res.status}`);
    return res.json();
}

export async function deleteGalleryCard(
    token: string,
    galleryId: number,
): Promise<void> {
    const res = await fetch(`${API_BASE}/user/gallery/${galleryId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Gallery delete failed: ${res.status}`);
}
