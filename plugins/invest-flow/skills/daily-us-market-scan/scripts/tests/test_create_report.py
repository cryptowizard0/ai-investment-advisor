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


class TemplateContractTests(unittest.TestCase):
    """Pin the focused, conclusion-first report template structure."""

    @classmethod
    def setUpClass(cls):
        module = load_create_report_module()
        cls.template_text = module.TEMPLATE_PATH.read_text(encoding="utf-8")
        cls.template_lines = cls.template_text.splitlines()

    def test_sections_are_conclusion_first_and_in_order(self):
        expected_order = [
            "## 0. 核心结论",
            "## 1. 大盘与宏观",
            "## 2. 板块与主题",
            "## 3. 新动态雷达",
            "## 4. 宽度与关键位",
            "## 5. 个股",
            "## 6. 财报与日历",
            "## 7. 明日剧本与风险",
        ]
        positions = []
        for header in expected_order:
            index = self.template_text.find(header)
            self.assertNotEqual(index, -1, f"缺少必需章节: {header}")
            positions.append(index)
        self.assertEqual(positions, sorted(positions), "章节顺序错误")

    def test_conclusion_card_holds_final_verdict_fields(self):
        section_zero = self.template_text.split("## 1. ")[0]
        for required in ["一句话总结", "当前市场阶段", "操作倾向", "最值得关注的 5 个信号"]:
            self.assertIn(required, section_zero, f"第 0 节缺少: {required}")

    def test_new_dynamics_radar_is_required_slot(self):
        radar_start = self.template_text.find("## 3. 新动态雷达")
        radar_end = self.template_text.find("## 4. ")
        radar = self.template_text[radar_start:radar_end]
        self.assertIn("必填", self.template_text[radar_start : radar_start + 40])
        self.assertIn("未发现", radar, "雷达节缺少'确无新动态'的如实声明出口")

    def test_bloated_legacy_sections_are_gone(self):
        for legacy in [
            "## 15. 最终结论",
            "## 12. 我的重点关注股观察",
            "## 11. 板块轮动判断",
            "## 2. 盘中走势复盘",
            "### 8.1 大型科技七巨头",
        ]:
            self.assertNotIn(legacy, self.template_text, f"旧膨胀结构仍在: {legacy}")

    def test_template_stays_within_line_budget(self):
        self.assertLessEqual(
            len(self.template_lines),
            200,
            f"模板 {len(self.template_lines)} 行,超出 200 行骨架预算",
        )

    def test_template_declares_hard_report_line_cap(self):
        self.assertIn("300 行", self.template_text, "模板未声明全文 300 行硬上限")


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
