import { useEffect, useRef } from 'react';

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

    return (
        <div 
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={handleBackdropClick}
        >
            <div 
                ref={modalRef}
                className={`
                    bg-[var(--background-primary)] 
                    rounded-lg 
                    shadow-xl 
                    w-full 
                    ${sizeClasses[size]}
                    max-h-[90vh] 
                    overflow-y-auto
                    border 
                    border-[var(--border-primary)]
                `}
            >
                {/* Header */}
                {title && (
                    <div className="flex items-center justify-between p-6 border-b border-[var(--border-secondary)]">
                        <h2 className="text-xl font-semibold text-[var(--text-primary)]">
                            {title}
                        </h2>
                        <button
                            onClick={onClose}
                            className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-2xl"
                        >
                            ×
                        </button>
                    </div>
                )}

                {/* Content */}
                <div className="p-6">
                    {children}
                </div>
            </div>
        </div>
    );
}