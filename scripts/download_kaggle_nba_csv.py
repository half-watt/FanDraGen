#!/usr/bin/env python3
"""Download the Kaggle NBA 24/25 stats dataset via kagglehub and install into data/kaggle/.

Requires: pip install kagglehub
Kaggle API credentials: https://www.kaggle.com/docs/api (kaggle.json or env)

Usage (from repo root):
  python scripts/download_kaggle_nba_csv.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import kagglehub

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEST = PROJECT_ROOT / "data" / "kaggle" / "nba_player_stats_2425.csv"
DATASET = "eduardopalmieri/nba-player-stats-season-2425"
SOURCE_NAME = "database_24_25.csv"


def main() -> None:
    path = Path(kagglehub.dataset_download(DATASET))
    src = path / SOURCE_NAME
    if not src.exists():
        csvs = sorted(path.glob("*.csv"))
        if not csvs:
            raise FileNotFoundError(f"No CSV in {path}")
        src = csvs[0]
        print(f"Using {src.name} (expected {SOURCE_NAME} not found).")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, DEST)
    print(f"Installed: {DEST}")
    print(f"Source:    {src}")


if __name__ == "__main__":
    main()
