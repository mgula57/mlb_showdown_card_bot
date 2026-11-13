import { useEffect, useRef, useState } from 'react';
import { FaSpinner } from 'react-icons/fa6';
import { COMMENT_MAX_LENGTH } from '../../../api/comments';
import { buttonClass } from '../buttonStyles';
import { fieldClass } from '../fieldStyles';
import { InlineError } from '../InlineError';

type CommentComposerProps = {
    /** Throws to keep the text and show why it failed. */
    onSubmit: (body: string) => Promise<void>;
    placeholder?: string;
    submitLabel?: string;
    /** Shown above the field, e.g. "Replying to @name". */
    context?: string;
    /** A reply's composer can be dismissed; the top-level one can't. */
    onCancel?: () => void;
    autoFocus?: boolean;
};

/** The field for a new comment or reply. ⌘/Ctrl+Enter posts. */
export function CommentComposer({ onSubmit, placeholder = 'Add a comment…', submitLabel = 'Post', context, onCancel, autoFocus = false }: CommentComposerProps) {
    const [body, setBody] = useState('');
    const [posting, setPosting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);
    const trimmed = body.trim();
    const remaining = COMMENT_MAX_LENGTH - trimmed.length;
    const canPost = !!trimmed && remaining >= 0 && !posting;

    useEffect(() => { if (autoFocus) inputRef.current?.focus(); }, [autoFocus]);

    async function submit() {
        if (!canPost) return;
        setPosting(true);
        setError(null);
        try {
            await onSubmit(trimmed);
            setBody('');
            onCancel?.();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Couldn't post your comment. Try again.");
        } finally {
            setPosting(false);
        }
    }

    return (
        <form
            className="flex flex-col gap-1.5"
            onSubmit={e => { e.preventDefault(); submit(); }}
        >
            {context && <span className="text-[12px] text-(--text-tertiary)">{context}</span>}
            <textarea
                ref={inputRef}
                value={body}
                onChange={e => setBody(e.target.value)}
                onKeyDown={e => {
                    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); submit(); }
                    if (e.key === 'Escape' && onCancel) { e.stopPropagation(); onCancel(); }
                }}
                rows={onCancel ? 2 : 3}
                maxLength={COMMENT_MAX_LENGTH + 200}
                placeholder={placeholder}
                aria-label={placeholder}
                className={fieldClass('md', 'h-auto py-2 resize-y w-full')}
            />
            {error && <InlineError size="sm">{error}</InlineError>}
            <div className="flex items-center justify-end gap-2">
                {/* Only once it's getting close, so it isn't noise on every comment */}
                {remaining < 100 && (
                    <span className={`mr-auto text-[11px] tabular-nums ${remaining < 0 ? 'text-(--showdown-red)' : 'text-(--text-tertiary)'}`}>
                        {remaining}
                    </span>
                )}
                {onCancel && (
                    <button type="button" onClick={onCancel} className={buttonClass('ghost', 'sm')}>Cancel</button>
                )}
                <button type="submit" disabled={!canPost} className={buttonClass('primary', 'sm', 'disabled:opacity-50 disabled:cursor-not-allowed')}>
                    {posting && <FaSpinner className="animate-spin text-[11px]" />}
                    {posting ? 'Posting…' : submitLabel}
                </button>
            </div>
        </form>
    );
}
