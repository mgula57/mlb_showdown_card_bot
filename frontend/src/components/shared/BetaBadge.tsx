import { Plate } from './Plate';

export function BetaBadge({ className }: { className?: string }) {
    return <Plate variant="outline" size="sm" className={`font-sans ${className}`}>Beta</Plate>;
}
