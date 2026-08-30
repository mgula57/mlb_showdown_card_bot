import { useRef } from 'react';
import { FaCamera, FaSpinner, FaXmark } from 'react-icons/fa6';

import { getContrastTextColor } from '../../functions/colors';

type TeamLogoSize = 'sm' | 'md' | 'lg';

type TeamLogoProps = {
    logoUrl: string | null;
    abbreviation: string;
    primaryColor: string;
    /** Owner-only controls: click to upload, hover to reveal a remove button. */
    editable?: boolean;
    uploading?: boolean;
    onUpload?: (file: File) => void;
    onRemove?: () => void;
    size?: TeamLogoSize;
    className?: string;
};

const SIZE_CLASSES: Record<TeamLogoSize, string> = {
    sm: 'w-9 h-9 text-[11px] rounded-md',
    md: 'w-12 h-12 text-sm rounded-lg',
    lg: 'w-20 h-20 text-xl rounded-xl',
};

const BADGE_CLASSES: Record<TeamLogoSize, string> = {
    sm: 'w-4 h-4 text-[8px] -bottom-1 -right-1',
    md: 'w-5 h-5 text-[10px] -bottom-1.5 -right-1.5',
    lg: 'w-7 h-7 text-[13px] -bottom-1.5 -right-1.5',
};

/** Square team logo: shows the uploaded image, or a colored fallback with the abbreviation.
 *  When editable, a camera badge advertises that it's clickable — click opens a file picker,
 *  and a hover-revealed button clears an uploaded logo. */
export function TeamLogo({
    logoUrl, abbreviation, primaryColor, editable = false, uploading = false, onUpload, onRemove, size = 'md', className = '',
}: TeamLogoProps) {
    const inputRef = useRef<HTMLInputElement>(null);
    const textColor = getContrastTextColor(primaryColor);

    return (
        <div
            className={`relative shrink-0 group ${editable ? 'cursor-pointer' : ''} ${className}`}
            onClick={() => editable && !uploading && inputRef.current?.click()}
            role={editable ? 'button' : undefined}
            tabIndex={editable ? 0 : undefined}
            onKeyDown={e => {
                if (editable && !uploading && (e.key === 'Enter' || e.key === ' ')) {
                    e.preventDefault();
                    inputRef.current?.click();
                }
            }}
            aria-label={editable ? `Upload a logo for ${abbreviation}` : undefined}
        >
            <div
                className={`relative overflow-hidden ${SIZE_CLASSES[size]} ${
                    editable && !logoUrl ? 'ring-1 ring-inset ring-white/40' : ''
                }`}
                style={{ backgroundColor: primaryColor }}
            >
                {logoUrl ? (
                    <img src={logoUrl} alt={`${abbreviation} logo`} className="absolute inset-0 w-full h-full object-cover" />
                ) : (
                    <span className="absolute inset-0 flex items-center justify-center font-black" style={{ color: textColor }}>
                        {abbreviation}
                    </span>
                )}

                {editable && (
                    <div
                        className={`absolute inset-0 flex items-center justify-center bg-black/50 transition-opacity ${
                            uploading ? 'opacity-100' : 'opacity-0 group-hover:opacity-100 group-focus:opacity-100'
                        }`}
                    >
                        {uploading ? <FaSpinner className="animate-spin text-white text-sm" /> : <FaCamera className="text-white text-sm" />}
                    </div>
                )}
            </div>

            {editable && (
                <>
                    <input
                        ref={inputRef}
                        type="file"
                        accept="image/png,image/jpeg,image/webp,image/gif"
                        className="hidden"
                        onClick={e => e.stopPropagation()}
                        onChange={e => {
                            const file = e.target.files?.[0];
                            if (file) onUpload?.(file);
                            e.target.value = '';
                        }}
                    />

                    {/* Persistent affordance so it's clear the logo can be changed, even without hover (mobile). */}
                    {!uploading && (
                        <span
                            className={`absolute ${BADGE_CLASSES[size]} rounded-full bg-(--showdown-red) text-white border-2 border-(--background-primary) flex items-center justify-center shadow-sm`}
                        >
                            <FaCamera />
                        </span>
                    )}

                    {logoUrl && onRemove && !uploading && (
                        <button
                            type="button"
                            onClick={e => { e.stopPropagation(); onRemove(); }}
                            className="absolute -top-1.5 -left-1.5 w-4 h-4 rounded-full bg-(--background-primary) border border-(--divider) flex items-center justify-center text-(--text-tertiary) hover:text-(--text-primary) opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-opacity cursor-pointer"
                            aria-label="Remove logo"
                        >
                            <FaXmark className="text-[8px]" />
                        </button>
                    )}
                </>
            )}
        </div>
    );
}

export default TeamLogo;
