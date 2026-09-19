"""
Runs the AI decision pipeline directly against the provided sample_test_cases.json and reports accuracy.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.decide import decide

TEST_CASES_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_test_cases.json"


def main():
    cases = json.loads(TEST_CASES_PATH.read_text(encoding="utf-8"))

    correct = 0
    print(f"{len(cases)} test cases\n")
    for case in cases:
        ticket = {k: v for k, v in case.items() if k not in ("case_id", "expected_action")}
        expected = case["expected_action"]
        result = decide(ticket)
        got = result["action"]
        ok = got == expected
        correct += ok
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {case['case_id']}: expected={expected} got={got}")

    total = len(cases)
    print(f"\nCorrect: {correct}")
    print(f"Incorrect: {total - correct}")
    print(f"Accuracy: {correct / total * 100:.1f}%")


if __name__ == "__main__":
    main()
