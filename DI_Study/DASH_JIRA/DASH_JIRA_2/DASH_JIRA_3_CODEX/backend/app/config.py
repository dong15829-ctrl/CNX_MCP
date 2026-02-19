import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
META_DIR = BASE_DIR / "META"


def _resolve_dataset_path(env_var: str | None, candidates: list[Path]) -> Path:
    if env_var:
        candidate = Path(env_var).expanduser()
        if candidate.exists():
            return candidate
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        f"Dataset not found. Tried: {[str(c) for c in candidates]} "
        f"(override with env variable)."
    )


DATA_FILE = _resolve_dataset_path(
    os.environ.get("JIRA_MODEL_DATASET"),
    [
        Path("/home/ubuntu/DI/DASH_JIRA_2/processed/dataset_modeling.csv"),
        BASE_DIR / "processed" / "dataset_modeling.csv",
    ],
)

TEST_DATA_FILE = _resolve_dataset_path(
    os.environ.get("JIRA_TEST_DATASET"),
    [
        Path("/home/ubuntu/DI/DASH_JIRA_2/processed/dataset_test.csv"),
        BASE_DIR / "processed" / "dataset_test.csv",
    ],
)

DEFAULT_TIME_WINDOW_DAYS = 30
TOP_LIMIT = 10
SIMULATION_MAX_BATCH = 50

CLOSED_STATUS_MARKERS = [
    "closed",
    "done",
    "resolved",
    "verification",
    "complete",
]

HIGH_PRIORITY_MARKERS = ["highest", "high", "critical", "p1", "p0"]
