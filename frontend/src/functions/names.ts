
export const getFirstName = (name?: string): string => {
    if (!name) return 'Unknown';
    const trimmed = name.trim();
    if (!trimmed) return 'Unknown';
    const parts = trimmed.split(/\s+/);
    if (parts.length === 0) return 'Unknown';
    return parts[0];
};

export const getLastName = (name?: string): string => {
    if (!name) return 'Unknown';
    const trimmed = name.trim();
    if (!trimmed) return 'Unknown';
    const parts = trimmed.split(/\s+/);
    if (parts.length === 1) return parts[0];
    const last = parts[parts.length - 1].replace('.', '').toUpperCase();
    if (['JR', 'SR', 'II', 'III', 'IV', 'V'].includes(last) && parts.length > 1) {
        return `${parts[parts.length - 2]} ${parts[parts.length - 1]}`;
    }
    return parts[parts.length - 1];
};

export const getFirstInitial = (name?: string): string => {
    // Returns the first initial of the player's first name
    if (!name) return '';
    const trimmed = name.trim();
    if (!trimmed) return '';
    return trimmed.split(/\s+/)[0][0].toUpperCase();
};