"""PocketBase client for Steam Price Collector."""

import os
import requests
import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = structlog.get_logger(__name__)

class PocketBaseClient:
    def __init__(self, url: str = None, email: str = None, password: str = None):
        self.url = url or os.getenv("POCKETBASE_URL")
        if self.url and self.url.endswith('/'):
            self.url = self.url[:-1]
            
        self.email = email or os.getenv("POCKETBASE_EMAIL")
        self.password = password or os.getenv("POCKETBASE_PASSWORD")
        self.token = None
        self.session = requests.Session()
        
        # Performance tuning for high throughput
        adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=3)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def authenticate(self) -> bool:
        """Authenticate with PocketBase."""
        try:
            auth_paths = ["/api/admins/auth-with-password", "/api/collections/_superusers/auth-with-password"]
            for path in auth_paths:
                resp = self.session.post(f"{self.url}{path}", json={
                    "identity": self.email,
                    "password": self.password
                }, timeout=10)
                if resp.status_code == 200:
                    self.token = resp.json().get("token")
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    return True
            return False
        except Exception as e:
            logger.error("PocketBase authentication failed", error=str(e))
            return False

    def sync_catalog(self, catalog_data: Dict[str, Any]) -> bool:
        """Upsert a catalog record."""
        appid = catalog_data.get("appid")
        try:
            # Check if exists first
            resp = self.session.get(f"{self.url}/api/collections/steam_catalog/records", params={
                "filter": f"appid={appid}"
            }, timeout=10)
            if resp.status_code == 200 and resp.json().get("totalItems", 0) > 0:
                record_id = resp.json().get("items")[0]["id"]
                resp = self.session.patch(f"{self.url}/api/collections/steam_catalog/records/{record_id}", json=catalog_data, timeout=10)
            else:
                resp = self.session.post(f"{self.url}/api/collections/steam_catalog/records", json=catalog_data, timeout=10)
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error("Failed to sync catalog to PocketBase", appid=appid, error=str(e))
            return False

    def sync_price(self, price_data: Dict[str, Any]) -> bool:
        """Sync a price record."""
        try:
            # PB doesn't support easy batching of upserts, so we just post.
            # Usually we don't care about duplicates in PB since it's a log.
            resp = self.session.post(f"{self.url}/api/collections/price_snapshots/records", json=price_data, timeout=10)
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error("Failed to sync price to PocketBase", appid=price_data.get("appid"), error=str(e))
            return False
    
    def sync_batch_prices(self, batch: List[Dict[str, Any]]) -> int:
        """Sync a batch of prices to PocketBase."""
        success_count = 0
        for item in batch:
            if self.sync_price(item):
                success_count += 1
        return success_count

    def get_next_pending_batch(self) -> Optional[Dict]:
        """Get the next pending batch control record that is due to run."""
        try:
            # PB date format: YYYY-MM-DD HH:MM:SS.000Z
            now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.000Z")
            filter_str = f"status='pending' && scheduled_time <= '{now_str}'"
            resp = self.session.get(f"{self.url}/api/collections/batch_controls/records", params={
                "filter": filter_str,
                "sort": "+scheduled_time",
                "perPage": 1
            }, timeout=10)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    return items[0]
            return None
        except Exception as e:
            logger.error("Failed to fetch pending batch", error=str(e))
            return None

    def update_batch(self, batch_id: str, data: Dict) -> bool:
        """Update a batch control record status/times."""
        try:
            resp = self.session.patch(f"{self.url}/api/collections/batch_controls/records/{batch_id}", json=data, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error("Failed to update batch", batch_id=batch_id, error=str(e))
            return False
