"""Utility functions for Steam Price Collector."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, TypeVar

from .config import get_config, get_path_manager
from .models import SteamAppCatalog, PriceSnapshot, CrawlRunMetadata, BaseModel

T = TypeVar("T")


def get_utc_now() -> datetime:
    """Return current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


def format_date(dt: datetime | None = None) -> str:
    """Format date as YYYY-MM-DD."""
    if dt is None:
        dt = get_utc_now()
    return dt.strftime("%Y-%m-%d")


def generate_run_id() -> str:
    """Generate unique crawl run ID."""
    now = get_utc_now()
    return now.strftime("%Y%m%d_%H%M%S")


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists and return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def append_jsonl(path: Path, data: Dict[str, Any] | BaseModel) -> None:
    """Append a single record to a JSONL file."""
    ensure_dir(path.parent)
    
    if isinstance(data, BaseModel):
        record = data.model_dump(mode="json")
    else:
        record = data
    
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: Path, model_class: type[T] | None = None) -> Iterator[T | Dict]:
    """Read JSONL file and optionally parse into Pydantic models."""
    if not path.exists():
        return
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                data = json.loads(line)
                if model_class:
                    yield model_class.model_validate(data)
                else:
                    yield data
            except (json.JSONDecodeError, Exception) as e:
                logging.warning(f"Failed to parse line in {path}: {e}")


def load_checkpoint() -> Dict:
    """Load checkpoint from disk."""
    path = get_path_manager().get_checkpoint_path()
    if not path.exists():
        return {}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_checkpoint(data: Dict) -> None:
    """Save checkpoint to disk."""
    path = get_path_manager().get_checkpoint_path()
    ensure_dir(path.parent)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def load_last_if_modified_since() -> int:
    """Load last successful if_modified_since timestamp."""
    path = get_path_manager().get_last_modified_path()
    if not path.exists():
        return 0
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("last_if_modified_since", 0)
    except Exception:
        return 0


def save_last_if_modified_since(timestamp: int) -> None:
    """Save last successful if_modified_since timestamp."""
    path = get_path_manager().get_last_modified_path()
    ensure_dir(path.parent)
    
    data = {"last_if_modified_since": timestamp, "updated_at": get_utc_now().isoformat()}
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
