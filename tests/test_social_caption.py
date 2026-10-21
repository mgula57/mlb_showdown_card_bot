"""Offline tests for the social post caption builder and card picker (scripts/social)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "social"))

from caption import CaptionBuilder, MAX_POST_LENGTH, HITTER_TEMPLATES, PITCHER_TEMPLATES  # noqa: E402
from pick_card import CardPicker, card_key_for_row  # noqa: E402

HITTER_ROW = {
    "card_id": "2001-bondsba01-2001", "name": "Barry Bonds", "year": 2001, "bref_id": "bondsba01",
    "showdown_set": "2001", "player_type": "HITTER", "is_pitcher": False, "team_id": "SFG",
    "team_id_list": ["SFG"], "points": 760, "command": 16, "speed": 15,
    "positions_and_defense_string": "LF/RF+1", "real_batting_avg": "0.328", "real_onbase_perc": "0.515",
    "real_slugging_perc": "0.863", "real_onbase_plus_slugging": "1.379", "real_hr": 73, "real_sb": 13,
}
PITCHER_ROW = {
    "card_id": "2000-martipe02-CLASSIC", "name": "Pedro Martinez", "year": 2000, "bref_id": "martipe02",
    "showdown_set": "CLASSIC", "player_type": "PITCHER", "is_pitcher": True, "team_id": "BOS",
    "team_id_list": ["BOS"], "points": 690, "command": 6, "ip": 7, "positions_and_defense_string": "SP",
    "real_earned_run_avg": "1.74", "real_whip": "0.737", "real_so": 284, "real_w": 18, "real_sv": 0,
}
CARD = {"accolades": ["NL MVP", "HR LEADER"]}


def test_every_hitter_template_renders_within_limit():
    for _ in range(200):
        caption = CaptionBuilder(HITTER_ROW, CARD).caption()
        assert len(caption) <= MAX_POST_LENGTH
        assert "Barry Bonds" in caption and "{" not in caption


def test_pitcher_caption_uses_pitcher_facts():
    captions = {CaptionBuilder(PITCHER_ROW, CARD).caption() for _ in range(200)}
    assert len(captions) == len(PITCHER_TEMPLATES)
    assert all("Control +6" in c for c in captions)
    assert not any("OB " in c for c in captions)


def test_hitter_uses_all_templates_and_real_stats():
    captions = {CaptionBuilder(HITTER_ROW, CARD).caption() for _ in range(300)}
    assert len(captions) == len(HITTER_TEMPLATES)
    assert any(".328/.515/.863, 73 HR" in c for c in captions)
    assert any("73 home runs" in c for c in captions)


def test_missing_stats_fall_back_to_usable_templates():
    row = {k: v for k, v in HITTER_ROW.items() if not k.startswith("real_")}
    for _ in range(50):
        caption = CaptionBuilder(row, {}).caption()
        assert "{" not in caption and "Barry Bonds" in caption


def test_alt_text_describes_card():
    alt = CaptionBuilder(PITCHER_ROW, CARD).alt_text()
    assert alt.startswith("MLB Showdown card for 2000 Pedro Martinez (BOS), Classic set")
    assert "Control +6" in alt and "IP 7" in alt


def test_card_key_and_exclusion():
    assert card_key_for_row(HITTER_ROW) == "bondsba01-2001"
    assert card_key_for_row({**HITTER_ROW, "player_type_override": "(pitcher)"}) == "bondsba01-2001-pitcher"
    picker = CardPicker(api=None, excluded_keys={"bondsba01-2001"}, output_dir=Path("."))
    assert picker.eligible_candidates([HITTER_ROW, PITCHER_ROW]) == [PITCHER_ROW]
