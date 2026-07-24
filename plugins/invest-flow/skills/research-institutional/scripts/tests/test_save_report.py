"""Tests for the institutional report saver."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "save_report.py"


def load_save_report_module():
    spec = importlib.util.spec_from_file_location("save_report", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load report saver: {SCRIPT_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SaveReportTests(unittest.TestCase):
    def test_saves_canonical_filename_and_preserves_duplicate_reports(self):
        saver = load_save_report_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with patch.object(saver, "datetime") as mocked_datetime:
                mocked_datetime.now.return_value = datetime(2026, 7, 24)
                first_path = saver.save_report("# First\n", "tsla", output_dir)
                second_path = saver.save_report("# Second\n", "tsla", output_dir)

        self.assertEqual(
            first_path.name,
            "research-institutional-机构操作分析-20260724-TSLA.md",
        )
        self.assertEqual(
            second_path.name,
            "research-institutional-机构操作分析-20260724-TSLA(1).md",
        )


if __name__ == "__main__":
    unittest.main()
