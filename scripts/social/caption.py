"""Post captions and image alt text built from real card data."""
import random
from string import Formatter

MAX_POST_LENGTH = 280
MAX_ALT_TEXT_LENGTH = 1000
HASHTAG = "#MLBShowdown"

# `{fact}` names must be keys produced by `CaptionBuilder.facts`. A template is only used when every
# fact it references exists for the card, so a card missing real stats still gets a caption.
HITTER_TEMPLATES = [
    "{year} {name}{team}. {points} PTS, OB {command}, SPD {speed}. {stat_line}.",
    "{name}, {year} ({set_label} set): {highlight}. On the card that's OB {command} for {points} points.",
    "Random pull: {year} {name}. {stat_line} in real life, {points} PTS and OB {command} on the card.",
    "{year} {name} at {positions}. OB {command}, SPD {speed}, {points} points. {highlight}.",
]
PITCHER_TEMPLATES = [
    "{year} {name}{team}. Control {command}, IP {ip}, {points} PTS. {stat_line}.",
    "{name}, {year} ({set_label} set): {highlight}. On the card that's Control {command}, IP {ip} for {points} points.",
    "Random pull: {year} {name}. {stat_line} in real life, Control {command} and {points} PTS on the card.",
]
FALLBACK_TEMPLATE = "{year} {name}, {set_label} set."


def _float(value) -> float | None:
    """API numerics can arrive as strings (Decimal columns); treat blanks as missing."""
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _rate(value: float) -> str:
    """.312 style for AVG/OBP/SLG, 1.035 for OPS over 1."""
    return f"{value:.3f}".removeprefix("0")


def _template_fields(template: str) -> set[str]:
    return {field for _, field, _, _ in Formatter().parse(template) if field}


class CaptionBuilder:
    """Builds the post text and image alt text for one card.

    Args:
      row: `card_bot` row from /cards/search (flattened card attributes + real stats).
      card: Full serialized ShowdownPlayerCard (used for accolades).
    """

    def __init__(self, row: dict, card: dict) -> None:
        self.row = row
        self.card = card
        self.is_pitcher = bool(row.get("is_pitcher")) or row.get("player_type") == "PITCHER"

    @property
    def set_label(self) -> str:
        showdown_set = str(self.row.get("showdown_set") or self.card.get("set") or "")
        return showdown_set.title() if showdown_set.isalpha() else f"'{showdown_set[-2:]}"

    def facts(self) -> dict[str, str]:
        """Every caption fact available for this card, already formatted. Missing facts are omitted."""
        row = self.row
        facts: dict[str, str] = {
            "name": str(row["name"]),
            "year": str(row["year"]),
            "set_label": self.set_label,
        }
        team = row.get("team_id")
        facts["team"] = f" ({team})" if team and len(row.get("team_id_list") or [team]) <= 1 else ""

        points, command = _float(row.get("points")), _float(row.get("command"))
        if points is not None:
            facts["points"] = str(int(points))
        if command is not None:
            facts["command"] = f"+{int(command)}" if self.is_pitcher else str(int(command))
        if row.get("positions_and_defense_string"):
            facts["positions"] = str(row["positions_and_defense_string"])

        if self.is_pitcher:
            ip = _float(row.get("ip"))
            if ip is not None:
                facts["ip"] = str(int(ip))
            stat_line, highlight = self._pitcher_stats()
        else:
            speed = _float(row.get("speed"))
            if speed is not None:
                facts["speed"] = str(int(speed))
            stat_line, highlight = self._hitter_stats()

        if stat_line:
            facts["stat_line"] = stat_line
        accolades = self.card.get("accolades") or []
        highlight = highlight or (accolades[0] if accolades else None)
        if highlight:
            facts["highlight"] = highlight
        return facts

    def _hitter_stats(self) -> tuple[str | None, str | None]:
        """(slash line + counting stats, single most notable stat)."""
        row = self.row
        avg, obp, slg = (_float(row.get(k)) for k in ("real_batting_avg", "real_onbase_perc", "real_slugging_perc"))
        ops = _float(row.get("real_onbase_plus_slugging"))
        hr, sb = _float(row.get("real_hr")), _float(row.get("real_sb"))

        stat_line = None
        if avg is not None and obp is not None and slg is not None:
            stat_line = f"{_rate(avg)}/{_rate(obp)}/{_rate(slg)}"
            if hr is not None:
                stat_line += f", {int(hr)} HR"
            if sb is not None and sb >= 20:
                stat_line += f", {int(sb)} SB"

        highlights = [
            (hr is not None and hr >= 40, f"{int(hr or 0)} home runs"),
            (sb is not None and sb >= 40, f"{int(sb or 0)} stolen bases"),
            (ops is not None and ops >= 0.950, f"a {_rate(ops or 0)} OPS"),
            (avg is not None and avg >= 0.330, f"a {_rate(avg or 0)} average"),
        ]
        highlight = next((text for is_notable, text in highlights if is_notable), None)
        return stat_line, highlight

    def _pitcher_stats(self) -> tuple[str | None, str | None]:
        row = self.row
        era, whip = _float(row.get("real_earned_run_avg")), _float(row.get("real_whip"))
        so, wins, saves = _float(row.get("real_so")), _float(row.get("real_w")), _float(row.get("real_sv"))

        stat_line = None
        if era is not None:
            parts = [f"{era:.2f} ERA"]
            if whip is not None:
                parts.append(f"{whip:.2f} WHIP")
            if so is not None:
                parts.append(f"{int(so)} K")
            if saves is not None and saves >= 10:
                parts.append(f"{int(saves)} SV")
            stat_line = ", ".join(parts)

        highlights = [
            (era is not None and era <= 2.50, f"a {era or 0:.2f} ERA"),
            (so is not None and so >= 200, f"{int(so or 0)} strikeouts"),
            (saves is not None and saves >= 30, f"{int(saves or 0)} saves"),
            (wins is not None and wins >= 18, f"{int(wins or 0)} wins"),
        ]
        highlight = next((text for is_notable, text in highlights if is_notable), None)
        return stat_line, highlight

    def caption(self) -> str:
        """Random template among those the card has facts for, with the hashtag when it fits."""
        facts = self.facts()
        templates = PITCHER_TEMPLATES if self.is_pitcher else HITTER_TEMPLATES
        usable = [t for t in templates if _template_fields(t) <= facts.keys()] or [FALLBACK_TEMPLATE]
        text = random.choice(usable).format(**facts)
        if len(text) + len(HASHTAG) + 2 <= MAX_POST_LENGTH:
            text += f"\n\n{HASHTAG}"
        return text[:MAX_POST_LENGTH]

    def alt_text(self) -> str:
        """Screen-reader description: player, season, set and the card's key ratings."""
        facts = self.facts()
        parts = [f"MLB Showdown card for {facts['year']} {facts['name']}{facts['team']}, {facts['set_label']} set"]
        if "points" in facts:
            parts.append(f"{facts['points']} points")
        if "command" in facts:
            parts.append(f"{'Control' if self.is_pitcher else 'On-Base'} {facts['command']}")
        if "ip" in facts:
            parts.append(f"IP {facts['ip']}")
        if "speed" in facts:
            parts.append(f"Speed {facts['speed']}")
        if "positions" in facts:
            parts.append(f"Positions {facts['positions']}")
        if "stat_line" in facts:
            parts.append(f"Real stats: {facts['stat_line']}")
        return (". ".join(parts) + ".")[:MAX_ALT_TEXT_LENGTH]
