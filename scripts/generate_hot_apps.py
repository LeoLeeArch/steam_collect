import os
import requests

def generate():
    """Fetch top 6000 most played/owned games from SteamSpy API."""
    os.makedirs("data", exist_ok=True)
    hot_apps = []
    print("Fetching top ~6000 hot games from SteamSpy...")
    
    # SteamSpy pages return 1000 results each. Pages 0-5 = 6000 games.
    for page in range(6):
        print(f"Fetching page {page}/5...")
        try:
            resp = requests.get(f"https://steamspy.com/api.php?request=all&page={page}", timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for appid in data.keys():
                    hot_apps.append(str(appid))
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            
    if hot_apps:
        # Deduplicate while preserving order
        seen = set()
        unique_hot_apps = []
        for appid in hot_apps:
            if appid not in seen:
                seen.add(appid)
                unique_hot_apps.append(appid)
                
        with open("data/hot_apps.txt", "w", encoding="utf-8") as f:
            for appid in unique_hot_apps:
                f.write(f"{appid}\n")
        print(f"Successfully saved {len(unique_hot_apps)} hot games to data/hot_apps.txt")
    else:
        print("Failed to fetch hot games.")

if __name__ == "__main__":
    generate()
