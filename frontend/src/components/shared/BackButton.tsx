import { FaChevronLeft } from "react-icons/fa6";

type BackButtonProps = {
    onBack: () => void;
    label?: string;
    className?: string;
};

export default function BackButton({ onBack, label = "Back to Games", className = "" }: BackButtonProps) {
    return (
        <button
            type="button"
            onClick={onBack}
            className={`flex items-center gap-1.5 text-sm font-semibold text-(--secondary) hover:text-(--primary) bg-(--background-secondary) p-2 rounded-lg cursor-pointer transition-colors ${className}`}
        >
            <FaChevronLeft className="h-3 w-3" />
            {label}
        </button>
    );
}
