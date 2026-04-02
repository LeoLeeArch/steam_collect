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
                {"name": "initial_price_minor", "type": "number"},
                {"name": "final_price_minor", "type": "number"},
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
                {"name": "error_log", "type": "text"}
            ],
            "indexes": [
                "CREATE UNIQUE INDEX idx_batch_date_region ON batch_controls (batch_date, region)",
                "CREATE INDEX idx_batch_status_time ON batch_controls (status, scheduled_time)"
            ]
        }
    ]

    for coll in collections:
        resp = requests.get(f"{pb_url}/api/collections/{coll['name']}", headers=headers)
        if resp.status_code == 200:
            print(f"Collection {coll['name']} already exists.")
        else:
            resp = requests.post(f"{pb_url}/api/collections", headers=headers, json=coll)
            if resp.status_code == 200:
                print(f"Collection {coll['name']} created.")
            else:
                print(f"Error creating {coll['name']}: {resp.text}")

if __name__ == "__main__":
    setup()
