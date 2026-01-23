import requests

def fetch_betify_events_minimal(BRAND="2491953325260546049", sports_target=None, lang="en"):
    if sports_target is None:
        sports_target = ["17","22","43", "44","45", "46", "48"]  # tes sports

    # 1) On récupère juste la dernière version (snapshot = 0)
    url = f"https://api-a-c7818b61-600.sptpub.com/api/v4/prematch/brand/{BRAND}/{lang}/0"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []

    data = resp.json()
    events = data.get("events", {})
    categories = data.get("categories", {})

    filtered_events = []

    for event_id, event_data in events.items():
        desc = event_data.get("desc", {})
        sport_id = str(desc.get("sport"))
        if sport_id not in sports_target:
            continue

        # On récupère juste les infos essentielles
        category_id = desc.get("category")
        competition_name = categories.get(str(category_id), {}).get("name", "")

        filtered_events.append({
            "event_id": event_id,
            "sport_id": sport_id,
            "slug": desc.get("slug"),
            "scheduled": desc.get("scheduled"),
            "competition": competition_name
        })

    return filtered_events
