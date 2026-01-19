import requests
import re
from typing import List, Dict
import csv
import io

# -------------------------------
# CONSTANTS
# -------------------------------
CHADWICK_API_URL = (
    "https://api.github.com/repos/chadwickbureau/register/contents/data"
)
PEOPLE_RE = re.compile(r"^people-[0-9a-z]+\.csv$")


# -------------------------------
# METHODS
# -------------------------------

def _list_people_csv_urls(requests_session: requests.Session) -> List[str]:
    """List all available player ID CSV files from chadwickbureau register repo.
     
    Returns:
        List of download URLs for player ID CSV files.
    """
    resp = requests_session.get(CHADWICK_API_URL, timeout=30)
    resp.raise_for_status()

    files = resp.json()
    urls = []

    for f in files:
        name = f.get("name", "")
        if PEOPLE_RE.match(name):
            urls.append(f["download_url"])

    return urls


def fetch_player_id_csv() -> List[Dict[str, object]]:
    """Fetch player ID CSV from chadwickbureau. Enables easier ID mapping between various baseball data sources."""
    
    """
    Downloads Chadwick people CSVs and returns a list of dicts
    containing only rows with both bbref and mlbam IDs.
    """
    session = requests.Session()
    results = []

    # Get all parts of the people CSVs
    urls = _list_people_csv_urls(session)

    if urls is None or len(urls) == 0:
        return results

    for url in urls:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()

        reader = csv.DictReader(io.StringIO(resp.text))
        for r in reader:
            bbref = (r.get("key_bbref") or "").strip()
            mlbam = (r.get("key_mlbam") or "").strip()
            fangraphs = (r.get("key_fangraphs") or "").strip()

            # Skip rows without both IDs
            if not bbref or not mlbam: continue

            try: mlbam_id = int(mlbam)
            except ValueError: continue

            try: fangraphs_id = int(fangraphs) if fangraphs else None
            except ValueError: fangraphs_id = None

            try: mlb_first_year = int(r.get("mlb_played_first", None))
            except ValueError: mlb_first_year = None

            try: mlb_last_year = int(r.get("mlb_played_last", None))
            except ValueError: mlb_last_year = None

            results.append({
                "bref_id": bbref,
                "mlb_id": mlbam_id,
                "fangraphs_id": fangraphs_id,
                "name_first": (r.get("name_first") or "").strip() or None,
                "name_last": (r.get("name_last") or "").strip() or None,
                "mlb_first_year": mlb_first_year,
                "mlb_last_year": mlb_last_year,
            })

    return results
    
