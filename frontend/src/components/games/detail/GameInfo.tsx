import type { BoxscoreTeamData } from "../../../api/mlbAPI";
import { Heading } from "../../shared/Heading";
import { CAPS_LABEL_CLASS } from "../../shared/fieldStyles";

export default function GameInfo({ away, home }: { away: BoxscoreTeamData; home: BoxscoreTeamData }) {
    const allInfo = [...away.info, ...home.info];

    if (allInfo.length === 0) return null;

    return (
        <div className="rounded-card border border-(--divider) bg-(--background-secondary) p-3 space-y-3">
            <Heading level="panel" as="div">Game Info</Heading>
            {allInfo.map((section, idx) => (
                <div key={idx} className="space-y-1">
                    <div className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>{section.title}</div>
                    {section.fieldList.map((field, fidx) => (
                        <div key={fidx} className="flex gap-2 text-xs">
                            <span className="font-bold text-(--primary) shrink-0">{field.label}:</span>
                            <span className="text-(--secondary)">{field.value}</span>
                        </div>
                    ))}
                </div>
            ))}
        </div>
    );
}
