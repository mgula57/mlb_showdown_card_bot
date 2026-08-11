import { FaChevronLeft } from "react-icons/fa6";

export default function BackButton({ onBack }: { onBack: () => void }) {
    return (
        <button
            type="button"
            onClick={onBack}
            className="flex items-center gap-1.5 text-sm font-semibold text-(--secondary) hover:text-(--primary) bg-(--background-secondary) p-2 rounded-lg cursor-pointer transition-colors"
        >
            <FaChevronLeft className="h-3 w-3" />
            Back to Games
        </button>
    );
}
