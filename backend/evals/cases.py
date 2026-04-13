from dataclasses import dataclass
from pathlib import Path


FIXTURES_ROOT = Path(__file__).resolve().parents[1] / "fixtures"


@dataclass(frozen=True)
class EvalCase:
    name: str
    source_path: Path
    target_type: str
    expected_kind: str
    expected_min_findings: int
    expected_max_findings: int
    expected_score_floor: int
    expected_score_ceiling: int
    expected_severities: dict[str, int] | None = None
    tags: tuple[str, ...] = ()


EVAL_CASES = [
    EvalCase(
        name="vulnerable_demo",
        source_path=FIXTURES_ROOT / "vulnerable_demo.py",
        target_type="file",
        expected_kind="vulnerable",
        expected_min_findings=4,
        expected_max_findings=12,
        expected_score_floor=0,
        expected_score_ceiling=40,
        expected_severities={"critical": 2, "high": 2},
        tags=("fixture", "python"),
    ),
    EvalCase(
        name="safe_demo",
        source_path=FIXTURES_ROOT / "safe_demo.py",
        target_type="file",
        expected_kind="clean",
        expected_min_findings=0,
        expected_max_findings=0,
        expected_score_floor=90,
        expected_score_ceiling=100,
        expected_severities={"critical": 0, "high": 0, "medium": 0, "low": 0},
        tags=("fixture", "python", "clean"),
    ),
    EvalCase(
        name="cross_file_demo",
        source_path=FIXTURES_ROOT / "cross_file_demo",
        target_type="folder",
        expected_kind="vulnerable",
        expected_min_findings=1,
        expected_max_findings=6,
        expected_score_floor=0,
        expected_score_ceiling=85,
        expected_severities={"high": 1},
        tags=("fixture", "python", "cross_file"),
    ),
    EvalCase(
        name="sanitized_demo",
        source_path=FIXTURES_ROOT / "sanitized_demo.py",
        target_type="file",
        expected_kind="clean",
        expected_min_findings=0,
        expected_max_findings=0,
        expected_score_floor=90,
        expected_score_ceiling=100,
        expected_severities={"critical": 0, "high": 0, "medium": 0, "low": 0},
        tags=("fixture", "python", "clean", "sanitizer"),
    ),
]
