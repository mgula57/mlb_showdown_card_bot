/** An account in an admin table: opens that user's detail, or reads "Anonymous" with no account. */
export function AccountLink({ userId, label, onOpen }: { userId: string | null; label: string | null; onOpen: (userId: string) => void }) {
    if (!userId) return <span className="text-(--text-tertiary)">Anonymous</span>;
    return (
        <button
            type="button"
            onClick={() => onOpen(userId)}
            className="text-(--showdown-blue) hover:underline cursor-pointer text-left break-all"
        >
            {label || userId.slice(0, 8)}
        </button>
    );
}
