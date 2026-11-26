import { useEffect, useRef, useState } from 'react';
import { FaCheck, FaCopy, FaXmark } from 'react-icons/fa6';
import { buttonClass } from '../../shared/buttonStyles';
import { CAPS_LABEL_CLASS } from '../../shared/fieldStyles';

type CopyCardInfoMenuProps = {
    name?: string | null;
    brefId?: string | null;
    mlbId?: number | string | null;
    /** URL of the card's rendered image; adds an Image row that copies it as a PNG */
    imageUrl?: string | null;
};

type CopyRow = { key: string; label: string; value: string; copy: () => Promise<void> };

/** The image at `url` as a PNG blob — the one image type every browser's clipboard accepts */
async function fetchImageAsPng(url: string): Promise<Blob> {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Image request failed (${response.status})`);
    const blob = await response.blob();
    if (blob.type === 'image/png') return blob;
    const bitmap = await createImageBitmap(blob);
    const canvas = document.createElement('canvas');
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    canvas.getContext('2d')?.drawImage(bitmap, 0, 0);
    return new Promise((resolve, reject) => canvas.toBlob(png => (png ? resolve(png) : reject(new Error('PNG conversion failed'))), 'image/png'));
}

/** A copy button beside a card's player name: opens a menu of the player's name, Baseball
 * Reference id, MLB id and the card image, and clicking a row copies it. */
export function CopyCardInfoMenu({ name, brefId, mlbId, imageUrl }: CopyCardInfoMenuProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [status, setStatus] = useState<{ key: string; ok: boolean } | null>(null);
    const rootRef = useRef<HTMLDivElement>(null);

    const copyText = (value: string) => navigator.clipboard.writeText(value);
    const rows: CopyRow[] = [
        ...[
            { key: 'name', label: 'Name', value: name },
            { key: 'bref', label: 'BREF ID', value: brefId },
            { key: 'mlb', label: 'MLB ID', value: mlbId },
        ]
            .filter(row => row.value != null && row.value !== '')
            .map(row => ({ key: row.key, label: row.label, value: String(row.value), copy: () => copyText(String(row.value)) })),
        ...(imageUrl && typeof ClipboardItem !== 'undefined' ? [{
            key: 'image',
            label: 'Image',
            value: 'Card image',
            // The ClipboardItem gets the blob as a promise so the write starts inside the click (Safari requires it)
            copy: () => navigator.clipboard.write([new ClipboardItem({ 'image/png': fetchImageAsPng(imageUrl) })]),
        }] : []),
    ];

    useEffect(() => {
        if (!isOpen) return;
        const handleMouseDown = (event: MouseEvent) => {
            if (!rootRef.current?.contains(event.target as Node)) setIsOpen(false);
        };
        document.addEventListener('mousedown', handleMouseDown);
        return () => document.removeEventListener('mousedown', handleMouseDown);
    }, [isOpen]);

    if (rows.length === 0) return null;

    const handleCopy = (row: CopyRow) => {
        row.copy()
            .then(() => setStatus({ key: row.key, ok: true }))
            .catch((error) => {
                console.error(`Couldn't copy ${row.label}:`, error);
                setStatus({ key: row.key, ok: false });
            })
            .finally(() => {
                setTimeout(() => setStatus(current => (current?.key === row.key ? null : current)), 1500);
            });
    };

    return (
        <div
            ref={rootRef}
            className="relative"
            onKeyDown={(event) => {
                // Closes just the menu, not an enclosing modal
                if (event.key === 'Escape' && isOpen) {
                    event.stopPropagation();
                    setIsOpen(false);
                }
            }}
        >
            <button
                type="button"
                onClick={() => setIsOpen(open => !open)}
                aria-label="Copy player name, ids or card image"
                aria-expanded={isOpen}
                title="Copy name, BREF ID, MLB ID or card image"
                className={buttonClass('ghost', 'sm', 'px-2 text-(--text-tertiary)')}
            >
                <FaCopy className="w-3.5 h-3.5" />
            </button>

            {isOpen && (
                <div
                    role="menu"
                    className="absolute left-0 top-full mt-1 z-30 min-w-56 bg-(--background-secondary) rounded-card shadow-overlay border border-(--rule-strong) py-1"
                >
                    {rows.map(row => {
                        const rowStatus = status?.key === row.key ? status : null;
                        return (
                            <button
                                key={row.key}
                                type="button"
                                role="menuitem"
                                onClick={() => handleCopy(row)}
                                className="w-full flex items-center gap-3 px-3 py-2 text-left text-sm cursor-pointer hover:bg-(--background-tertiary)"
                            >
                                <span className={`${CAPS_LABEL_CLASS} text-(--text-tertiary) w-16 shrink-0`}>{row.label}</span>
                                <span className={`flex-1 min-w-0 truncate tabular-nums ${rowStatus && !rowStatus.ok ? 'text-(--red)' : ''}`}>
                                    {rowStatus && !rowStatus.ok ? "Couldn't copy" : row.value}
                                </span>
                                {rowStatus
                                    ? (rowStatus.ok
                                        ? <FaCheck className="shrink-0 text-(--green) text-[11px]" aria-label="Copied" />
                                        : <FaXmark className="shrink-0 text-(--red) text-[11px]" aria-label="Copy failed" />)
                                    : <FaCopy className="shrink-0 text-(--text-tertiary) text-[11px]" />}
                            </button>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

export default CopyCardInfoMenu;
