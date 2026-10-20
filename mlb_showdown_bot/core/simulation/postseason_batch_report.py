from .postseason_batch import ROUND_LABELS, NotableGameTag, PostseasonBatchSummary
from .social_report import SocialSheetReport

_NOTABLE_LABELS = {
    NotableGameTag.WALK_OFF.value: "Walk-offs",
    NotableGameTag.EXTRA_INNINGS.value: "Extra-inning games",
    NotableGameTag.BLOWOUT.value: "Blowouts (7+ runs)",
}


class PostseasonBatchReport(SocialSheetReport):
    """Renders a `PostseasonBatchSummary` as a single self-contained HTML page - see
    `SocialSheetReport` for the 1080px layout and the PDF/image export. Two 1080x1350 sheets."""

    SHEET_COUNT = 2
    TEMPLATE_NAME = "postseason_batch_summary.html.j2"

    def __init__(self, summary: PostseasonBatchSummary) -> None:
        super().__init__()
        self.summary = summary

    def context(self) -> dict:
        summary = self.summary
        contenders = [t for t in summary.teams if t.titles > 0]
        max_title_pct = max((t.title_pct for t in contenders), default=1) or 1
        leagues = sorted({t.league for t in summary.teams if t.league})
        return dict(
            s=summary,
            contenders=contenders,
            max_title_pct=max_title_pct,
            pennant_races={
                league: sorted([t for t in summary.teams if t.league == league], key=lambda t: -t.pennant_pct)
                for league in leagues
            },
            round_labels=ROUND_LABELS,
            notable_labels=_NOTABLE_LABELS,
        )
