import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_nhnl as bn  # noqa: E402


def daily_index(periods: int, start: str = "2024-01-01") -> pd.DatetimeIndex:
    return pd.bdate_range(start, periods=periods)


def synthetic_prices(periods: int = 320) -> pd.DataFrame:
    idx = daily_index(periods)
    up = pd.Series(range(1, periods + 1), index=idx, dtype=float)
    down = pd.Series(range(periods, 0, -1), index=idx, dtype=float)
    flat = pd.Series(100.0, index=idx)
    short = flat.copy()
    short.iloc[:-100] = float("nan")  # listed too recently to be eligible
    return pd.DataFrame({"UP": up, "DOWN": down, "FLAT": flat, "SHORT": short})


def breadth_frame(weekly_targets: list[float], nh_per_day: list[int],
                  nl_per_day: list[int]) -> pd.DataFrame:
    idx = daily_index(len(weekly_targets) * 5, start="2024-01-01")
    ratio = [weekly_targets[i // 5] for i in range(len(idx))]
    nh = [nh_per_day[i // 5] for i in range(len(idx))]
    nl = [nl_per_day[i // 5] for i in range(len(idx))]
    return pd.DataFrame({"weekly_ratio": ratio, "nh": nh, "nl": nl,
                         "daily_nhnl": [h - l for h, l in zip(nh, nl)]}, index=idx)


class ThresholdTests(unittest.TestCase):
    def test_absolute_equivalents_scale_with_universe(self) -> None:
        thresholds = bn.abs_thresholds(30)
        self.assertAlmostEqual(thresholds["capitulation"], -17.13, places=2)
        self.assertAlmostEqual(thresholds["bull_confirm"], 10.71, places=2)


class BreadthTests(unittest.TestCase):
    def test_counts_and_eligibility(self) -> None:
        breadth = bn.compute_breadth(synthetic_prices(), lookback=252)
        last = breadth.iloc[-1]
        self.assertEqual(last["nh"], 1)       # UP keeps making 252d highs
        self.assertEqual(last["nl"], 1)       # DOWN keeps making 252d lows
        self.assertEqual(last["daily_nhnl"], 0)
        self.assertEqual(last["n_eligible"], 3)  # SHORT lacks 252d of history
        self.assertAlmostEqual(last["weekly_ratio"], 0.0)

    def test_warmup_rows_are_nan(self) -> None:
        breadth = bn.compute_breadth(synthetic_prices(), lookback=252)
        self.assertTrue(pd.isna(breadth["weekly_ratio"].iloc[100]))


class IndicatorTests(unittest.TestCase):
    def test_impulse_colors_track_trend(self) -> None:
        idx = daily_index(80)
        rising = pd.Series([100 * 1.01 ** i for i in range(80)], index=idx)
        falling = pd.Series([100 * 0.99 ** i for i in range(80)], index=idx)
        self.assertEqual(bn.impulse(rising).iloc[-1], "green")
        self.assertEqual(bn.impulse(falling).iloc[-1], "red")

    def test_below_level_episodes_finds_troughs(self) -> None:
        idx = pd.date_range("2024-01-05", periods=7, freq="W-FRI")
        series = pd.Series([0.1, -0.2, -0.5, -0.1, 0.2, -0.3, 0.4], index=idx)
        episodes = bn.below_level_episodes(series, 0.0)
        self.assertEqual(len(episodes), 2)
        self.assertAlmostEqual(episodes[0]["trough"], -0.5)
        self.assertAlmostEqual(episodes[1]["trough"], -0.3)
        self.assertIsNotNone(episodes[1]["end"])


class DivergenceTests(unittest.TestCase):
    def build(self, second_trough: float):
        idx = pd.date_range("2024-01-05", periods=12, freq="W-FRI")
        ratio = pd.Series([0.2, -0.5, -2.0, -0.4, 0.3, 0.1,
                           -0.3, second_trough, -0.2, 0.4, 0.5, 0.6], index=idx)
        price = pd.Series([110, 105, 100, 102, 108, 107,
                           95, 90, 96, 104, 108, 112], index=idx, dtype=float)
        return ratio, price

    def test_valid_divergence_detected(self) -> None:
        found = bn.divergence_check(*self.build(second_trough=-0.9))
        self.assertIsNotNone(found)
        self.assertAlmostEqual(found["first"]["trough"], -2.0)
        self.assertAlmostEqual(found["second"]["trough"], -0.9)

    def test_shallow_requirement_enforced(self) -> None:
        self.assertIsNone(bn.divergence_check(*self.build(second_trough=-1.5)))


class FalseBreakoutTests(unittest.TestCase):
    def test_break_and_reclaim_detected(self) -> None:
        idx = daily_index(250)
        close = pd.Series(100.0, index=idx)
        close.iloc[150] = 90.0   # prior significant low
        close.iloc[210] = 89.0   # break below it...
        close.iloc[211:214] = 92.0  # ...reclaimed within days
        events = bn.false_breakouts(close)
        self.assertEqual(len(events), 1)
        self.assertAlmostEqual(events[0]["ref_low"], 90.0)


class ClassifyTests(unittest.TestCase):
    def test_capitulation_is_p1(self) -> None:
        frame = breadth_frame([0.0] * 11 + [-1.0], [0] * 12, [20] * 12)
        self.assertEqual(bn.classify(frame, None)["state"], "P1")

    def test_recent_confirm_is_p5(self) -> None:
        frame = breadth_frame([0.0] * 11 + [0.5], [10] * 12, [0] * 12)
        self.assertEqual(bn.classify(frame, None)["state"], "P5")

    def test_dried_highs_without_lows_is_judgment_zone(self) -> None:
        targets = [0.5] * 24 + [0.0] * 6
        nh = [8] * 24 + [0] * 6
        frame = breadth_frame(targets, nh, [0] * 30)
        self.assertEqual(bn.classify(frame, None)["state"], "PX")

    def test_dried_highs_with_lows_is_p0(self) -> None:
        targets = [0.5] * 24 + [0.0] * 3 + [-0.1] * 3
        nh = [8] * 24 + [0] * 6
        nl = [0] * 24 + [0] * 3 + [2] * 3
        frame = breadth_frame(targets, nh, nl)
        self.assertEqual(bn.classify(frame, None)["state"], "P0")


class CliTests(unittest.TestCase):
    def test_offline_json_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            prices = synthetic_prices()[["UP", "DOWN", "FLAT"]]
            prices.to_csv(tmp_path / "prices.csv")
            index_close = prices["FLAT"].rename("close")
            index_close.to_csv(tmp_path / "index.csv")
            (tmp_path / "tickers.txt").write_text("UP\nDOWN\nFLAT\n", encoding="utf-8")
            output = bn.run([
                "--tickers-file", str(tmp_path / "tickers.txt"),
                "--prices-file", str(tmp_path / "prices.csv"),
                "--index-file", str(tmp_path / "index.csv"),
                "--label", "TEST", "--format", "json",
                "--cache-dir", str(tmp_path / "cache"),
            ])
            result = json.loads(output)
            self.assertEqual(result["n_universe"], 3)
            self.assertIn(result["state"], bn.STATE_LABELS)
            self.assertEqual(len(result["recent_weeks"]), 8)
            self.assertTrue((tmp_path / "cache" / "nhnl_daily_TEST.csv").exists())


if __name__ == "__main__":
    unittest.main()
