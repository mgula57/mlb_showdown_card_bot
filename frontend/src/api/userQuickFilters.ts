import { CardSource } from '../types/cardSource';

const API_BASE = import.meta.env.PROD ? '/api' : 'http://127.0.0.1:5000/api';

export interface QuickFilter {
    id: string;
    name: string;
    filters: Record<string, unknown>;
    created_at?: string;
}

export async function getUserQuickFilters(token: string, source: CardSource): Promise<QuickFilter[]> {
    try {
        const res = await fetch(`${API_BASE}/user/quick_filters?source=${source}`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return [];
        return await res.json();
    } catch {
        return [];
    }
}

export async function createUserQuickFilter(
    token: string,
    source: CardSource,
    filter: Omit<QuickFilter, 'created_at'>,
): Promise<void> {
    try {
        await fetch(`${API_BASE}/user/quick_filters`, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ...filter, source }),
        });
    } catch (err) {
        console.warn('[userQuickFilters] POST error:', err);
    }
}

export async function updateUserQuickFilter(
    token: string,
    id: string,
    patch: { name?: string; filters?: Record<string, unknown> },
): Promise<void> {
    try {
        await fetch(`${API_BASE}/user/quick_filters/${id}`, {
            method: 'PATCH',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(patch),
        });
    } catch (err) {
        console.warn('[userQuickFilters] PATCH error:', err);
    }
}

export async function deleteUserQuickFilter(token: string, id: string): Promise<void> {
    try {
        await fetch(`${API_BASE}/user/quick_filters/${id}`, {
            method: 'DELETE',
            headers: { Authorization: `Bearer ${token}` },
        });
    } catch (err) {
        console.warn('[userQuickFilters] DELETE error:', err);
    }
}
