"""CLI: run Guard HTTP server."""

from __future__ import annotations

import argparse

from tehuti_guard import __version__
from tehuti_guard.server import default_port, run_server


def main() -> None:
    p = argparse.ArgumentParser(
        prog="tehuti-guard-serve",
        description="Tehuti Guard v1 decision API (consumes Sentinel unified view).",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--host", default="127.0.0.1", help="Bind address")
    p.add_argument(
        "--port",
        type=int,
        default=default_port(),
        help="Port (default 8013 or TEHUTI_GUARD_PORT)",
    )
    args = p.parse_args()
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
