"""trakt-recs: Trakt watch-history puller + context emitter for Claude.

Subcommands: auth, pull, context, status.
"""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trakt-recs", description=__doc__)
    parser.add_subparsers(dest="cmd", required=True)
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
