import unittest
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


class ModelTests(unittest.TestCase):
    def test_stage_result_to_dict_contains_handoff(self):
        from investflow_pipeline.models import AnalysisStatus, Handoff, StageResult

        result = StageResult(
            skill_name="fundamental-analysis",
            agent_name="fundamental",
            status=AnalysisStatus.SUCCESS,
            report_path="/tmp/report.md",
            handoff=Handoff(
                conclusion="业务质量稳定",
                recommendation="观望",
                confidence=62,
                key_evidence=["收入增长"],
                risk_flags=["估值偏高"],
                contradiction_points=[],
                monitoring_signals=["下一季收入增速"],
                data_gaps=[],
            ),
            duration=1.5,
            retry_count=0,
        )

        data = result.to_dict()

        self.assertEqual(data["skill_name"], "fundamental-analysis")
        self.assertEqual(data["agent_name"], "fundamental")
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["handoff"]["recommendation"], "观望")
        self.assertEqual(data["handoff"]["confidence"], 62)
        self.assertTrue(result.is_success)


if __name__ == "__main__":
    unittest.main()
