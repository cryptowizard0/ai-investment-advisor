import csv
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from calculate_cycles import PricePoint, detect_cycles, load_prices  # noqa: E402


class DetectCyclesTests(unittest.TestCase):
    def test_sox_sample_closes_bull_and_opens_bear(self):
        points = [
            PricePoint(date(2025, 4, 8), 3562.94218291255),
            PricePoint(date(2026, 6, 22), 14634.72240616581),
            PricePoint(date(2026, 7, 17), 11673.88857801999),
            PricePoint(date(2026, 7, 20), 11743.84912277605),
        ]

        cycles = detect_cycles(points, threshold=0.20, seed_kind="bull")

        self.assertEqual(len(cycles), 2)
        bull, bear = cycles
        self.assertEqual((bull.kind, bull.status), ("bull", "completed"))
        self.assertEqual(bull.end_date, date(2026, 6, 22))
        self.assertEqual(bull.duration_days, 440)
        self.assertAlmostEqual(bull.return_pct, 310.7482427402895)
        self.assertEqual(bull.confirmed_date, date(2026, 7, 17))

        self.assertEqual((bear.kind, bear.status), ("bear", "ongoing"))
        self.assertEqual(bear.start_date, date(2026, 6, 22))
        self.assertEqual(bear.end_date, date(2026, 7, 17))
        self.assertEqual(bear.duration_days, 25)
        self.assertAlmostEqual(bear.return_pct, -20.231568088359364)

    def test_ongoing_cycle_uses_extreme_date_instead_of_last_date(self):
        points = [
            PricePoint(date(2026, 1, 1), 100.0),
            PricePoint(date(2026, 1, 2), 75.0),
            PricePoint(date(2026, 1, 3), 80.0),
        ]

        cycle = detect_cycles(points, seed_kind="bear")[0]

        self.assertEqual(cycle.end_date, date(2026, 1, 2))
        self.assertEqual(cycle.return_pct, -25.0)
        self.assertEqual(cycle.status, "ongoing")

    def test_auto_mode_backdates_first_confirmed_bull_to_low(self):
        points = [
            PricePoint(date(2026, 1, 1), 105.0),
            PricePoint(date(2026, 1, 2), 100.0),
            PricePoint(date(2026, 1, 3), 121.0),
        ]

        cycle = detect_cycles(points, seed_kind="auto")[0]

        self.assertEqual(cycle.kind, "bull")
        self.assertEqual(cycle.start_date, date(2026, 1, 2))
        self.assertEqual(cycle.confirmed_date, date(2026, 1, 3))

    def test_bear_closes_and_opens_bull_after_threshold_rebound(self):
        points = [
            PricePoint(date(2026, 1, 1), 100.0),
            PricePoint(date(2026, 1, 2), 70.0),
            PricePoint(date(2026, 1, 3), 84.0),
        ]

        cycles = detect_cycles(points, seed_kind="bear")

        self.assertEqual(len(cycles), 2)
        bear, bull = cycles
        self.assertEqual((bear.kind, bear.status), ("bear", "completed"))
        self.assertEqual(bear.end_date, date(2026, 1, 2))
        self.assertEqual(bear.confirmed_date, date(2026, 1, 3))
        self.assertEqual((bull.kind, bull.status), ("bull", "ongoing"))
        self.assertEqual(bull.start_date, date(2026, 1, 2))
        self.assertAlmostEqual(bull.return_pct, 20.0)


class LoadPricesTests(unittest.TestCase):
    def test_loads_case_insensitive_columns_and_honors_as_of(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "prices.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["Date", "Close"])
                writer.writerow(["2026/01/02", "1,234.5"])
                writer.writerow(["2026/01/03", "1,250.0"])
                writer.writerow(["2026/01/04", "1,260.0"])

            points = load_prices(path, as_of=date(2026, 1, 3))

        self.assertEqual(
            points,
            [
                PricePoint(date(2026, 1, 2), 1234.5),
                PricePoint(date(2026, 1, 3), 1250.0),
            ],
        )


if __name__ == "__main__":
    unittest.main()
