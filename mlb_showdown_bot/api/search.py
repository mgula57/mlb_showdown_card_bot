from flask import Blueprint, request, jsonify
from datetime import datetime
from ..core.shared.team import Team
from .utils.search_helpers import summarize_awards, get_career_records

search_bp = Blueprint('search', __name__)

@search_bp.route('/players/search', methods=["POST", "GET"])
def search_players():

    # USER QUERY
    query = request.args.get('q', '').strip()

    # OPTIONS
    exclude_multi_year = request.args.get('exclude_multi_year', 'false').lower() == 'true'

    # MINIMUM OF 2 CHARACTERS
    if len(query) < 2:
        return jsonify([])

    # IF ALL DIGITS, MINIMUM OF 4 CHARACTERS
    if query.isdigit() and len(query) < 4:
        return jsonify([])

    try:
        from mlb_showdown_bot.core.database.postgres_db import PostgresDB

        # CONNECT TO DB
        conn = PostgresDB(is_archive=True).connection # TODO: CHANGE BEFORE PROD
        cursor = conn.cursor()

        # Check query type
        query_lower = query.lower()
        is_team_search = len(query) in [2, 3] and query_lower in [team.value.lower() for team in Team]
        is_year_query = query.isdigit() and len(query) == 4
        is_career_query = query_lower in ['career', 'careers', 'all time', 'best'] and not exclude_multi_year
        is_year_range = '-' in query and len(query.split('-')) == 2 and not exclude_multi_year
        is_name_and_year = (query_lower.split(' ')[-1].isdigit() or query_lower.split(' ')[-1] == 'career') \
                             and len(query_lower.split(' ')) > 1
        
        # Check for name + team pattern (e.g., "Judge NYY", "Trout LAA")
        is_name_and_team = False
        player_name = None
        team_code = None

        if ' ' in query and len(query.split()) >= 2:
            parts = query.split()
            potential_team = parts[-1].upper()  # Last word as potential team
            # Check if last word is a valid team code
            if potential_team in [team.value for team in Team]:
                is_name_and_team = True
                player_name = ' '.join(parts[:-1])  # Everything except last word
                team_code = potential_team

        # -------------------
        # TEAM SEARCH
        # -------------------
        if is_team_search:
            team_code = query_lower.upper()
            cursor.execute("""
                SELECT 
                    name,
                    year,
                    bref_id,
                    team,
                    is_hof,
                    award_summary,
                    bwar
                FROM player_search
                WHERE team = %s
                ORDER BY COALESCE(bwar, 0) DESC, year DESC, name
                LIMIT 30
            """, (team_code,))
            
            results = cursor.fetchall()
            displays = []
            for name, year, bref_id, team, is_hof, award_summary, bwar in results:
                displays.append({
                    'type': 'single_year',
                    'name': name,
                    'year': int(year),
                    'year_display': str(int(year)),
                    'bref_id': bref_id,
                    'team': team,
                    'is_hof': is_hof,
                    'award_summary': award_summary,
                    'bwar': bwar,
                })

        # -------------------
        # CAREER SEARCH - TOP PLAYERS BY TOTAL CAREER BWAR
        # -------------------
        elif is_career_query:
            
            cursor.execute("""
                SELECT 
                    name,
                    bref_id,
                    bool_or(is_hof) as is_hof,
                    string_agg(DISTINCT team, ',' ORDER BY team) as team,
                    string_agg(DISTINCT award_summary, ',' ORDER BY award_summary) as award_summary,
                    SUM(COALESCE(bwar, 0)) as career_bwar,
                    MIN(year) as first_year,
                    MAX(year) as last_year,
                    COUNT(*) as seasons
                FROM player_search
                WHERE bwar IS NOT NULL
                GROUP BY name, bref_id
                HAVING SUM(COALESCE(bwar, 0)) > 5
                ORDER BY career_bwar DESC
                LIMIT 30
            """)

            results = cursor.fetchall()
            displays = []
            for name, bref_id, is_hof, team, award_summary, career_bwar, first_year, last_year, seasons in results:
                displays.append({
                    'type': 'career',
                    'name': name,
                    'year': "CAREER",
                    'year_display': f"Career ({int(first_year)}-{int(last_year)})",
                    'bref_id': bref_id,
                    'is_hof': is_hof,
                    'award_summary': award_summary,
                    'bwar': round(career_bwar, 1),
                    'seasons': seasons,
                    'team': team,
                })

        # -------------------
        # YEAR RANGE SEARCH (EX: "2006-2008")
        # -------------------
        elif is_year_range:
            try:
                year_parts = query.split('-')
                start_year = int(year_parts[0].strip())
                end_year = int(year_parts[1].strip())

                # FLIP IF NECESSARY
                if start_year > end_year:
                    start_year, end_year = end_year, start_year
                
                cursor.execute("""
                    SELECT 
                        name,
                        bref_id,
                        bool_or(is_hof) as is_hof,
                        string_agg(DISTINCT team, ',' ORDER BY team) as team,
                        MIN(year) as first_year,
                        MAX(year) as last_year,
                        string_agg(DISTINCT award_summary, ',' ORDER BY award_summary) as award_summary,
                        SUM(COALESCE(bwar, 0)) as total_bwar
                    FROM player_search
                    WHERE year BETWEEN %s AND %s
                        AND bwar IS NOT NULL
                    GROUP BY name, bref_id
                    HAVING SUM(COALESCE(bwar, 0)) > 1
                    ORDER BY total_bwar DESC
                    LIMIT 30
                """, (start_year, end_year))
                
                results = cursor.fetchall()
                displays = []
                for name, bref_id, is_hof, team, first_year, last_year, award_summary, total_bwar in results:

                    
                    award_list = [award.strip() for award in award_summary.split(',')]

                    award_counts = {}
                    key_awards = ['MVP-1', 'CYA-1', 'ROY-1', 'GG', 'SS', 'AS',]
                    for award in award_list:
                        if award in key_awards:
                            award_counts[award] = award_counts.get(award, 0) + 1

                    final_strings = []
                    for award in key_awards:
                        count = award_counts.get(award, 0)
                        if count == 0: continue
                        award_cleaned = award
                        if '-' in award:
                            award_cleaned = award.split('-')[0]
                        final_str = f"{count}x {award_cleaned}"
                        if final_str.startswith('1x '):
                            final_str = final_str.replace('1x ', '', 1)
                        final_strings.append(final_str)
                    award_summary = summarize_awards(award_summary)

                    displays.append({
                        'type': 'year_range',
                        'name': name,
                        'year': f"{int(first_year)}-{int(last_year)}",
                        'year_display': f"{int(first_year)}-{int(last_year)}",
                        'bref_id': bref_id,
                        'is_hof': is_hof,
                        'award_summary': award_summary,
                        'bwar': round(total_bwar, 1),
                        'team': team,
                    })
            except (ValueError, IndexError):
                displays = []
        
        # -------------------
        # SINGLE YEAR (EX: "2006")
        # -------------------
        elif is_year_query:
            # Single year search
            cursor.execute("""
                SELECT 
                    name,
                    year,
                    bref_id,
                    team,
                    is_hof,
                    award_summary,
                    bwar
                FROM player_search
                WHERE year = %s
                ORDER BY COALESCE(bwar, 0) DESC, name
                LIMIT 30
            """, (int(query),))
            
            results = cursor.fetchall()
            displays = []
            for name, year, bref_id, team, is_hof, award_summary, bwar in results:
                displays.append({
                    'type': 'single_year',
                    'name': name,
                    'year': year,
                    'bref_id': bref_id,
                    'team': team,
                    'is_hof': is_hof,
                    'award_summary': award_summary,
                    'bwar': bwar
                })
        
        # -------------------
        # PLAYER NAME AND YEAR OR CAREER (EX: "Babe Ruth career", "Babe Ruth 1927")
        # -------------------
        elif is_name_and_year:
            name, year = query_lower.rsplit(' ', 1)
            if year == 'career':
                year = 'career'
                displays = get_career_records(cursor=cursor, name=name)
            else:
                year = int(year)
                cursor.execute("""
                    SELECT 
                        name,
                        year,
                        bref_id,
                        team,
                        is_hof,
                        award_summary,
                        bwar
                    FROM player_search
                    WHERE name LIKE LOWER(%s) AND year = %s
                    ORDER BY COALESCE(bwar, 0) DESC, name
                    LIMIT 30
                """, (f'%{name}%', year))

                results = cursor.fetchall()
                displays = []
                for name, year, bref_id, team, is_hof, award_summary, bwar in results:
                    displays.append({
                        'type': 'single_year',
                        'name': name,
                        'year': year,
                        'bref_id': bref_id,
                        'is_hof': is_hof,
                        'award_summary': award_summary,
                        'bwar': bwar,
                        'team': team,
                    })
        
        # -------------------
        # NAME + TEAM SEARCH (EX: "Judge NYY", "Trout LAA")
        # -------------------
        elif is_name_and_team:
            cursor.execute("""
                SELECT 
                    name,
                    year,
                    bref_id,
                    team,
                    is_hof,
                    award_summary,
                    bwar,
                    CASE 
                        WHEN LOWER(name) = LOWER(%s) THEN 1                    -- Exact match
                        WHEN LOWER(name) LIKE LOWER(%s) THEN 2                 -- Starts with
                        WHEN LOWER(name) LIKE LOWER(%s) THEN 3                 -- Contains
                        ELSE 4
                    END as match_rank
                FROM player_search
                WHERE LOWER(name) LIKE LOWER(%s) 
                    AND team = %s
                ORDER BY 
                    LOWER(name) = LOWER(%s) DESC,  -- Exact name match first
                    COALESCE(bwar, 0) DESC,        -- Then by performance
                    match_rank,                    -- Then by name match quality
                    year DESC,                     -- Then by recent years
                    name
                LIMIT 25
            """, (
                player_name,        # Exact match check
                f'{player_name}%',  # Starts with check
                f'%{player_name}%', # Contains check
                f'%{player_name}%', # Main WHERE contains
                team_code,          # Team filter
                player_name         # Exact match check for ordering
            ))
            
            results = cursor.fetchall()
            displays = []
            for name, year, bref_id, team, is_hof, award_summary, bwar, match_rank in results:
                displays.append({
                    'type': 'single_year',
                    'name': name,
                    'year': year,
                    'bref_id': bref_id,
                    'is_hof': is_hof,
                    'award_summary': award_summary,
                    'bwar': bwar,
                    'team': team,
                })
        
        # -------------------
        # REGULAR NAME SEARCH
        # -------------------
        else:
            displays = []

            if not exclude_multi_year:
                exact_match_cursor = conn.cursor()
                exact_match_cursor.execute("""
                    SELECT 
                        name,
                        bref_id,
                        player_type_override,
                        bool_or(is_hof) as is_hof,
                        string_agg(DISTINCT team, ',' ORDER BY team) as team,
                        string_agg(DISTINCT award_summary, ',' ORDER BY award_summary) as award_summary,
                        SUM(COALESCE(bwar, 0)) as career_bwar,
                        MIN(year) as first_year,
                        MAX(year) as last_year
                    FROM player_search
                    WHERE name = LOWER(%s)
                    GROUP BY name, bref_id, player_type_override
                    ORDER BY SUM(COALESCE(bwar, 0)) DESC
                """, (query,))
                
                exact_matches = exact_match_cursor.fetchall() or []
                exact_match_cursor.close()
            
                for exact_match in exact_matches:
                    name, bref_id, player_type_override, is_hof, team, award_summary, career_bwar, first_year, last_year = exact_match
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
                        'player_type_override': player_type_override,
                    })
            
            # Then add individual year results
            cursor.execute("""
                SELECT 
                    name,
                    year,
                    player_type_override,
                    bref_id,
                    team,
                    is_hof,
                    award_summary,
                    bwar,
                    CASE 
                        WHEN LOWER(name) = LOWER(%s) THEN 1                    -- Exact match
                        WHEN LOWER(name) LIKE LOWER(%s) THEN 2                 -- Starts with
                        WHEN LOWER(name) LIKE LOWER(%s) THEN 3                 -- Contains
                        ELSE 4
                    END as match_rank
                FROM player_search
                WHERE LOWER(name) LIKE LOWER(%s)
                ORDER BY 
                    LOWER(name) = LOWER(%s) DESC, -- Exact match first
                    year = %s DESC,               -- Prioritize current year
                    COALESCE(bwar, 0) DESC,
                    match_rank,
                    year DESC,
                    name
                LIMIT 25  -- Reduced to make room for career total
            """, (
                query,              # Exact match check
                f'{query}%',        # Starts with check
                f'%{query}%',       # Contains check
                f'%{query}%',       # Main WHERE contains
                query,              # Exact match check
                datetime.now().year
            ))
            
            results = cursor.fetchall()
            for name, year, player_type_override, bref_id, team, is_hof, award_summary, bwar, match_rank in results:
                displays.append({
                    'type': 'single_year',
                    'name': name,
                    'year': year,
                    'bref_id': bref_id,
                    'is_hof': is_hof,
                    'award_summary': award_summary,
                    'bwar': bwar,
                    'team': team,
                    'player_type_override': player_type_override,
                })

        # CLOSE THE CONNECTION
        conn.close()

        return jsonify(displays)
        
    except Exception as e:
        import traceback
        print(f"Error searching players: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return jsonify([]), 500