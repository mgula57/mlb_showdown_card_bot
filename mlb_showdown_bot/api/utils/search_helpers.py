
def summarize_awards(award_string: str) -> str:
    """Summarize award string into counts"""
    if award_string is None or award_string.strip() == '':
        return None

    # Parse awards and count key ones
    award_list = [award.strip() for award in award_string.split(',')]
    award_counts = {}
    key_awards = ['MVP-1', 'CYA-1', 'ROY-1', 'GG', 'SS', 'AS']
    
    for award in award_list:
        if award in key_awards:
            award_counts[award] = award_counts.get(award, 0) + 1

    final_strings = []
    for award in key_awards:
        count = award_counts.get(award, 0)
        if count == 0:
            continue
        award_cleaned = award.split('-')[0] if '-' in award else award
        final_str = f"{count}x {award_cleaned}"
        if final_str.startswith('1x '):
            final_str = final_str.replace('1x ', '', 1)
        final_strings.append(final_str)
    
    return ','.join(final_strings) if final_strings else None

def get_career_records(cursor, name: str) -> list[dict]:
    """Get career records for a player."""
    cursor.execute("""
        SELECT 
            name, bref_id, bool_or(is_hof) as is_hof,
            string_agg(DISTINCT team, ',' ORDER BY team) as team,
            string_agg(DISTINCT award_summary, ',' ORDER BY award_summary) as award_summary,
            SUM(COALESCE(bwar, 0)) as career_bwar,
            MIN(year) as first_year, MAX(year) as last_year
        FROM player_year_list
        WHERE name LIKE LOWER(%s)
        GROUP BY name, bref_id
        ORDER BY career_bwar desc
    """, (f"%{name}%",))

    results = cursor.fetchall()
    displays = []
    
    for row in results:
        name, bref_id, is_hof, team, award_summary, career_bwar, first_year, last_year = row
        award_summary = summarize_awards(award_summary)
        displays.append({
            'type': 'career',
            'name': name,
            'year': f"{int(first_year)}-{int(last_year)}",
            'year_display': f"Career ({int(first_year)}-{int(last_year)})",
            'bref_id': bref_id,
            'is_hof': is_hof,
            'award_summary': award_summary,
            'bwar': round(career_bwar, 1),
            'team': team,
        })
    
    return displays