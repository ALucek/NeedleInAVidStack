"""Helpers for working with Google Gen AI and stored analyses."""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from google import genai
from google.genai import types
from google.oauth2 import service_account

from paths import ANALYSIS_DIR, ensure_output_dirs

###############################################################################
# Initialize Gen AI Client
###############################################################################

def initialize_genai_client(api_choice: str, credentials: str | None, project_id: str | None, location: str | None):
    """Initialise a Google Gen AI client for Gemini API or Vertex AI."""

    if api_choice == "Vertex AI":
        if not credentials or not Path(credentials).exists():
            raise RuntimeError("Invalid GCP credentials file path. Please check your input.")

        try:
            gcp_credentials = service_account.Credentials.from_service_account_file(credentials).with_scopes(
                ["https://www.googleapis.com/auth/cloud-platform"]
            )
            return genai.Client(vertexai=True, project=project_id, location=location, credentials=gcp_credentials)
        except Exception as exc:  # pragma: no cover - depends on external files
            raise RuntimeError(f"Failed to load GCP credentials: {exc}") from exc

    if api_choice == "Gemini API":
        if not credentials:
            raise RuntimeError("Gemini API key is missing. Please enter your API key.")
        return genai.Client(api_key=credentials)

    raise RuntimeError("Invalid API selection. Choose 'Gemini API' or 'Vertex AI'.")


###############################################################################
# Analyze Audio
###############################################################################


def analyze_audio_with_genai(audio_path: str | Path, prompt: str, client, model_name: str) -> str:
    """Analyse ``audio_path`` using a supplied Gen AI *client*."""

    try:
        with Path(audio_path).open("rb") as audio_file:
            audio_bytes = audio_file.read()

        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/mpeg")
        response = client.models.generate_content(model=model_name, contents=[audio_part, prompt])
        return response.text.strip()
    except Exception as exc:  # pragma: no cover - depends on remote API
        raise RuntimeError(f"Gen AI analysis error: {exc}") from exc


###############################################################################
# Analysis file helpers
###############################################################################


def analysis_path_for(audio_file: str | Path) -> Path:
    """Return the expected analysis path for *audio_file*."""

    ensure_output_dirs()
    audio_stem = Path(audio_file).stem
    return ANALYSIS_DIR / f"{audio_stem}_analysis.txt"


def load_existing_analysis(audio_file: str | Path) -> Tuple[bool, str | None]:
    """Load the stored analysis for *audio_file* if it exists."""

    analysis_path = analysis_path_for(audio_file)
    if analysis_path.exists():
        return True, analysis_path.read_text(encoding="utf-8")
    return False, None


def get_all_existing_analyses() -> List[Tuple[str, Path]]:
    """Return ``(audio_filename, analysis_path)`` pairs for saved analyses."""

    ensure_output_dirs()
    analyses: List[Tuple[str, Path]] = []
    for analysis_file in sorted(ANALYSIS_DIR.glob("*_analysis.txt")):
        audio_filename = f"{analysis_file.stem.removesuffix('_analysis')}.mp3"
        analyses.append((audio_filename, analysis_file))
    return analyses
