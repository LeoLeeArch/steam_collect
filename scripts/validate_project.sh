#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "[check] required files"
test -f SteamPulse.xcodeproj/project.pbxproj
test -f README.md
test -f AGENTS.md
test -f docs/PLAN.md
test -f docs/STATUS.md

echo "[check] no database dependencies"
if rg -n "CoreData|Realm|SQLite|PostgreSQL|MongoDB|Redis|MySQL" SteamPulse README.md docs AGENTS.md >/tmp/db_hits.txt; then
  if [[ -s /tmp/db_hits.txt ]]; then
    echo "Found potential DB-related keywords (verify context):"
    cat /tmp/db_hits.txt
  fi
fi

echo "[check] phase-1 key modules exist"
test -f SteamPulse/Services/Sources/SteamChartsSourceProvider.swift
test -f SteamPulse/Services/Sources/GameDetailService.swift
test -f SteamPulse/Services/History/PriceHistoryStore.swift
test -f SteamPulse/Services/History/PriceAnalyzer.swift

echo "[ok] repository structure validation passed"
