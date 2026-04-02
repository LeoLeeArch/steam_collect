import os
from dotenv import load_dotenv

load_dotenv()
from src.pocketbase_client import PocketBaseClient

def reset_one():
    pb = PocketBaseClient()
    if pb.authenticate():
        resp = pb.session.get(f"{pb.url}/api/collections/batch_controls/records?filter=batch_date='2026-04-02'")
        items = resp.json().get("items", [])
        for item in items:
            print(f"Resetting {item['id']} ({item['region']}) to pending...")
            pb.update_batch(item['id'], {"status": "pending", "scheduled_time": "2026-04-01 00:00:00.000Z"})
            break
            
if __name__ == "__main__":
    reset_one()
