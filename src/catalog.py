"""Catalog synchronization using official IStoreService/GetAppList API."""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Set, Tuple

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
from .pocketbase_client import PocketBaseClient

logger = structlog.get_logger(__name__)
config = get_config()
path_manager = get_path_manager()


class CatalogSync:
    """Handles Steam catalog synchronization with optional PocketBase sync."""
    
    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
        self.run_id = generate_run_id()
        self.pb_client = PocketBaseClient()
        self.changed_apps: List[Dict] = []
        self.scanned_count = 0
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "SteamPriceCollector/0.1 (+https://github.com)"}
        )
        if not self.pb_client.authenticate():
            logger.warning("PocketBase authentication failed in CatalogSync")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @with_retry
    async def fetch_app_list_page(self, last_appid: int = 0, if_modified_since: int = 0, max_results: int = 1000) -> Dict:
        url = f"{config.steam.get('base_url', 'https://api.steampowered.com')}/IStoreService/GetAppList/v1/"
        keys = config.get_api_keys()
        import random
        key_to_use = random.choice(keys) if keys else ""
        
        params = {"key": key_to_use, "last_appid": last_appid, "max_results": max_results}
        if if_modified_since > 0: params["if_modified_since"] = if_modified_since
        
        await get_rate_limiter("catalog", len(keys)).acquire()
        async with self.session.get(url, params=params) as resp:
            if resp.status != 200: resp.raise_for_status()
            data = await resp.json()
            return data.get("response", {})
    
    def process_app(self, app_data: Dict, is_full_sync: bool = False) -> SteamAppCatalog:
        appid = app_data.get("appid")
        now = get_utc_now()
        catalog_entry = SteamAppCatalog(
            appid=appid,
            name=app_data.get("name", "Unknown"),
            type=app_data.get("type"),
            is_free=app_data.get("is_free"),
            coming_soon=app_data.get("coming_soon"),
            release_date=app_data.get("release_date"),
            steam_last_modified=app_data.get("last_modified"),
            steam_price_change_number=app_data.get("price_change_number"),
            first_seen_at=now, last_seen_at=now,
            raw_basic_json=app_data,
        )
        catalog_entry.store_url = f"https://store.steampowered.com/app/{appid}"
        if "header" in app_data: catalog_entry.header_image = app_data.get("header")
        return catalog_entry
    
    async def sync_catalog(self, mode: str = "incremental", max_pages: int = 0) -> Tuple[CrawlRunMetadata, List[Dict]]:
        logger.info(f"Starting catalog sync", mode=mode, run_id=self.run_id)
        is_full = mode == "full"
        last_appid = 0
        if_modified_since = 0 if is_full else load_last_if_modified_since()
        processed_appids: Set[int] = set()
        page_count = 0
        has_more = True
        
        metadata = CrawlRunMetadata(crawl_run_id=self.run_id, started_at=get_utc_now(), mode=mode, target_regions=config.regions)
        
        while has_more and (max_pages == 0 or page_count < max_pages):
            page_count += 1
            try:
                response = await self.fetch_app_list_page(last_appid=last_appid, if_modified_since=if_modified_since)
                apps = response.get("apps", [])
                if not apps: break
                
                for app in apps:
                    appid = app.get("appid")
                    if appid in processed_appids: continue
                    processed_appids.add(appid)
                    self.scanned_count += 1
                    
                    try:
                        catalog_entry = self.process_app(app, is_full_sync=is_full)
                        append_jsonl(path_manager.get_catalog_path(format_date()), catalog_entry)
                        
                        if app.get("last_modified") or app.get("price_change_number"):
                            self.changed_apps.append({"appid": appid, "name": catalog_entry.name})
                    except Exception as e:
                        logger.error("Failed to process app", appid=appid, error=str(e))
                
                last_appid = response.get("last_appid", 0)
                has_more = response.get("have_more_results", False) or len(apps) >= 900
                if self.scanned_count % config.checkpoint.get("save_interval", 500) == 0:
                    self._save_progress(last_appid, if_modified_since)
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.error("Failed to fetch catalog page", page=page_count, error=str(e))
                break
        
        if not is_full and self.changed_apps:
            save_last_if_modified_since(int(datetime.now().timestamp()))
        
        metadata.finished_at = get_utc_now()
        metadata.apps_scanned = self.scanned_count
        metadata.apps_changed = len(self.changed_apps)
        self._save_progress(last_appid, if_modified_since)
        
        return metadata, self.changed_apps
    
    def _save_progress(self, last_appid: int, if_modified_since: int):
        checkpoint = {
            "last_run_id": self.run_id, "last_catalog_sync": get_utc_now().isoformat(),
            "last_appid": last_appid, "last_if_modified_since": if_modified_since,
            "total_apps_known": self.scanned_count,
        }
        save_checkpoint(checkpoint)


async def run_catalog_sync(mode: str = "incremental", max_pages: int = 0):
    async with CatalogSync() as sync:
        return await sync.sync_catalog(mode=mode, max_pages=max_pages)
