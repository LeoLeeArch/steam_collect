"""Data models for Steam Price Collector.

All models follow the exact field requirements specified in the project spec.
Uses Pydantic v2 for validation and type safety.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class SteamAppCatalog(BaseModel):
    """Steam application catalog entry from IStoreService/GetAppList."""
    
    appid: int = Field(..., description="Steam App ID")
    name: str = Field(..., description="Game/Application name")
    type: Optional[str] = Field(None, description="Type: game, application, music, etc.")
    is_free: Optional[bool] = Field(None, description="Whether the app is free")
    coming_soon: Optional[bool] = Field(None, description="Whether it's coming soon")
    release_date: Optional[str] = Field(None, description="Release date string")
    
    developers: Optional[List[str]] = Field(default_factory=list)
    publishers: Optional[List[str]] = Field(default_factory=list)
    categories: Optional[List[str]] = Field(default_factory=list)
    genres: Optional[List[str]] = Field(default_factory=list)
    
    header_image: Optional[str] = Field(None, description="Header image URL")
    store_url: Optional[str] = Field(None, description="Store page URL")
    
    # Steam internal tracking fields
    steam_last_modified: Optional[int] = Field(None, description="Steam last modified timestamp")
    steam_price_change_number: Optional[int] = Field(None, description="Price change number for incremental detection")
    
    # Our tracking fields
    first_seen_at: datetime = Field(..., description="First time we saw this app")
    last_seen_at: datetime = Field(..., description="Last time we saw this app")
    
    # Raw data for future schema evolution
    raw_basic_json: Dict[str, Any] = Field(default_factory=dict, description="Raw JSON from catalog API")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PriceSnapshot(BaseModel):
    """Price snapshot for a specific app in a specific country."""
    
    snapshot_date: str = Field(..., description="Date of the snapshot (YYYY-MM-DD)")
    collected_at_utc: datetime = Field(..., description="When this data was collected (UTC)")
    crawl_run_id: str = Field(..., description="Unique ID of this crawl run")
    
    appid: int = Field(..., description="Steam App ID")
    name: str = Field(..., description="App name at time of collection")
    
    country_code: str = Field(..., description="Country code (us, cn, gb, jp, de)")
    currency: str = Field(..., description="Currency code (USD, CNY, GBP, JPY, EUR)")
    
    # Prices in major units (USD, CNY, etc. e.g., 5.99)
    initial_price: Optional[float] = Field(None, description="Original price (e.g., 5.99)")
    final_price: Optional[float] = Field(None, description="Final/discounted price (e.g., 5.99)")
    discount_percent: Optional[int] = Field(None, description="Discount percentage")
    
    is_discounted: bool = Field(False, description="Whether there is a discount")
    is_free_now: bool = Field(False, description="Whether it's currently free")
    
    discount_description: Optional[str] = Field(None, description="Promotion description or sale name if available")
    
    package_id: Optional[int] = Field(None, description="Associated package ID if any")
    
    # Steam tracking
    steam_last_modified: Optional[int] = Field(None)
    steam_price_change_number: Optional[int] = Field(None)
    
    price_source: str = Field("appdetails", description="Source of the price data")
    
    # Raw data for replay and future fields
    raw_price_json: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CrawlRunMetadata(BaseModel):
    """Metadata for a single crawl run."""
    
    crawl_run_id: str = Field(..., description="Unique run identifier")
    started_at: datetime = Field(..., description="When the run started")
    finished_at: Optional[datetime] = Field(None, description="When the run finished")
    
    mode: str = Field(..., description="full or incremental")
    target_regions: List[str] = Field(default_factory=list)
    
    apps_scanned: int = Field(0, description="Number of apps processed in catalog")
    apps_changed: int = Field(0, description="Number of apps that changed")
    appdetails_requests: int = Field(0, description="Number of appdetails API calls")
    
    success_count: int = Field(0)
    fail_count: int = Field(0)
    skipped_count: int = Field(0)
    
    error_summary: Dict[str, int] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Checkpoint(BaseModel):
    """Persistent checkpoint for resuming operations."""
    
    last_run_id: Optional[str] = None
    last_catalog_sync: Optional[datetime] = None
    last_if_modified_since: Optional[int] = Field(0, description="Unix timestamp for incremental sync")
    last_appid: int = Field(0, description="Last appid from previous pagination")
    
    last_successful_run: Optional[datetime] = None
    total_apps_known: int = Field(0)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
