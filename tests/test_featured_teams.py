"""Offline checks for the admin-curated ('featured') teams feature.

Run: python tests/test_featured_teams.py
No DB — exercises the pure logic (field allow-lists, admin identity, is_drafting,
the publish deep-copy helper, and Team model round-tripping of the new columns).
"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("ADMIN_USER_IDS", "admin-uuid-1, admin-uuid-2")
os.environ.setdefault("ADMIN_EMAILS", "boss@example.com")

from config import Config  # noqa: E402
from mlb_showdown_bot.api.user_settings import is_admin  # noqa: E402
from mlb_showdown_bot.api.admin_teams import _copy_roster_and_lineups  # noqa: E402
from mlb_showdown_bot.core.database.postgres_db import PostgresDB  # noqa: E402
from mlb_showdown_bot.core.card.team_builder.team import Team, TeamSource  # noqa: E402

failures: list[str] = []


def check(name: str, cond: bool) -> None:
    print(f"  {'ok ' if cond else 'FAIL'} {name}")
    if not cond:
        failures.append(name)


print("admin identity")
check("user id on allowlist", is_admin("admin-uuid-1", None))
check("email on allowlist (case-insensitive)", is_admin("nope", "BOSS@example.com"))
check("stranger rejected", not is_admin("someone", "someone@example.com"))
check("empty rejected", not is_admin(None, None))
check("config parsed the env list", "admin-uuid-2" in Config.ADMIN_USER_IDS)

print("field allow-lists")
payload = {
    "name": "T", "is_public": True, "source": "official",
    "collection_slug": "s1", "subtitle": "blurb", "strategy_deck": {"Great Throw": 3},
    "published_by": "admin-uuid-1", "bogus": 1,
}
user_fields = PostgresDB._team_payload_fields(payload)
admin_fields = PostgresDB._admin_team_payload_fields(payload)
check("user path drops source", "source" not in user_fields)
check("user path drops collection_slug", "collection_slug" not in user_fields)
check("user path keeps is_public", user_fields.get("is_public") is True)
check("admin path keeps source", admin_fields.get("source") == "official")
check("admin path keeps curation fields", {"collection_slug", "subtitle", "strategy_deck", "published_by"} <= set(admin_fields))
check("neither path keeps unknown keys", "bogus" not in user_fields and "bogus" not in admin_fields)
check("strategy_deck is a jsonb field", "strategy_deck" in PostgresDB._TEAM_JSONB_FIELDS)

print("is_drafting")
official_row = {"source": "official", "filled_field": 0, "roster_count": 0, "roster_size": 25}
user_row = {"source": "user", "filled_field": 0, "num_starters": 5, "min_bench": 2,
            "min_bullpen": 5, "roster_count": 0, "roster_size": 25}
check("official teams never drafting", PostgresDB._compute_is_drafting(official_row) is False)
check("incomplete user team is drafting", PostgresDB._compute_is_drafting(user_row) is True)

print("Team model round-trips new columns")
t = Team(
    name="Gary Quinn", abbreviation="GQ", source=TeamSource.OFFICIAL, is_public=True,
    collection_slug="showdown-league-s1", subtitle="1996 Champ", credit="Built by Gary Quinn",
    collection_sort_index=2, strategy_deck={"Clutch Hitting": 4},
)
d = t.to_db_dict()
check("to_db_dict carries collection_slug", d["collection_slug"] == "showdown-league-s1")
check("to_db_dict carries strategy_deck", d["strategy_deck"] == {"Clutch Hitting": 4})
back = Team.from_db_row({
    "team_id": "abc", "name": "x", "abbreviation": "x", "roster": [],
    "subtitle": "hi", "credit": "c", "collection_sort_index": 5, "strategy_deck": {"a": 1},
})
check("from_db_row reads subtitle/credit", back.subtitle == "hi" and back.credit == "c")
check("from_db_row reads strategy_deck", back.strategy_deck == {"a": 1})

print("publish deep-copy helper")
src_row = {
    "roster": [
        {"card_id": "c1", "card_source": "WOTC", "roster_position": "SS", "draft_order": 3, "pick_source": "MANUAL", "points": 400},
        {"card_id": "p1", "card_source": "WOTC", "roster_position": "SP1", "draft_order": 1, "pick_source": "AUTOFILL"},
    ],
    "lineups": [
        {"name": "Default", "index": 0, "slots": [{"card_id": "c1", "card_source": "WOTC", "batting_order": 1}]},
        {"name": "vs LHP", "index": 1, "slots": [{"card_id": "c1", "card_source": "WOTC", "batting_order": 2}]},
    ],
}
roster, lineups = _copy_roster_and_lineups(src_row)
check("roster copied without draft history", all(s["draft_order"] is None for s in roster))
check("roster marked IMPORTED", all(s["pick_source"] == "IMPORTED" for s in roster))
check("roster keeps only the schema keys", set(roster[0]) == {"card_id", "card_source", "roster_position", "draft_order", "pick_source"})
check("Default lineup dropped, user lineup kept", [l["name"] for l in lineups] == ["vs LHP"])

print()
if failures:
    print(f"{len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("all featured-teams checks passed")
