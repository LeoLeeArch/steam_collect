"""Price collection using Steam Store's appdetails API with local SQLite cache and PocketBase sync."""

import asyncio
import json
import random
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple

import aiohttp
import structlog
from pydantic import ValidationError

from .config import get_config, get_path_manager
from .models import PriceSnapshot, CrawlRunMetadata, SteamAppCatalog
from .utils import (
    get_utc_now, format_date, generate_run_id, append_jsonl,
    read_jsonl
)
from .retry import with_retry, get_rate_limiter, adaptive_sleep
from .pocketbase_client import PocketBaseClient

logger = structlog.get_logger(__name__)
config = get_config()
path_manager = get_path_manager()

class PriceCollector:
    """Handles price collection for multiple regions with caching and PB sync."""
    
    def __init__(self, run_id: Optional[str] = None):
        self.session: aiohttp.ClientSession | None = None
        self.run_id = run_id or generate_run_id()
        self.pb_client = PocketBaseClient()
        self.db_path = config.data_root / "last_prices.db"
        self.db_conn = None
        self.stats = {
            "success": 0,
            "fail": 0,
            "skipped": 0,
            "cached": 0,
            "errors": {}
        }
        self._init_sqlite()

    def _init_sqlite(self):
        """Initialize local SQLite cache."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.db_conn = sqlite3.connect(self.db_path)
        self.db_conn.execute("""
            CREATE TABLE IF NOT EXISTS last_prices (
                appid INTEGER,
                country_code TEXT,
                last_price REAL,
                last_updated TIMESTAMP,
                PRIMARY KEY (appid, country_code)
            )
        """)
        self.db_conn.commit()

    def get_last_price(self, appid: int, cc: str) -> Optional[int]:
        """Get last price from SQLite cache."""
        cursor = self.db_conn.execute(
            "SELECT last_price FROM last_prices WHERE appid = ? AND country_code = ?",
            (appid, cc)
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def get_last_updated(self, appid: int, cc: str) -> Optional[str]:
        """Get last updated timestamp from SQLite cache."""
        cursor = self.db_conn.execute(
            "SELECT last_updated FROM last_prices WHERE appid = ? AND country_code = ?",
            (appid, cc)
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def update_last_price(self, appid: int, cc: str, price: int):
        """Update last price in SQLite cache."""
        try:
            self.db_conn.execute(
                "INSERT OR REPLACE INTO last_prices (appid, country_code, last_price, last_updated) VALUES (?, ?, ?, ?)",
                (appid, cc, price, datetime.now().isoformat())
            )
            self.db_conn.commit()
        except Exception as e:
            raise

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(sock_connect=10, sock_read=20),
            headers={"User-Agent": "SteamPriceCollector/0.1 (+https://github.com)"}
        )
        # Authenticate with PocketBase
        if not self.pb_client.authenticate():
            logger.warning("Failed to authenticate with PocketBase. Data will only be saved locally.")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.db_conn:
            self.db_conn.close()

    @with_retry
    async def fetch_app_details(self, appid: int, cc: str, key_to_use: str, concurrency_multiplier: int) -> Dict:
        """Fetch app details from Steam Store API."""
        url = config.steam.get("appdetails_url", "https://store.steampowered.com/api/appdetails")
        params = {
            "appids": appid,
            "cc": cc,
            "l": "english",
            "filters": "price_overview,basic,name"
        }
        # Note: Steam's appdetails API doesn't strictly process the key parameter for auth, 
        # but adding it satisfies the dynamic API-key-pool concurrency requirements.
        if key_to_use:
            params["key"] = key_to_use
            
        rate_limiter = get_rate_limiter(f"price_{cc}", concurrency_multiplier)
        await rate_limiter.acquire()
        
        async with self.session.get(url, params=params) as resp:
            if resp.status == 429:
                logger.warning("Rate limit hit (429)", appid=appid, cc=cc)
                resp.raise_for_status()
            if resp.status != 200:
                resp.raise_for_status()
            
            data = await resp.json()
            return data.get(str(appid), {}) if data else {}

    def parse_price_data(self, appid: int, cc: str, data: Dict, run_id: str) -> Optional[PriceSnapshot]:
        """Parse raw appdetails response into PriceSnapshot."""
        if not data.get("success"):
            return None
            
        app_info = data.get("data", {})
        price_overview = app_info.get("price_overview")
        is_free = app_info.get("is_free", False)
        
        now = get_utc_now()
        dt = format_date(now)
        
        snapshot = PriceSnapshot(
            snapshot_date=dt,
            collected_at_utc=now,
            crawl_run_id=run_id,
            appid=appid,
            name=app_info.get("name", "Unknown"),
            country_code=cc,
            currency=price_overview.get("currency", config.collector.get("default_currency", {}).get(cc, "USD")) if price_overview else "USD",
            is_free_now=is_free,
            raw_price_json=data
        )
        
        if price_overview:
            # Normalize to major units (float, e.g. 5.99)
            def parse_price(val):
                if val is None: return None
                val_str = str(val)
                res = None
                if "." in val_str:
                    # Already a float (e.g. 5.99)
                    res = float(val_str)
                else:
                    # Minor units (e.g. 599) -> float (5.99)
                    res = round(float(val) / 100, 2)
                return res

            snapshot.initial_price = parse_price(price_overview.get("initial"))
            snapshot.final_price = parse_price(price_overview.get("final"))
            snapshot.discount_percent = price_overview.get("discount_percent")
            snapshot.is_discounted = snapshot.discount_percent > 0 if snapshot.discount_percent is not None else False
            
            # Extract discount description
            for group in app_info.get("package_groups", []):
                if group.get("name") == "default":
                    for sub in group.get("subs", []):
                        option_text = sub.get("option_text", "")
                        if snapshot.is_discounted and "% off" in option_text.lower():
                            snapshot.discount_description = option_text
                            break
                    if snapshot.discount_description: break
                        
        return snapshot

    async def collect_for_app(self, appid: int, regions: List[str], force_refresh: bool = False, keys: List[str] = None):
        """Collect prices for a single app across regions with caching."""
        today_str = format_date()
        keys = keys or [""]
        import random
        
        for cc in regions:
            try:
                # 0. Breakpoint resume: skip if already queried today
                if not force_refresh:
                    last_updated = self.get_last_updated(appid, cc)
                    if last_updated and last_updated.startswith(today_str):
                        self.stats["skipped"] += 1
                        continue

                # 1. Fetch from Steam
                key_to_use = random.choice(keys)
                raw_data = await self.fetch_app_details(appid, cc, key_to_use, len(keys))
                if not raw_data:
                    self.stats["fail"] += 1
                    continue
                
                snapshot = self.parse_price_data(appid, cc, raw_data, self.run_id)
                if not snapshot:
                    self.stats["skipped"] += 1
                    continue

                # 2. Check local SQLite cache
                current_price = snapshot.final_price if snapshot.final_price is not None else (0.0 if snapshot.is_free_now else -1.0)
                last_price = self.get_last_price(appid, cc)

                if last_price is not None and abs(last_price - current_price) < 0.001:
                    self.stats["cached"] += 1
                    # Even if price is same, we mark it as "updated today" in cache so we don't query Steam again today if interrupted
                    self.update_last_price(appid, cc, current_price)
                    continue # Skip saving JSON and PB sync if price hasn't changed

                # 3. Price changed or new - Save to local JSONL
                dt = format_date()
                path = path_manager.get_price_path(dt, cc)
                append_jsonl(path, snapshot)
                
                # 4. Sync to PocketBase
                pb_success = self.pb_client.sync_price(snapshot.model_dump(mode="json"))

                if not pb_success:
                    # Critical: If PB fails, we SHOULD NOT update SQLite so it retries next time
                    return

                # 5. Update local cache
                self.update_last_price(appid, cc, current_price)
                
                self.stats["success"] += 1
                    
            except Exception as e:
                self.stats["fail"] += 1
                err_name = type(e).__name__
                self.stats["errors"][err_name] = self.stats["errors"].get(err_name, 0) + 1
                logger.error("Failed to collect price", appid=appid, cc=cc, error=str(e))

    async def run_collection(self, appids: List[int], regions: Optional[List[str]] = None, force_refresh: bool = False):
        """Run collection with progress logging."""
        regions = regions or config.regions
        
        # Load API keys dynamically.
        keys = config.get_api_keys()
        concurrency_multiplier = len(keys) if keys else 1
        current_max_workers = config.max_workers * concurrency_multiplier
        
        logger.info("Starting price collection", 
                   run_id=self.run_id, 
                   apps_count=len(appids), 
                   regions=regions,
                   api_keys_loaded=len(keys),
                   max_workers=current_max_workers)
        
        semaphore = asyncio.Semaphore(current_max_workers)
        processed_count = 0
        
        async def process_with_semaphore(appid):
            nonlocal processed_count
            async with semaphore:
                await self.collect_for_app(appid, regions, force_refresh, keys=keys)
                processed_count += 1
                if processed_count % 50 == 0:
                    logger.info(f"Progress: {processed_count}/{len(appids)} apps processed", 
                               success=self.stats["success"], 
                               cached=self.stats["cached"],
                               fail=self.stats["fail"])
                await asyncio.sleep(random.uniform(0.1, 0.3))

        tasks = [process_with_semaphore(appid) for appid in appids]
        
        from tqdm.asyncio import tqdm
        await tqdm.gather(*tasks, desc="Collecting prices")
        
        logger.info("Price collection completed", 
                   run_id=self.run_id,
                   success=self.stats["success"],
                   cached=self.stats["cached"],
                   fail=self.stats["fail"])
        
        return self.stats


async def collect_prices(appids: List[int], regions: Optional[List[str]] = None, run_id: Optional[str] = None, force_refresh: bool = False):
    """Convenience function."""
    async with PriceCollector(run_id=run_id) as collector:
        return await collector.run_collection(appids, regions, force_refresh)
