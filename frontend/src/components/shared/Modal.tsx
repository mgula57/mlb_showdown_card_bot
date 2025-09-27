import { useEffect, useRef } from 'react';
import { FaXmark } from 'react-icons/fa6';

let bodyScrollLockCount = 0;

type ModalProps = {
    children: React.ReactNode;
    onClose: () => void;
    title?: string;
    size?: 'sm' | 'md' | 'lg' | 'xl';
};

export function Modal({ children, onClose, title, size = 'lg' }: ModalProps) {
    const modalRef = useRef<HTMLDivElement>(null);
    const scrollYRef = useRef(0);

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

    // Prevent body scroll while modal is open
    useEffect(() => {
        bodyScrollLockCount += 1;
        if (bodyScrollLockCount === 1) {
            const body = document.body;
            const docEl = document.documentElement;
            const scrollbarWidth = Math.max(0, window.innerWidth - docEl.clientWidth);

            scrollYRef.current = window.scrollY;
            body.style.position = 'fixed';
            body.style.top = `-${scrollYRef.current}px`;
            body.style.width = '100%';
            if (scrollbarWidth) body.style.paddingRight = `${scrollbarWidth}px`;
        }

        return () => {
            bodyScrollLockCount -= 1;
            if (bodyScrollLockCount === 0) {
                const body = document.body;
                const top = body.style.top;
                body.style.position = '';
                body.style.top = '';
                body.style.width = '';
                body.style.paddingRight = '';
                const y = parseInt(top || '0', 10) || 0;
                window.scrollTo(0, -y);
            }
        };
    }, []);

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
            className="fixed left-0 top-0 w-screen h-lvh bg-black/50 flex items-center justify-center z-50 p-4 cursor-pointer"
            onClick={handleBackdropClick}
        >
            <div 
                ref={modalRef}
                className={`
                    bg-[var(--background-primary)] 
                    rounded-2xl
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