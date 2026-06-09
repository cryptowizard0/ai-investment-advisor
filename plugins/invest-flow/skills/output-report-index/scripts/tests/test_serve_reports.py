"""Tests for the UTF-8 report static server."""

from __future__ import annotations

import importlib.util
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "serve_reports.py"


def load_server_module():
    if not SCRIPT_PATH.exists():
        raise AssertionError(f"Server script is missing: {SCRIPT_PATH}")

    spec = importlib.util.spec_from_file_location("serve_reports", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load server script: {SCRIPT_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ServeReportsTests(unittest.TestCase):
    def test_serves_markdown_and_html_with_utf8_charset(self) -> None:
        server_module = load_server_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root_dir = Path(tmpdir)
            output_dir = root_dir / "output"
            output_dir.mkdir()
            markdown_path = output_dir / "中文报告.md"
            markdown_path.write_text("# 中文报告\n\n正文：混合云与AI。", encoding="utf-8")
            html_path = output_dir / "index.html"
            html_path.write_text("<!doctype html><p>中文</p>", encoding="utf-8")

            original_log_message = server_module.Utf8ReportRequestHandler.log_message
            server_module.Utf8ReportRequestHandler.log_message = lambda *args, **kwargs: None
            handler_class = server_module.create_handler(root_dir)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{httpd.server_port}"
                with urlopen(f"{base_url}/output/%E4%B8%AD%E6%96%87%E6%8A%A5%E5%91%8A.md") as response:
                    content_type = response.headers.get("Content-Type", "")
                    body = response.read().decode("utf-8")
                with urlopen(f"{base_url}/output/index.html") as response:
                    html_content_type = response.headers.get("Content-Type", "")
                    cache_control = response.headers.get("Cache-Control", "")
                cached_request = Request(
                    f"{base_url}/output/index.html",
                    headers={"If-Modified-Since": "Wed, 09 Jun 2099 10:00:00 GMT"},
                )
                with urlopen(cached_request) as response:
                    cached_status = response.status
                    cached_body = response.read().decode("utf-8")

                self.assertIn("text/markdown", content_type)
                self.assertIn("charset=utf-8", content_type.lower())
                self.assertIn("# 中文报告", body)
                self.assertIn("text/html", html_content_type)
                self.assertIn("charset=utf-8", html_content_type.lower())
                self.assertIn("no-store", cache_control)
                self.assertEqual(200, cached_status)
                self.assertIn("中文", cached_body)
            finally:
                httpd.shutdown()
                httpd.server_close()
                thread.join(timeout=2)
                server_module.Utf8ReportRequestHandler.log_message = original_log_message


if __name__ == "__main__":
    unittest.main()
