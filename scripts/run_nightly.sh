#!/bin/bash
# Steam Price Collector Nightly Run Script

# Exit on error
set -e

# Load environment variables if needed
# source /path/to/conda/etc/profile.d/conda.sh
# conda activate py312

echo "Starting Nightly Job: $(date)"

# Run incremental sync and price collection
python -m src.cli nightly-job --regions us cn gb jp de

echo "Job Finished: $(date)"
