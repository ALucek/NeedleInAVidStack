"""Common filesystem helpers for NeedleInAVidStack."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

OUTPUT_DIR = Path("output")
AUDIO_DIR = OUTPUT_DIR / "audio"
ANALYSIS_DIR = OUTPUT_DIR / "analysis"


def ensure_output_dirs() -> Tuple[Path, Path]:
    """Ensure that the audio and analysis directories exist."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    return AUDIO_DIR, ANALYSIS_DIR
