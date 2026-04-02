"""Configuration management for Steam Price Collector."""

import os
from pathlib import Path
from typing import Dict, List

import yaml
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .models import Checkpoint

# Load environment variables
load_dotenv()


class CollectorConfig(BaseModel):
    """Main configuration model."""
    
    steam: Dict = Field(default_factory=dict)
    collector: Dict = Field(default_factory=dict)
    rate_limit: Dict = Field(default_factory=dict)
    paths: Dict = Field(default_factory=dict)
    logging: Dict = Field(default_factory=dict)
    checkpoint: Dict = Field(default_factory=dict)
    
    @property
    def steam_api_key(self) -> str:
        return os.getenv("STEAM_API_KEY", "")

    def get_api_keys(self) -> List[str]:
        """Dynamic loading of API keys from config/api_keys.txt. 
        Each key allows +1 parallelism. Updates next time the worker polls."""
        keys = []
        key_file = Path("config/api_keys.txt")
        if key_file.exists():
            with open(key_file, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        keys.append(stripped)
                        
        env_key = self.steam_api_key
        if env_key and env_key not in keys:
            keys.append(env_key)
            
        return keys if keys else [""]
    
    @classmethod
    def from_yaml(cls, config_path: str = "config/config.yaml") -> "CollectorConfig":
        """Load configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        
        return cls(**config_dict)
    
    @property
    def data_root(self) -> Path:
        return Path(self.paths.get("data_root", "data"))
    
    @property
    def catalog_dir(self) -> Path:
        return self.data_root / self.paths.get("catalog_dir", "data/catalog").split("/")[-1]
    
    @property
    def prices_dir(self) -> Path:
        return self.data_root / self.paths.get("prices_dir", "data/prices").split("/")[-1]
    
    @property
    def runs_dir(self) -> Path:
        return self.data_root / self.paths.get("runs_dir", "data/runs").split("/")[-1]
    
    @property
    def state_dir(self) -> Path:
        return self.data_root / self.paths.get("state_dir", "data/state").split("/")[-1]
    
    @property
    def regions(self) -> List[str]:
        return self.collector.get("regions", ["us", "cn", "gb", "jp", "de"])
    
    @property
    def max_workers(self) -> int:
        return self.rate_limit.get("max_workers", 3)
    
    @property
    def log_level(self) -> str:
        return self.logging.get("level", "INFO")


class PathManager:
    """Helper to generate dated and region-partitioned paths."""
    
    def __init__(self, config: CollectorConfig):
        self.config = config
    
    def get_catalog_path(self, dt: str) -> Path:
        """Return path for catalog: data/catalog/dt=YYYY-MM-DD/apps.jsonl"""
        dir_path = self.config.catalog_dir / f"dt={dt}"
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path / "apps.jsonl"
    
    def get_price_path(self, dt: str, country_code: str) -> Path:
        """Return path for prices: data/prices/dt=YYYY-MM-DD/cc=xx.jsonl"""
        dir_path = self.config.prices_dir / f"dt={dt}"
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path / f"cc={country_code}.jsonl"
    
    def get_run_path(self, run_id: str) -> Path:
        """Return path for run metadata."""
        self.config.runs_dir.mkdir(parents=True, exist_ok=True)
        return self.config.runs_dir / f"crawl_run_{run_id}.json"
    
    def get_checkpoint_path(self) -> Path:
        """Return checkpoint file path."""
        self.config.state_dir.mkdir(parents=True, exist_ok=True)
        return self.config.state_dir / "checkpoint.json"
    
    def get_last_modified_path(self) -> Path:
        """Return last_if_modified_since file path."""
        self.config.state_dir.mkdir(parents=True, exist_ok=True)
        return self.config.state_dir / "last_if_modified_since.json"


# Global config instance
_config: CollectorConfig | None = None


def get_config() -> CollectorConfig:
    """Get singleton config instance."""
    global _config
    if _config is None:
        _config = CollectorConfig.from_yaml()
    return _config


def get_path_manager() -> PathManager:
    """Get path manager instance."""
    return PathManager(get_config())
