const API_BASE = import.meta.env.PROD ? '/api' : 'http://127.0.0.1:5000/api';

export interface UserSettingsDB {
    theme?: 'light' | 'dark' | 'system';
    showdown_set?: string;
    custom_card_form_settings?: Record<string, unknown>;
    starred_teams?: { mlb?: string[]; wbc?: string[] };
    avatar_url?: string;
}

export async function getUserSettings(token: string): Promise<UserSettingsDB | null> {
    try {
        const res = await fetch(`${API_BASE}/user/settings`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return null;
        const data = await res.json();
        return Object.keys(data).length > 0 ? (data as UserSettingsDB) : null;
    } catch {
        return null;
    }
}

export async function updateUserSettings(
    token: string,
    settings: Partial<UserSettingsDB>,
): Promise<void> {
    try {
        await fetch(`${API_BASE}/user/settings`, {
            method: 'PUT',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings),
        });
    } catch (err) {
        console.warn('[userSettings] PUT error:', err);
    }
}
