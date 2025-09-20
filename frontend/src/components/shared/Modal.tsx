import { useEffect, useRef } from 'react';
import { FaXmark } from 'react-icons/fa6';

type ModalProps = {
    children: React.ReactNode;
    onClose: () => void;
    title?: string;
    size?: 'sm' | 'md' | 'lg' | 'xl';
};

export function Modal({ children, onClose, title, size = 'lg' }: ModalProps) {
    const modalRef = useRef<HTMLDivElement>(null);

    // Close on escape key
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                onClose();
            }
        };

        document.addEventListener('keydown', handleEscape);
        return () => document.removeEventListener('keydown', handleEscape);
    }, [onClose]);

    // Close when clicking outside
    const handleBackdropClick = (e: React.MouseEvent) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    };

    const sizeClasses = {
        sm: 'max-w-md',
        md: 'max-w-2xl',
        lg: 'max-w-4xl',
        xl: 'max-w-6xl'
    };

    const closeButton = () => (
        <button
            onClick={onClose}
            className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-2xl cursor-pointer"
        >
            <FaXmark />
        </button>
    );

    return (
        <div 
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 cursor-pointer"
            onClick={handleBackdropClick}
        >
            <div 
                ref={modalRef}
                className={`
                    bg-[var(--background-primary)] 
                    rounded-lg 
                    shadow-2xl 
                    w-full 
                    ${sizeClasses[size]}
                    max-h-[85vh] 
                    overflow-y-auto
                    cursor-default
                    relative
                `}
            >
                {/* Header */}
                {title ? (
                    <div className="flex items-center justify-between p-3 border-b border-[var(--border-secondary)]">
                        <h2 className="text-xl font-semibold text-[var(--text-primary)]">
                            {title}
                        </h2>
                        {closeButton()}
                    </div>
                ) : (
                    <div className="absolute right-3 top-3">
                        {closeButton()}
                    </div>
                )}

                {/* Content */}
                <div className="p-0">
                    {children}
                </div>

            </div>
        </div>
    );
}