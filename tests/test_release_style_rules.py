"""Offline checks for Release Builder edition style rules.

Run: python tests/test_release_style_rules.py
No DB — exercises the pool label mirror (must match `GROUPERS` in poolGrouping.ts), rule matching,
and how rules layer between the edition style and a card's own overrides in `EditionImagePlan`.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from mlb_showdown_bot.core.set_builder.release_images import EditionImagePlan  # noqa: E402
from mlb_showdown_bot.core.set_builder.release_style_rules import (  # noqa: E402
    EditionStyleRules, ReleaseCardDimensions,
)

failures: list[str] = []


def check(name: str, cond: bool) -> None:
    print(f"  {'ok ' if cond else 'FAIL'} {name}")
    if not cond:
        failures.append(name)


HITTER = {
    'source_card_id': 'hitter',
    'tags': ['FOIL'],
    'card_snapshot': {
        'team': 'ARI', 'league': 'NL', 'positions_list': ['CF', 'LF/RF'], 'is_pitcher': False, 'hand': 'Both',
        'year': '2001-2003', 'is_hof': True, 'awards_list': ['AS', 'MVP-1', 'AS'], 'nationality': 'USA',
        'points': 350.0, 'command': 10.0, 'speed': 18,
    },
}
PITCHER = {
    'source_card_id': 'pitcher',
    'tags': [],
    'card_snapshot': {
        'team': 'MON', 'league': 'NL', 'positions_list': ['RELIEVER'], 'is_pitcher': True, 'hand': 'L',
        'year': 'CAREER', 'is_hof': False, 'awards_list': [], 'nationality': '',
        'points': 90, 'command': 4, 'ip': 1,
    },
}


def labels_mirror_pool_grouping() -> None:
    print("pool labels")
    hitter, pitcher = ReleaseCardDimensions(HITTER), ReleaseCardDimensions(PITCHER)
    expected = {
        'team': (['ARI'], ['WSN']),
        'league': (['NL'], ['NL']),
        'position': (['CF'], ['RELIEVER']),
        'type': (['Position Player'], ['Relief Pitcher']),
        'hand': (['Bats S'], ['LHP']),
        'year': (['2001'], ['Unknown']),
        'hof': (['Hall of Fame'], ['Not in Hall of Fame']),
        'awards': (['AS', 'MVP-1'], ['No Awards']),
        'nationality': (['USA'], ['Unknown']),
        'points': (['300-399 PTS'], ['0-99 PTS']),
        'command': (['Onbase 10'], ['Control 4']),
        'speed': (['Speed 18'], ['Pitchers']),
        'ip': (['Hitters'], ['IP 1']),
        'tag': (['FOIL'], ['Untagged']),
    }
    for dimension, (hitter_labels, pitcher_labels) in expected.items():
        check(f"{dimension}: {hitter_labels} / {pitcher_labels}",
              hitter.labels(dimension) == hitter_labels and pitcher.labels(dimension) == pitcher_labels)
    check("image_match is not a rule dimension", hitter.labels('image_match') is None)


def rule_matching() -> None:
    print("rule matching")
    rules = EditionStyleRules.from_attributes({'style_rules': [
        {'id': 'a', 'when': {'team': ['ARI']}, 'style': {'image_coloring': 'SECONDARY'}},
        # OR within a dimension, AND across
        {'id': 'b', 'when': {'tag': ['FOIL', 'SP'], 'type': ['Position Player']}, 'style': {'image_parallel': 'RF', 'is_bordered': True}},
        # Later rule wins
        {'id': 'c', 'when': {'hof': ['Hall of Fame']}, 'style': {'image_coloring': 'MULTI'}},
        # Incomplete and unknown-dimension rules never match
        {'id': 'd', 'when': {}, 'style': {'is_dark_mode': True}},
        {'id': 'e', 'when': {'team': []}, 'style': {'is_dark_mode': True}},
        {'id': 'f', 'when': {'team': ['ARI'], 'image_match': ['Exact']}, 'style': {'is_dark_mode': True}},
        {'id': 'g', 'when': {'team': ['ARI']}, 'style': {}},
        'not a rule',
    ]})
    check("malformed rule dropped", len(rules.rules) == 7)
    check("hitter gets matching rules, later wins, non-rule keys dropped",
          rules.style_for(HITTER) == {'image_coloring': 'MULTI', 'image_parallel': 'RF'})
    check("pitcher matches nothing", rules.style_for(PITCHER) == {})
    check("no rules attribute", EditionStyleRules.from_attributes({}).rules == [])


def image_plan_layering() -> None:
    print("image plan layering")
    card_with_override = {**HITTER, 'card_number': '1', 'card_overrides': {'style': {'image_coloring': 'PRIMARY'}}}
    plan = EditionImagePlan({
        'id': 'edition', 'release_id': 'release',
        'attributes': {
            'style': {'image_parallel': 'GOLD', 'is_dark_mode': True},
            'style_rules': [
                {'when': {'tag': ['FOIL']}, 'style': {'image_parallel': 'RF', 'image_coloring': 'SECONDARY'}},
                {'when': {'type': ['Relief Pitcher']}, 'style': {'is_dark_mode': False}},
            ],
        },
        'cards': [card_with_override, {**PITCHER, 'card_number': '2'}],
    })
    hitter_style, pitcher_style = plan.specs[0].style, plan.specs[1].style
    check("rule beats edition style", hitter_style.image_parallel == 'RF')
    check("card override beats rule", hitter_style.image_coloring == 'PRIMARY')
    check("edition style kept where no rule applies", hitter_style.is_dark_mode is True and pitcher_style.image_parallel == 'GOLD')
    check("rule can turn a toggle off", pitcher_style.is_dark_mode is False)

    plain = EditionImagePlan({'id': 'edition', 'release_id': 'release', 'attributes': {'style': {'image_parallel': 'GOLD'}}, 'cards': [{**HITTER, 'card_number': '1'}]})
    check("rules change the render hash", plain.specs[0].render_hash != plan.specs[0].render_hash)


def edition_set_year() -> None:
    def plan_for(style: dict, card: dict = HITTER) -> EditionImagePlan:
        return EditionImagePlan({'id': 'edition', 'release_id': 'release', 'attributes': {'style': style}, 'cards': [{**card, 'card_number': '1'}]})

    unset, dated = plan_for({}).specs[0], plan_for({'set_year': '2026'}).specs[0]
    check("edition set year reaches the card", dated.styled_card_json({'image': {}})['image']['set_year'] == '2026')
    check("set year changes the render hash", unset.render_hash != dated.render_hash)
    check("unset set year stays out of the render hash", plan_for({'set_year': ''}).specs[0].render_hash == unset.render_hash)
    custom = {**HITTER, 'card_overrides': {'style': {'set_year': '1999'}}}
    check("card set year beats the edition's", plan_for({'set_year': '2026'}, custom).specs[0].style.set_year == '1999')
    check("cleared set year replaces the card's own", unset.styled_card_json({'image': {'set_year': 1999}})['image']['set_year'] is None)


if __name__ == '__main__':
    labels_mirror_pool_grouping()
    rule_matching()
    image_plan_layering()
    edition_set_year()
    if failures:
        print(f"\n{len(failures)} failed")
        sys.exit(1)
    print("\nall passed")
