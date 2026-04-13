from dataclasses import dataclass
from typing import Literal


ScanMode = Literal["fast", "deep"]


@dataclass(frozen=True, slots=True)
class ScanModeConfig:
    mode: ScanMode
    label: str
    target_coverage: int
    max_hotspot_files: int
    max_blocks_per_file: int
    max_path_units: int
    multi_pass: bool


SCAN_MODE_CONFIGS: dict[ScanMode, ScanModeConfig] = {
    "fast": ScanModeConfig(
        mode="fast",
        label="Fast Scan",
        target_coverage=45,
        max_hotspot_files=18,
        max_blocks_per_file=4,
        max_path_units=24,
        multi_pass=False,
    ),
    "deep": ScanModeConfig(
        mode="deep",
        label="Deep Scan",
        target_coverage=95,
        max_hotspot_files=9999,
        max_blocks_per_file=9999,
        max_path_units=9999,
        multi_pass=True,
    ),
}


def get_scan_mode_config(mode: str | None) -> ScanModeConfig:
    normalized = (mode or "deep").strip().lower()
    if normalized == "fast":
        return SCAN_MODE_CONFIGS["fast"]
    return SCAN_MODE_CONFIGS["deep"]
