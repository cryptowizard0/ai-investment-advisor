#!/usr/bin/env python3
"""Serve report files with explicit UTF-8 content types."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


class Utf8ReportRequestHandler(SimpleHTTPRequestHandler):
    """Static file handler that declares UTF-8 for report text files."""

    def do_GET(self) -> None:
        self._drop_conditional_cache_headers()
        super().do_GET()

    def do_HEAD(self) -> None:
        self._drop_conditional_cache_headers()
        super().do_HEAD()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def _drop_conditional_cache_headers(self) -> None:
        for header in ("If-Modified-Since", "If-None-Match"):
            if header in self.headers:
                del self.headers[header]

    def guess_type(self, path: str) -> str:
        content_type = super().guess_type(path)
        suffix = Path(path).suffix.lower()

        if suffix == ".md":
            return "text/markdown; charset=utf-8"
        if suffix == ".html":
            return "text/html; charset=utf-8"
        if suffix in {".css", ".js", ".json", ".txt"} and "charset=" not in content_type:
            return f"{content_type}; charset=utf-8"
        return content_type


def create_handler(directory: Path) -> type[Utf8ReportRequestHandler]:
    return partial(Utf8ReportRequestHandler, directory=str(directory))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve InvestFlow report outputs with explicit UTF-8 charset headers."
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host to bind. Default: {DEFAULT_HOST}.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to bind. Default: {DEFAULT_PORT}.",
    )
    parser.add_argument(
        "--directory",
        default=str(REPO_ROOT),
        help="Directory to serve. Defaults to the repository root.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    directory = Path(args.directory).resolve()
    if not directory.exists():
        raise SystemExit(f"Directory not found: {directory}")
    if not directory.is_dir():
        raise SystemExit(f"Path is not a directory: {directory}")

    handler_class = create_handler(directory)
    server = ThreadingHTTPServer((args.host, args.port), handler_class)
    url = f"http://{args.host}:{server.server_port}/output/index.html"
    print(f"Serving {directory} with UTF-8 report headers")
    print(f"Open {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
