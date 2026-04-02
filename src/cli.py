#!/usr/bin/env python3
"""Command Line Interface for Steam Price Collector."""

import argparse
import sys
from datetime import datetime

from .config import get_config, get_path_manager
from .log_config import setup_logging
from .utils import (
    generate_run_id, get_utc_now, format_date, read_jsonl
)
from .catalog import run_catalog_sync
from .collector import collect_prices
from .models import SteamAppCatalog


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Steam Multi-Region Price Collector"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Full catalog sync
    full_parser = subparsers.add_parser(
        "full-sync-catalog", 
        help="Perform full catalog sync (first time only)"
    )
    
    # Incremental catalog sync
    inc_parser = subparsers.add_parser(
        "incremental-sync-catalog", 
        help="Perform incremental catalog sync"
    )
    
    # Price collection
    price_parser = subparsers.add_parser(
        "collect-prices", 
        help="Collect prices for changed apps"
    )
    price_parser.add_argument(
        "--regions", 
        nargs="+", 
        default=None,
        help="Regions to collect prices for (default: all)"
    )
    price_parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit the number of apps to collect prices for (0 for no limit)"
    )
    
    # Nightly job
    nightly_parser = subparsers.add_parser(
        "nightly-job", 
        help="Run full nightly job (incremental catalog + prices)"
    )
    nightly_parser.add_argument(
        "--regions", 
        nargs="+", 
        default=None,
        help="Regions to collect prices for"
    )
    nightly_parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit the number of apps to collect prices for (0 for no limit)"
    )
    nightly_parser.add_argument(
        "--full",
        action="store_true",
        help="Perform a full run: full catalog sync and price collection for ALL apps"
    )
    nightly_parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Bypass daily breakpoint resume and force re-fetch from Steam even if fetched today"
    )
    
    # Resume run
    resume_parser = subparsers.add_parser(
        "resume-run", 
        help="Resume a failed crawl run"
    )
    resume_parser.add_argument(
        "--run-id", 
        required=True,
        help="Run ID to resume"
    )
    
    # Worker daemon
    worker_parser = subparsers.add_parser(
        "run-worker",
        help="Run the daemon worker that pulls jobs from PocketBase"
    )
    
    # Validate JSONL
    validate_parser = subparsers.add_parser(
        "validate-jsonl", 
        help="Validate generated JSONL files"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    setup_logging()
    
    config = get_config()
    print(f"Steam Price Collector v0.1.0")
    print(f"Mode: {args.command}")
    print(f"Regions: {config.regions}")
    print(f"Data root: {config.data_root}")
    print("-" * 60)
    
    if args.command == "full-sync-catalog":
        print("Starting full catalog synchronization...")
        import asyncio
        asyncio.run(run_catalog_sync(mode="full"))
        
    elif args.command == "incremental-sync-catalog":
        print("Starting incremental catalog synchronization...")
        import asyncio
        asyncio.run(run_catalog_sync(mode="incremental"))
        
    elif args.command == "collect-prices":
        import asyncio
        regions = args.regions or config.regions
        print(f"Collecting prices for regions: {regions}")
        
        # Determine which apps to collect for
        # By default, we look at today's catalog
        dt = format_date()
        path_manager = get_path_manager()
        catalog_path = path_manager.get_catalog_path(dt)
        
        if not catalog_path.exists():
            print(f"Error: No catalog found for today ({dt}). Please run a catalog sync first.")
            sys.exit(1)
            
        print(f"Loading app IDs from {catalog_path}...")
        appids = []
        for app in read_jsonl(catalog_path, model_class=SteamAppCatalog):
            appids.append(app.appid)
            
        if not appids:
            print("No apps found in today's catalog.")
            sys.exit(0)
            
        if args.limit > 0:
            print(f"Limiting collection to {args.limit} apps.")
            appids = appids[:args.limit]
            
        print(f"Found {len(appids)} apps. Starting collection...")
        asyncio.run(collect_prices(appids=appids, regions=regions))
        
    elif args.command == "nightly-job":
        import asyncio
        regions = args.regions or config.regions
        run_id = generate_run_id()
        print(f"Starting nightly job with run_id: {run_id}")
        print(f"Target regions: {regions}")
        
        if args.full:
            print("\nStep 1: FULL catalog synchronization...")
            asyncio.run(run_catalog_sync(mode="full"))
            
            print("\nStep 2: Price collection for ALL apps...")
            dt = format_date()
            path_manager = get_path_manager()
            catalog_path = path_manager.get_catalog_path(dt)
            appids = []
            if catalog_path.exists():
                for app in read_jsonl(catalog_path):
                    appids.append(app["appid"])
            else:
                print(f"Error: No catalog found for today ({dt}). Run full-sync-catalog first.")
                sys.exit(1)
        else:
            print("\nStep 1: Incremental catalog synchronization...")
            _, changed_apps = asyncio.run(run_catalog_sync(mode="incremental"))
            
            print("\nStep 2: Price collection for changed apps...")
            if not changed_apps:
                print("No apps changed since last sync. Skipping price collection.")
                appids = []
            else:
                appids = [app["appid"] for app in changed_apps]

        if appids:
            if args.limit > 0:
                print(f"Limiting collection to {args.limit} apps.")
                appids = appids[:args.limit]
            print(f"Found {len(appids)} apps to process. Collecting prices...")
            asyncio.run(collect_prices(appids=appids, regions=regions, run_id=run_id, force_refresh=args.force_refresh))
        
    elif args.command == "run-worker":
        print("Starting worker daemon...")
        import asyncio
        from .worker import run_worker
        asyncio.run(run_worker())
        
    elif args.command == "resume-run":
        print(f"Resuming run: {args.run_id}")
        print("✅ resume-run command registered (implementation pending)")
        
    elif args.command == "validate-jsonl":
        print("Validating JSONL files...")
        print("✅ validate-jsonl command registered (implementation pending)")
    
    print(f"\nRun completed at: {get_utc_now()}")


if __name__ == "__main__":
    main()
