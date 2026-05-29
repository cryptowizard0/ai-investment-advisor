import importlib.util
import unittest
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "create_report.py"


def load_create_report_module():
    spec = importlib.util.spec_from_file_location("daily_create_report", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SessionDateTests(unittest.TestCase):
    def test_beijing_morning_uses_completed_us_session_not_local_date(self):
        module = load_create_report_module()
        now = datetime(2026, 5, 27, 8, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

        self.assertEqual(module.latest_completed_us_session(now), date(2026, 5, 26))

    def test_weekend_or_holiday_skips_to_prior_trading_day(self):
        module = load_create_report_module()
        now = datetime(2026, 1, 19, 8, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

        self.assertEqual(module.latest_completed_us_session(now), date(2026, 1, 16))


if __name__ == "__main__":
    unittest.main()
