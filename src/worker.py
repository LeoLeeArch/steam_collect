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
                if mode == "full":
                    if catalog_path.exists() and catalog_path.stat().st_size > 5_000_000:
                        logger.info("Full catalog for today already exists locally, skipping duplicate full catalog sync.")
                    else:
                        _, changed_apps = await run_catalog_sync(mode="full")
                else:
                    _, changed_apps = await run_catalog_sync(mode="incremental")
                
                # 2. Get target appids
                appids = []
                if mode == "full":
                    if catalog_path.exists():
                        for app in read_jsonl(catalog_path):
                            appids.append(app["appid"])
                else:
                    if changed_apps:
                        appids = [app["appid"] for app in changed_apps]
                
                # 3. Collect Prices
                if appids:
                    # In worker mode, if mode is full, we bypass cache daily skip (force_refresh=True)
                    force_refresh = (mode == "full")
                    logger.info("Starting price collection for batch", region=region, app_count=len(appids))
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
