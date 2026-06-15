import { supabase } from './supabase';

const BUCKET = 'avatars';
const MAX_SIZE_BYTES = 2 * 1024 * 1024; // 2 MB

export function validateAvatarFile(file: File): string | null {
    if (!file.type.startsWith('image/')) return 'File must be an image';
    if (file.size > MAX_SIZE_BYTES) return 'Image must be under 2 MB';
    return null;
}

export async function uploadAvatar(file: File, userId: string): Promise<string | null> {
    const path = `${userId}/avatar`;
    const { error } = await supabase.storage
        .from(BUCKET)
        .upload(path, file, { upsert: true, contentType: file.type });
    if (error) {
        console.error('Avatar upload error:', error);
        return null;
    }
    const { data } = supabase.storage.from(BUCKET).getPublicUrl(path);
    return `${data.publicUrl}?t=${Date.now()}`;
}

export async function removeAvatar(userId: string): Promise<boolean> {
    const { error } = await supabase.storage.from(BUCKET).remove([`${userId}/avatar`]);
    return !error;
}
