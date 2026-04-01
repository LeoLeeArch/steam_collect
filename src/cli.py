#!/usr/bin/env python3
"""Command Line Interface for Steam Price Collector."""

import argparse
import sys
from datetime import datetime

from .config import get_config, get_path_manager
from .utils import generate_run_id, get_utc_now, format_date
from .catalog import run_catalog_sync


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
    
    # Validate JSONL
    validate_parser = subparsers.add_parser(
        "validate-jsonl", 
        help="Validate generated JSONL files"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
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
        regions = args.regions or config.regions
        print(f"Collecting prices for regions: {regions}")
        print("✅ collect-prices command registered (implementation pending)")
        
    elif args.command == "nightly-job":
        regions = args.regions or config.regions
        run_id = generate_run_id()
        print(f"Starting nightly job with run_id: {run_id}")
        print(f"Target regions: {regions}")
        print("✅ nightly-job command registered (implementation pending)")
        
    elif args.command == "resume-run":
        print(f"Resuming run: {args.run_id}")
        print("✅ resume-run command registered (implementation pending)")
        
    elif args.command == "validate-jsonl":
        print("Validating JSONL files...")
        print("✅ validate-jsonl command registered (implementation pending)")
    
    print(f"\nRun completed at: {get_utc_now()}")


if __name__ == "__main__":
    main()
