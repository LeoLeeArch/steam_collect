import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

pb_url = os.getenv("POCKETBASE_URL")
pb_email = os.getenv("POCKETBASE_EMAIL")
pb_password = os.getenv("POCKETBASE_PASSWORD")

def setup():
    # Try different auth paths
    auth_paths = ["/api/admins/auth-with-password", "/api/collections/_superusers/auth-with-password"]
    token = None
    
    for path in auth_paths:
        try:
            resp = requests.post(f"{pb_url}{path}", json={
                "identity": pb_email,
                "password": pb_password
            })
            if resp.status_code == 200:
                token = resp.json().get("token")
                print(f"Authenticated successfully using {path}")
                break
        except Exception as e:
            print(f"Error with {path}: {e}")

    if not token:
        print("Failed to authenticate.")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Define collections
    collections = [
        {
            "name": "steam_catalog",
            "type": "base",
            "schema": [
                {"name": "appid", "type": "number", "required": True, "unique": True},
                {"name": "name", "type": "text", "required": True},
                {"name": "type", "type": "text"},
                {"name": "is_free", "type": "bool"},
                {"name": "coming_soon", "type": "bool"},
                {"name": "release_date", "type": "text"},
                {"name": "store_url", "type": "url"},
                {"name": "header_image", "type": "url"},
                {"name": "steam_last_modified", "type": "number"},
                {"name": "steam_price_change_number", "type": "number"},
                {"name": "first_seen_at", "type": "date"},
                {"name": "last_seen_at", "type": "date"},
            ]
        },
        {
            "name": "price_snapshots",
            "type": "base",
            "schema": [
                {"name": "appid", "type": "number", "required": True},
                {"name": "name", "type": "text"},
                {"name": "country_code", "type": "text", "required": True},
                {"name": "currency", "type": "text"},
                {"name": "price_unit", "type": "text", "default": "major"},
                {"name": "initial_price", "type": "number"},
                {"name": "final_price", "type": "number"},
                {"name": "discount_percent", "type": "number"},
                {"name": "is_discounted", "type": "bool"},
                {"name": "is_free_now", "type": "bool"},
                {"name": "discount_description", "type": "text"},
                {"name": "snapshot_date", "type": "text"},
                {"name": "collected_at_utc", "type": "date"},
                {"name": "crawl_run_id", "type": "text"},
            ]
        },
        {
            "name": "batch_controls",
            "type": "base",
            "schema": [
                {"name": "batch_date", "type": "text", "required": True},
                {"name": "region", "type": "text", "required": True},
                {"name": "mode", "type": "text", "required": True},
                {"name": "status", "type": "text", "required": True},
                {"name": "scheduled_time", "type": "date"},
                {"name": "started_at", "type": "date"},
                {"name": "finished_at", "type": "date"},
                {"name": "error_log", "type": "text"},
                {"name": "apps_updated", "type": "number"},
                {"name": "apps_processed", "type": "number"}
            ],
            "indexes": [
                "CREATE UNIQUE INDEX idx_batch_date_region ON batch_controls (batch_date, region)",
                "CREATE INDEX idx_batch_status_time ON batch_controls (status, scheduled_time)"
            ]
        }
    ]

    for coll in collections:
        print(f"Checking collection {coll['name']}...")
        resp = requests.get(f"{pb_url}/api/collections/{coll['name']}", headers=headers, timeout=10)
        if resp.status_code == 200:
            existing_coll = resp.json()
            # Update schema to ensure new fields are present
            coll_id = existing_coll['id']
            print(f"Updating collection {coll['name']} (ID: {coll_id})...")
            resp = requests.patch(f"{pb_url}/api/collections/{coll_id}", headers=headers, json=coll, timeout=10)
            if resp.status_code == 200:
                print(f"Collection {coll['name']} updated successfully.")
            else:
                print(f"Error updating {coll['name']}: {resp.text}")
        else:
            print(f"Creating collection {coll['name']}...")
            resp = requests.post(f"{pb_url}/api/collections", headers=headers, json=coll, timeout=10)
            if resp.status_code == 200:
                print(f"Collection {coll['name']} created.")
            else:
                print(f"Error creating {coll['name']}: {resp.text}")

    # Generate initial batch schedule for next 7 days for all regions
    import datetime
    regions = ["us", "cn", "gb", "jp", "de", "vn", "id", "in"]
    today = datetime.date.today()
    
    print("Generating batch schedule for the next 7 days...")
    for i in range(7):
        batch_date = today + datetime.timedelta(days=i)
        date_str = batch_date.strftime("%Y-%m-%d")
        print(f"Processing date: {date_str}")
        
        for region in regions:
            # Set scheduled time to 01:00 UTC of that day
            scheduled_time = datetime.datetime.combine(batch_date, datetime.time(1, 0)).strftime("%Y-%m-%d %H:%M:%S.000Z")
            
            # Use 'full' for first day, 'incremental' for others
            mode = "full" if i == 0 else "incremental"
            
            batch_data = {
                "batch_date": date_str,
                "region": region,
                "mode": mode,
                "status": "pending",
                "scheduled_time": scheduled_time
            }
            
            # Check if exists
            filter_str = f"batch_date='{date_str}' && region='{region}'"
            check_resp = requests.get(f"{pb_url}/api/collections/batch_controls/records", 
                                    headers=headers, params={"filter": filter_str}, timeout=10)
            
            if check_resp.status_code == 200 and check_resp.json().get("totalItems", 0) > 0:
                # Update existing
                record_id = check_resp.json()["items"][0]["id"]
                # Only reset if it was failed or we want to force re-run today
                if i == 0:
                    print(f"Resetting existing batch for {date_str} {region} to pending/full...")
                    requests.patch(f"{pb_url}/api/collections/batch_controls/records/{record_id}", 
                                 headers=headers, json={"status": "pending", "mode": "full"}, timeout=10)
            else:
                # Create new
                print(f"Creating new batch for {date_str} {region}...")
                requests.post(f"{pb_url}/api/collections/batch_controls/records", 
                            headers=headers, json=batch_data, timeout=10)
    print("Batch schedule initialization complete.")

if __name__ == "__main__":
    setup()
