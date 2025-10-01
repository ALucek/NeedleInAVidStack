"""Application-level helpers shared by the Streamlit UI."""
from __future__ import annotations

from typing import List

import streamlit as st

from analysis_utils import analysis_path_for
from paths import AUDIO_DIR, ensure_output_dirs


def should_skip_analysis(audio_file: str, skip_reanalysis: bool) -> bool:
    """Return ``True`` when an analysis already exists and skipping is enabled."""

    if not skip_reanalysis:
        return False

    analysis_file = analysis_path_for(audio_file)
    return analysis_file.exists()


def save_analysis(audio_file: str, text: str) -> None:
    """Persist ``text`` for ``audio_file`` in the analysis directory."""

    analysis_file = analysis_path_for(audio_file)
    analysis_file.write_text(text, encoding="utf-8")


def list_audio_files() -> List[str]:
    """Return all MP3 files currently stored in :data:`AUDIO_DIR`."""

    ensure_output_dirs()
    return sorted(str(path) for path in AUDIO_DIR.glob("*.mp3"))


def info_message(message: str) -> None:
    """Display an information message without duplicating code."""

    st.info(message)


def warning_message(message: str) -> None:
    """Display a warning message without duplicating code."""

    st.warning(message)


def error_message(message: str) -> None:
    """Display an error message without duplicating code."""

    st.error(message)


def success_message(message: str) -> None:
    """Display a success message without duplicating code."""

    st.success(message)


def show_text_area(label: str, value: str, height: int = 200) -> None:
    """Render a read-only text area for displaying raw responses."""

    st.text_area(label, value=value, height=height)


def render_markdown(content: str) -> None:
    """Render Markdown content inside Streamlit."""

    st.markdown(content)
