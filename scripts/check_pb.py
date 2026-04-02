import os
from dotenv import load_dotenv

load_dotenv()
from src.pocketbase_client import PocketBaseClient

def check():
    client = PocketBaseClient()
    if client.authenticate():
        print("Auth success")
        resp = client.session.get(f"{client.url}/api/collections/price_snapshots/records?perPage=1")
        print("Price snapshots:", resp.json())
        
        resp2 = client.session.get(f"{client.url}/api/collections/steam_catalog/records?perPage=1")
        print("Catalog records:", resp2.json())
    else:
        print("Auth failed")

if __name__ == "__main__":
    check()
