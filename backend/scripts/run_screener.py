#!/usr/bin/env python3
"""
Run dynamic stock screener.

Usage:
    python scripts/run_screener.py [--max-stocks 100]
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from screener import DynamicScreener


def main():
    parser = argparse.ArgumentParser(description="Run dynamic stock screener")
    parser.add_argument("--max-stocks", type=int, default=100, help="Maximum stocks to select")
    parser.add_argument("--output", type=str, default=None, help="Output path for watchlist.json")
    args = parser.parse_args()

    screener = DynamicScreener(output_path=args.output)
    tickers = screener.run_and_save(max_stocks=args.max_stocks)

    print(f"Selected {len(tickers)} stocks")


if __name__ == "__main__":
    main()
