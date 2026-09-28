import { useEffect, useState } from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import { Modal } from '../shared/Modal';
import { fetchSimGuide } from '../../api/sim';
import { FaDice } from 'react-icons/fa';

/** Strips the parts of `SIMULATION_GUIDE.md` that are written for developers, not players: the
 *  leading H1 (redundant with this modal's own title), the dev-doc cross-link in the intro
 *  paragraph, and the trailing "Where to look next" section, whose links (README.md, a frontend
 *  file path) don't resolve inside the app. Everything else in the guide is player-facing as-is. */
function toDisplayMarkdown(raw: string): string {
    return raw
        .replace(/^# .+\n/, '')
        .replace(/ For the file-by-file developer reference, see \[README\.md]\(README\.md\)\./, '')
        .split(/\n## Where to look next[\s\S]*$/)[0];
}

const markdownComponents: Components = {
    h2: ({ children }) => (
        <h2 className="mt-6 first:mt-0 text-[15px] font-black text-(--text-primary) pb-1.5 border-b border-(--divider)">
            {children}
        </h2>
    ),
    h3: ({ children }) => <h3 className="mt-4 text-[13px] font-black text-(--text-primary)">{children}</h3>,
    p: ({ children }) => <p className="text-[13px] leading-relaxed text-(--text-secondary)">{children}</p>,
    ul: ({ children }) => <ul className="list-disc pl-5 space-y-1.5 text-[13px] leading-relaxed text-(--text-secondary)">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal pl-5 space-y-1.5 text-[13px] leading-relaxed text-(--text-secondary)">{children}</ol>,
    li: ({ children }) => <li>{children}</li>,
    strong: ({ children }) => <strong className="font-black text-(--text-primary)">{children}</strong>,
    hr: () => <hr className="border-(--divider) my-1" />,
    code: ({ children }) => (
        <code className="px-1 py-0.5 rounded bg-(--background-secondary) text-(--showdown-blue) text-[12px] font-mono">{children}</code>
    ),
    a: ({ href, children }) => {
        // Only absolute links resolve outside the app - everything else in the guide is a
        // relative cross-link into the repo (e.g. README.md) that would just 404 in the SPA.
        if (href && /^https?:\/\//.test(href)) {
            return (
                <a href={href} target="_blank" rel="noopener noreferrer" className="text-(--showdown-blue) underline underline-offset-2 hover:no-underline">
                    {children}
                </a>
            );
        }
        return <>{children}</>;
    },
};

function GuideSkeleton() {
    return (
        <div className="flex flex-col gap-3 animate-pulse">
            <div className="h-3 w-3/4 rounded bg-(--background-secondary)" />
            <div className="h-3 w-full rounded bg-(--background-secondary)" />
            <div className="h-3 w-5/6 rounded bg-(--background-secondary)" />
            <div className="h-4 w-1/3 rounded bg-(--background-secondary) mt-3" />
            <div className="h-3 w-full rounded bg-(--background-secondary)" />
            <div className="h-3 w-full rounded bg-(--background-secondary)" />
            <div className="h-3 w-2/3 rounded bg-(--background-secondary)" />
        </div>
    );
}

/**
 * Plain-language "how does this work" reference for the season sim engine, sourced live from
 * `core/simulation/SIMULATION_GUIDE.md` so this never drifts out of sync with the actual doc.
 * The rotating one-liners in `SimEngineExplainer` are the short version of the same content,
 * shown while a run is in flight; this is the long-form version, shown on demand.
 */
export function SimulationGuideModal({ onClose }: { onClose: () => void }) {
    const [content, setContent] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let stale = false;
        fetchSimGuide()
            .then(text => { if (!stale) setContent(text); })
            .catch(err => { if (!stale) setError(err instanceof Error ? err.message : String(err)); });
        return () => { stale = true; };
    }, []);

    return (
        <Modal 
            onClose={onClose} 
            title={<><FaDice className="inline mr-2" />How the Simulation Works</>}
            subtitle="What the engine assumes, decides, and deliberately leaves out" 
            size="lg"
        >
            <div className="p-5">
                {error ? (
                    <p className="text-[13px] text-red-500">{error}</p>
                ) : content ? (
                    <div className="flex flex-col gap-3">
                        <ReactMarkdown components={markdownComponents}>{toDisplayMarkdown(content)}</ReactMarkdown>
                    </div>
                ) : (
                    <GuideSkeleton />
                )}
            </div>
        </Modal>
    );
}
