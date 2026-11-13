

export default function LiveIcon({ size = 16, color = 'red', className = '', title = 'Live' }: { size?: number; color?: string; className?: string; title?: string }) {
    return (
        <span className="relative flex" style={{ height: size, width: size }} title={title}>
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full" style={{ backgroundColor: color, opacity: 0.75 }}></span>
            <span className={`relative inline-flex rounded-full ${className}`} style={{ height: size, width: size, backgroundColor: color, opacity: 0.9 }}></span>
        </span>
    );
}