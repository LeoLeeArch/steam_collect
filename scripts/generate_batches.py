import os
import sys
import asyncio
import aiohttp
from datetime import datetime, timedelta
from dotenv import load_dotenv
from tqdm.asyncio import tqdm

load_dotenv()

pb_url = os.getenv("POCKETBASE_URL")
if pb_url and pb_url.endswith('/'): pb_url = pb_url[:-1]
pb_email = os.getenv("POCKETBASE_EMAIL")
pb_password = os.getenv("POCKETBASE_PASSWORD")

async def main():
    async with aiohttp.ClientSession() as session:
        # Auth
        resp = await session.post(f"{pb_url}/api/admins/auth-with-password", json={
            "identity": pb_email, "password": pb_password
        })
        if resp.status != 200:
            print("Failed to authenticate to PocketBase.")
            return
            
        token = (await resp.json())["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check existing
        resp = await session.get(f"{pb_url}/api/collections/batch_controls/records?perPage=1", headers=headers)
        data = await resp.json()
        if data.get("totalItems", 0) > 0:
            if "--force" not in sys.argv:
                print("Batch records already exist. Use --force to add more anyway.")
                return

        print("Generating 5 years of batch dates (14,600 records)...")
        start_date = datetime.utcnow().date()
        regions = ["cn", "us", "gb", "jp", "de", "vn", "id", "in"]
        
        tasks = []
        sem = asyncio.Semaphore(50)
        
        async def create_record(date_str, region, mode, sched_time):
            async with sem:
                payload = {
                    "batch_date": date_str,
                    "region": region,
                    "mode": mode,
                    "status": "pending",
                    "scheduled_time": sched_time
                }
                # use try/except block to ignore duplicate entries
                try:
                    resp = await session.post(f"{pb_url}/api/collections/batch_controls/records", json=payload, headers=headers)
                except:
                    pass

        # Calculate time offsets for staggered region starts
        # For simplicity, they can just start at specific UTC times on that day
        region_offsets = {
            "cn": 0, "us": 1, "gb": 2, "jp": 3, "de": 4, "vn": 5, "id": 6, "in": 7
        }
        
        for i in range(1825):
            curr_date = start_date + timedelta(days=i)
            date_str = curr_date.strftime("%Y-%m-%d")
            
            for r in regions:
                mode = "full" if i == 0 else "incremental"
                # Schedule at 01:00 UTC + region offset
                hour = 1 + region_offsets[r]
                sched_time = f"{date_str} {hour:02d}:00:00.000Z"
                
                tasks.append(create_record(date_str, r, mode, sched_time))
                
        # Batch insert using tqdm
        chunk_size = 1000
        for i in range(0, len(tasks), chunk_size):
            print(f"Uploading chunk {i//chunk_size + 1}/{len(tasks)//chunk_size + 1}")
            await asyncio.gather(*tasks[i:i+chunk_size])

if __name__ == "__main__":
    asyncio.run(main())
