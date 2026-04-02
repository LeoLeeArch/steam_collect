"""Worker daemon that pulls batch jobs from PocketBase and runs them."""

import asyncio
import structlog
from datetime import datetime
import sys

from .pocketbase_client import PocketBaseClient
from .catalog import run_catalog_sync
from .collector import collect_prices
from .utils import format_date, get_path_manager, read_jsonl

logger = structlog.get_logger(__name__)

async def run_worker():
    pb = PocketBaseClient()
    if not pb.authenticate():
        logger.error("PocketBase Authentication failed. Worker cannot start.")
        sys.exit(1)

    logger.info("Worker started, waiting for jobs in batch_controls...")
    
    while True:
        try:
            batch = pb.get_next_pending_batch()
            if not batch:
                # No pending batches due yet
                await asyncio.sleep(60)
                continue

            batch_id = batch["id"]
            region = batch["region"]
            mode = batch.get("mode", "incremental")
            batch_date = batch.get("batch_date")
            
            logger.info("Claimed batch job", batch_id=batch_id, batch_date=batch_date, region=region, mode=mode)
            
            # Mark as running
            now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.000Z")
            pb.update_batch(batch_id, {"status": "running", "started_at": now_str})
            
            try:
                dt = format_date()
                path_manager = get_path_manager()
                catalog_path = path_manager.get_catalog_path(dt)
                
                changed_apps = []
                
                # 1. Sync Catalog
                # To prevent syncing full catalog multiple times a day (since each region has its own batch)
                # we do a simple file size check for full sync.
                is_catalog_sync_needed = True
                if mode == "full":
                    # Check if today's catalog exists and has enough size to be a real full catalog (180k+ apps ~ 100MB+)
                    if catalog_path.exists() and catalog_path.stat().st_size > 50_000_000:
                        logger.info("Full catalog for today already exists locally, skipping duplicate full catalog sync.")
                        is_catalog_sync_needed = False
                    else:
                        if catalog_path.exists():
                            logger.info(f"Existing catalog is too small ({catalog_path.stat().st_size} bytes), overwriting with full sync...")
                            catalog_path.unlink() # Delete incomplete catalog so it doesn't cause issues
                
                if is_catalog_sync_needed:
                    _, changed_apps = await run_catalog_sync(mode=mode)
                else:
                    changed_apps = [] # If skipped, we read appids directly below
                
                # 2. Get target appids
                appids = []
                if mode == "full":
                    if catalog_path.exists():
                        for app in read_jsonl(catalog_path):
                            appids.append(app["appid"])
                else:
                    if not is_catalog_sync_needed:
                        # If incremental was skipped (rare, but future proofing), we'd need to handle it.
                        pass
                    elif changed_apps:
                        appids = [app["appid"] for app in changed_apps]
                        
                # --- SORTING LOGIC FOR OPTIMIZATION ---
                # Prioritize: 1. Hot Apps (top 6000), 2. New Apps (higher AppID first)
                import os
                hot_apps = set()
                if os.path.exists("data/hot_apps.txt"):
                    with open("data/hot_apps.txt") as f:
                        for line in f:
                            if line.strip().isdigit():
                                hot_apps.add(int(line.strip()))
                
                priority_appids = []
                regular_appids = []
                for appid in appids:
                    if appid in hot_apps:
                        priority_appids.append(appid)
                    else:
                        regular_appids.append(appid)
                
                # Sort regular apps descending so newer games (larger appids) are processed first
                regular_appids.sort(reverse=True)
                appids = priority_appids + regular_appids
                # --------------------------------------
                
                # 3. Collect Prices
                if appids:
                        # In worker mode, we let the SQLite cache handle resumption automatically
                    force_refresh = False
                    logger.info("Starting price collection for batch", region=region, app_count=len(appids))
                    
                    # Log if it looks suspiciously small
                    if len(appids) < 10000 and mode == "full":
                        logger.warning(f"Batch mode is full but only {len(appids)} apps were found! Check if catalog sync failed or was interrupted.")
                    
                    await collect_prices(appids=appids, regions=[region], run_id=batch_id, force_refresh=force_refresh)
                else:
                    logger.info("No apps to collect for this batch")
                
                # Mark as completed
                now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.000Z")
                pb.update_batch(batch_id, {"status": "completed", "finished_at": now_str})
                logger.info("Batch completed successfully", batch_id=batch_id)
                
            except Exception as e:
                logger.error("Batch failed during execution", batch_id=batch_id, error=str(e))
                now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.000Z")
                pb.update_batch(batch_id, {"status": "failed", "finished_at": now_str, "error_log": str(e)})

        except Exception as e:
            logger.error("Worker generic error", error=str(e))
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_worker())
