"""Catalog synchronization using official IStoreService/GetAppList API.

Implements full + incremental sync with checkpointing and state management.
Strictly follows Steam's recommended incremental pattern using:
- last_appid
- if_modified_since
- last_modified
- price_change_number
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Set

import aiohttp
import structlog
from aiohttp import ClientConnectorError

from .config import get_config, get_path_manager
from .models import SteamAppCatalog, CrawlRunMetadata, Checkpoint
from .utils import (
    get_utc_now, format_date, generate_run_id, append_jsonl,
    load_checkpoint, save_checkpoint, load_last_if_modified_since,
    save_last_if_modified_since
)
from .retry import with_retry, get_rate_limiter

logger = structlog.get_logger(__name__)
config = get_config()
path_manager = get_path_manager()


class CatalogSync:
    """Handles Steam catalog synchronization in full and incremental modes."""
    
    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
        self.run_id = generate_run_id()
        self.changed_apps: List[Dict] = []
        self.scanned_count = 0
        self.new_apps = 0
        self.updated_apps = 0
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "SteamPriceCollector/0.1 (+https://github.com)"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @with_retry
    async def fetch_app_list_page(
        self, 
        last_appid: int = 0, 
        if_modified_since: int = 0,
        max_results: int = 1000
    ) -> Dict:
        """Fetch one page from IStoreService/GetAppList."""
        
        url = f"{config.steam.get('base_url', 'https://api.steampowered.com')}/IStoreService/GetAppList/v1/"
        
        params = {
            "key": "",  # Public endpoint, no key needed
            "last_appid": last_appid,
            "max_results": max_results,
        }
        
        if if_modified_since > 0:
            params["if_modified_since"] = if_modified_since
        
        rate_limiter = get_rate_limiter("catalog")
        await rate_limiter.acquire()
        
        async with self.session.get(url, params=params) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error("Catalog API error", status=resp.status, response=text[:200])
                resp.raise_for_status()
            
            data = await resp.json()
            return data.get("response", {})
    
    def process_app(self, app_data: Dict, is_full_sync: bool = False) -> SteamAppCatalog:
        """Process raw app data into our model."""
        appid = app_data.get("appid")
        name = app_data.get("name", "Unknown")
        
        now = get_utc_now()
        
        catalog_entry = SteamAppCatalog(
            appid=appid,
            name=name,
            type=app_data.get("type"),
            is_free=app_data.get("is_free"),
            coming_soon=app_data.get("coming_soon"),
            release_date=app_data.get("release_date"),
            steam_last_modified=app_data.get("last_modified"),
            steam_price_change_number=app_data.get("price_change_number"),
            first_seen_at=now if is_full_sync else now,  # Will be updated properly in full sync
            last_seen_at=now,
            raw_basic_json=app_data,
        )
        
        # Generate store URL and header image
        catalog_entry.store_url = f"https://store.steampowered.com/app/{appid}"
        if "header" in app_data:
            catalog_entry.header_image = app_data.get("header")
        
        return catalog_entry
    
    async def sync_catalog(self, mode: str = "incremental", max_pages: int = 0) -> CrawlRunMetadata:
        """Main catalog sync method."""
        logger.info(f"Starting catalog sync in {mode} mode", run_id=self.run_id)
        
        is_full = mode == "full"
        last_appid = 0
        if_modified_since = 0 if is_full else load_last_if_modified_since()
        
        processed_appids: Set[int] = set()
        page_count = 0
        has_more = True
        
        metadata = CrawlRunMetadata(
            crawl_run_id=self.run_id,
            started_at=get_utc_now(),
            mode=mode,
            target_regions=config.regions,
        )
        
        while has_more and (max_pages == 0 or page_count < max_pages):
            page_count += 1
            logger.info(f"Fetching catalog page {page_count}", last_appid=last_appid)
            
            try:
                response = await self.fetch_app_list_page(
                    last_appid=last_appid,
                    if_modified_since=if_modified_since
                )
                
                apps = response.get("apps", [])
                if not apps:
                    break
                
                for app in apps:
                    appid = app.get("appid")
                    if appid in processed_appids:
                        continue
                    
                    processed_appids.add(appid)
                    self.scanned_count += 1
                    
                    try:
                        catalog_entry = self.process_app(app, is_full_sync=is_full)
                        dt = format_date()
                        
                        # Write to dated catalog file
                        catalog_path = path_manager.get_catalog_path(dt)
                        append_jsonl(catalog_path, catalog_entry)
                        
                        # Track changed/new apps for price collection
                        if app.get("last_modified") or app.get("price_change_number"):
                            self.changed_apps.append({
                                "appid": appid,
                                "name": catalog_entry.name,
                                "last_modified": app.get("last_modified"),
                                "price_change_number": app.get("price_change_number")
                            })
                        
                        if is_full:
                            self.new_apps += 1
                        else:
                            self.updated_apps += 1
                            
                    except Exception as e:
                        logger.error("Failed to process app", appid=appid, error=str(e))
                
                # Update pagination
                last_appid = response.get("last_appid", 0)
                has_more = response.get("have_more_results", False) or len(apps) >= 900
                
                # Save checkpoint periodically
                if self.scanned_count % config.checkpoint.get("save_interval", 500) == 0:
                    self._save_progress(last_appid, if_modified_since)
                
                await asyncio.sleep(0.3)  # Conservative delay between pages
                
            except Exception as e:
                logger.error("Failed to fetch catalog page", page=page_count, error=str(e))
                break
        
        # Finalize
        if not is_full and self.changed_apps:
            save_last_if_modified_since(int(datetime.now().timestamp()))
        
        metadata.finished_at = get_utc_now()
        metadata.apps_scanned = self.scanned_count
        metadata.apps_changed = len(self.changed_apps)
        
        self._save_run_metadata(metadata)
        self._save_progress(last_appid, if_modified_since)
        
        logger.info("Catalog sync completed", 
                   mode=mode,
                   apps_scanned=self.scanned_count,
                   apps_changed=len(self.changed_apps),
                   pages=page_count)
        
        return metadata
    
    def _save_progress(self, last_appid: int, if_modified_since: int):
        """Save current progress to checkpoint."""
        checkpoint = {
            "last_run_id": self.run_id,
            "last_catalog_sync": get_utc_now().isoformat(),
            "last_appid": last_appid,
            "last_if_modified_since": if_modified_since,
            "total_apps_known": self.scanned_count,
        }
        save_checkpoint(checkpoint)
    
    def _save_run_metadata(self, metadata: CrawlRunMetadata):
        """Save run metadata."""
        path = path_manager.get_run_path(self.run_id)
        append_jsonl(path, metadata)  # Using append for consistency, though it's one record


async def run_catalog_sync(mode: str = "incremental"):
    """Convenience function to run catalog sync."""
    async with CatalogSync() as sync:
        return await sync.sync_catalog(mode=mode)
