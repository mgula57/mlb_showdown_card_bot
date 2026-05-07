const API_BASE = import.meta.env.PROD ? '/api' : 'http://127.0.0.1:5000/api';

export interface GalleryImageRecord {
    id: number;
    storage_path: string;
    public_url: string | null;
    player_name: string | null;
    year: string | null;
    set_name: string | null;
    card_metadata: Record<string, unknown> | null;
    created_at: string;
}

export interface GalleryResponse {
    gallery: GalleryImageRecord[];
    has_more: boolean;
}

export async function fetchUserGallery(
    token: string,
    limit = 50,
    offset = 0,
): Promise<GalleryResponse> {
    const res = await fetch(
        `${API_BASE}/user/gallery?limit=${limit}&offset=${offset}`,
        { headers: { Authorization: `Bearer ${token}` } },
    );
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
