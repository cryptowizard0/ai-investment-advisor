import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class RunScriptTests(unittest.TestCase):
    def test_limits_graceful_shutdown_wait(self) -> None:
        script = (REPO_ROOT / "web" / "run.sh").read_text(encoding="utf-8")

        self.assertRegex(
            script,
            re.compile(r"--timeout-graceful-shutdown\s+[1-9]\d*"),
        )


if __name__ == "__main__":
    unittest.main()
