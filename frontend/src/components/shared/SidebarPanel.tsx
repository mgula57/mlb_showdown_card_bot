import { type ReactNode } from "react";
import { FaChevronDown } from "react-icons/fa6";

export type SidebarSection = {
    id: string;
    title: string;
    content: ReactNode;
    collapsible?: boolean;
    defaultOpen?: boolean;
    isHidden?: boolean;
};

type SidebarPanelProps = {
    title: string;
    subtitle?: string;
    sections: SidebarSection[];
    className?: string;
    isHidden?: boolean;
};

export default function SidebarPanel({ title, subtitle, sections, className = ""}: SidebarPanelProps) {
    return (
        <aside className={`w-full ${className}`}>
            <div className="rounded-2xl border border-(--divider) bg-(--background-secondary) overflow-hidden">
                <div className="px-4 py-4 border-b border-(--divider)">
                    <h2 className="text-lg font-bold text-(--text-primary)">{title}</h2>
                    {subtitle && <p className="mt-1 text-xs text-(--text-secondary)">{subtitle}</p>}
                </div>

                <div className="p-3 space-y-3">
                    {sections.map((section) => {
                        const isCollapsible = section.collapsible !== false;
                        const isOpen = section.defaultOpen !== false;

                        if (!isCollapsible) {
                            return (
                                <section key={section.id} className={`pb-1 border-b border-(--divider) last:border-b-0 last:pb-0 ${section.isHidden ? "hidden" : ""}`}>
                                    <div className="px-1 pb-2 text-[11px] font-semibold uppercase tracking-wide text-(--text-secondary)">
                                        {section.title}
                                    </div>
                                    <div>{section.content}</div>
                                </section>
                            );
                        }

                        return (
                            <details
                                key={section.id}
                                className={`group pb-2 border-b border-(--divider) last:border-b-0 last:pb-0 ${section.isHidden ? "hidden" : ""}`}
                                open={isOpen}
                            >
                                <summary className="list-none flex items-center justify-between px-1 pb-2 cursor-pointer">
                                    <span className="text-[11px] font-semibold uppercase tracking-wide text-(--text-secondary)">{section.title}</span>
                                    <FaChevronDown className="h-3 w-3 text-(--text-secondary) transition-transform group-open:rotate-180" />
                                </summary>
                                <div>{section.content}</div>
                            </details>
                        );
                    })}
                </div>
            </div>
        </aside>
    );
}
