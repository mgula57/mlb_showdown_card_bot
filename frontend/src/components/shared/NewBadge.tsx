import { Plate } from './Plate';

export function NewBadge({ className }: { className?: string }) {
    return <Plate variant="red" size="sm" className={`font-sans ${className}`}>New</Plate>;
}
