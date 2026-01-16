"""
Generate a comprehensive list of Brazilian celebrities from Wikipedia categories.
This script fetches celebrities from various categories and saves them to a JSON file.
"""
import requests
import json
import time
from typing import List, Dict, Set

# User-Agent required by Wikipedia API
HEADERS = {
    "User-Agent": "CelebFaceMatch/1.0 (Brazilian Celebrity Face Recognition Project; Educational Use)"
}

PT_WIKI_API = "https://pt.wikipedia.org/w/api.php"

# Wikipedia categories for Brazilian celebrities
# These are Portuguese Wikipedia category names
# Using more specific subcategories for better coverage
CATEGORIES = [
    # Music
    "Cantores_do_Brasil",
    "Cantoras_do_Brasil",
    "Músicos_do_Brasil",
    "Rappers_do_Brasil",
    "Compositores_do_Brasil",

    # Acting
    "Atores_do_Brasil",
    "Atrizes_do_Brasil",
    "Atores_de_televisão_do_Brasil",
    "Atrizes_de_televisão_do_Brasil",

    # Sports
    "Futebolistas_do_Brasil",
    "Jogadores_da_Seleção_Brasileira_de_Futebol",
    "Pilotos_de_Fórmula_1_do_Brasil",
    "Tenistas_do_Brasil",
    "Surfistas_do_Brasil",
    "Skatistas_do_Brasil",
    "Ginastas_olímpicos_do_Brasil",
    "Jogadores_de_vôlei_do_Brasil",

    # Media & Entertainment
    "Youtubers_do_Brasil",
    "Apresentadores_de_televisão_do_Brasil",
    "Humoristas_do_Brasil",
    "Modelos_do_Brasil",
    "Influenciadores_digitais_do_Brasil",
    "Jornalistas_do_Brasil",
]

def get_category_members(category: str, limit: int = 500, include_subcats: bool = True) -> List[str]:
    """
    Get all members of a Wikipedia category, optionally including subcategories.
    Returns a list of page titles.
    """
    members = []
    continue_token = None
    fetched = 0

    while fetched < limit:
        params = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": min(500, limit - fetched),  # API max is 500
            "cmtype": "page"  # Only pages, not subcategories
        }

        if continue_token:
            params["cmcontinue"] = continue_token

        try:
            response = requests.get(PT_WIKI_API, params=params, headers=HEADERS, timeout=15)
            response.raise_for_status()
            data = response.json()

            for member in data.get("query", {}).get("categorymembers", []):
                title = member.get("title", "")
                # Filter out non-person pages
                if not any(skip in title.lower() for skip in ["lista de", "categoria:", "anexo:", "wikipédia:"]):
                    members.append(title)
                    fetched += 1

            # Check if there are more results
            continue_token = data.get("continue", {}).get("cmcontinue")
            if not continue_token:
                break

        except Exception as e:
            print(f"  Error fetching {category}: {e}")
            break

    print(f"  Found {len(members)} members in {category}")
    return members

def clean_name(name: str) -> str:
    """
    Clean Wikipedia page title to get actual person name.
    Removes disambiguation and other Wikipedia artifacts.
    """
    # Remove disambiguation parentheses
    if "(" in name:
        name = name.split("(")[0].strip()
    
    return name.strip()

def generate_celebrity_list(output_file: str = "data/celebrities_generated.json"):
    """
    Generate a comprehensive celebrity list from Wikipedia categories.
    """
    print("Generating celebrity list from Wikipedia categories...\n")
    
    all_celebs: Set[str] = set()
    category_counts = {}
    
    for category in CATEGORIES:
        print(f"Fetching: {category}")
        members = get_category_members(category)
        category_counts[category] = len(members)
        
        for member in members:
            clean = clean_name(member)
            if clean and len(clean) > 2:  # Basic validation
                all_celebs.add(clean)
        
        # Be nice to Wikipedia's servers
        time.sleep(0.5)
    
    # Convert to list of dicts
    celebrity_list = [
        {
            "name": name,
            "category": "auto"
        }
        for name in sorted(all_celebs)
    ]
    
    # Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(celebrity_list, f, indent=4, ensure_ascii=False)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total unique celebrities: {len(celebrity_list)}")
    print(f"\nBreakdown by category:")
    for cat, count in category_counts.items():
        print(f"  {cat}: {count}")
    print(f"\nSaved to: {output_file}")
    print(f"{'='*60}")
    
    return celebrity_list

if __name__ == "__main__":
    generate_celebrity_list()

