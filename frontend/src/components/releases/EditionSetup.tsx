import { FaArrowRight } from 'react-icons/fa6';
import { Heading } from '../shared/Heading';
import { buttonClass } from '../shared/buttonStyles';
import { ScopePanel } from './ScopePanel';
import type { EditionScope, OutsideScopeCounts } from './editionScope';

type EditionSetupProps = {
    scope: EditionScope;
    onChange: (patch: Partial<EditionScope>) => void;
    outside: OutsideScopeCounts;
    onContinue: () => void;
};

/** Step 1 of the Edition Builder: the seasons, sets and size this edition draws from. Most people
 * know these up front, so it's one screen to fill in and leave; it stays open to come back to. */
export function EditionSetup({ scope, onChange, outside, onContinue }: EditionSetupProps) {
    return (
        <div className="flex-1 min-h-0 overflow-y-auto">
            <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:py-8 flex flex-col gap-6">
                <div className="flex flex-col gap-1.5">
                    <Heading level="section">Edition Setup</Heading>
                    <p className="text-[13px] text-(--text-secondary)">
                        What this edition draws from. Define the high level details here. Changes save as you make them, and you can come back to this step any time from the bar above.
                    </p>
                </div>
                <ScopePanel scope={scope} onChange={onChange} outside={outside} />
                <div className="flex justify-end border-t border-(--divider) pt-4">
                    <button type="button" onClick={onContinue} className={buttonClass('primary', 'md')}>
                        Continue to Player Pool <FaArrowRight className="text-[11px]" />
                    </button>
                </div>
            </div>
        </div>
    );
}
