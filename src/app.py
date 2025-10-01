"""Streamlit UI for the NeedleInAVidStack application."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import streamlit as st

from analysis_utils import (
    analyze_audio_with_genai,
    get_all_existing_analyses,
    initialize_genai_client,
    load_existing_analysis,
)
from app_utils import (
    error_message,
    info_message,
    list_audio_files,
    render_markdown,
    save_analysis,
    should_skip_analysis,
    show_text_area,
    success_message,
    warning_message,
)
from video_processing import process_videos_in_directory

###############################################################################
# Constants and Defaults
###############################################################################
DEFAULT_PROMPT = """Analyze this audio for specific examples of [target topic] - these are instances where [explain what you're looking for].

Please start with a brief overview of what the audio is about.

For each relevant example found, include:
- When it was mentioned (timestamp)
- What specific aspect of [target topic] was discussed
- The context and details provided
- Direct quotes from the speaker if they described it specifically

Don't include:
- General discussion about [target topic] without specific examples
- Tangential mentions or references
- Theory or hypothetical scenarios

End with your assessment: How confident are you these were genuine examples of [target topic]? Were any examples unclear or ambiguous? How reliable were the speakers in their descriptions?

If no clear examples are found, simply state that."""

DEFAULT_MODEL = "gemini-2.0-flash-001"
DEFAULT_GCP_PROJECT = "my-gcp-project"
DEFAULT_GCP_LOCATION = "us-east1"

###############################################################################
# Session state helpers
###############################################################################


def _apply_secrets() -> None:
    """Populate session state from ``st.secrets`` when available."""

    secrets: Dict[str, str] = getattr(st, "secrets", {})
    if not secrets:
        return

    if not st.session_state.get("credentials") and secrets.get("GEMINI_API_KEY"):
        st.session_state.api_choice = "Gemini API"
        st.session_state.credentials = secrets["GEMINI_API_KEY"]

    vertex_secrets = secrets.get("vertex_ai", {})
    if vertex_secrets:
        st.session_state.project_id = vertex_secrets.get("project_id", st.session_state.project_id)
        st.session_state.location = vertex_secrets.get("location", st.session_state.location)
        if vertex_secrets.get("credentials_file") and not st.session_state.get("credentials"):
            st.session_state.api_choice = "Vertex AI"
            st.session_state.credentials = vertex_secrets.get("credentials_file")


def initialise_session_state() -> None:
    """Ensure all keys used by the UI exist in ``st.session_state``."""

    defaults = {
        "analysis_prompt": DEFAULT_PROMPT,
        "api_choice": "Gemini API",
        "credentials": "",
        "project_id": DEFAULT_GCP_PROJECT,
        "location": DEFAULT_GCP_LOCATION,
        "model_name": DEFAULT_MODEL,
        "processed_audio_files": [],
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    if not st.session_state.get("_secrets_applied"):
        _apply_secrets()
        st.session_state._secrets_applied = True


###############################################################################
# UI Sections
###############################################################################


def render_prompt_input() -> None:
    with st.expander("Prompt Configuration", expanded=True):
        if st.button("Reset to Default Prompt"):
            st.session_state.analysis_prompt = DEFAULT_PROMPT

        st.session_state.analysis_prompt = st.text_area(
            "Analysis Prompt:",
            value=st.session_state.analysis_prompt,
            height=250,
        )


def render_api_configuration() -> None:
    with st.expander("API Configuration", expanded=True):
        st.session_state.api_choice = st.radio(
            "Choose API:",
            ["Gemini API", "Vertex AI"],
            index=0 if st.session_state.api_choice == "Gemini API" else 1,
            help="Select which API to use for analysis.",
        )

        st.session_state.model_name = st.text_input("Model Name:", value=st.session_state.model_name)

        st.write("---")
        st.markdown("#### Credentials")

        if st.session_state.api_choice == "Gemini API":
            st.session_state.credentials = st.text_input(
                "Gemini API Key:",
                value=st.session_state.credentials,
                type="password",
                help="Enter your Gemini API key",
            )
            st.session_state.project_id = None
            st.session_state.location = None
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.project_id = st.text_input(
                    "GCP Project ID:", value=st.session_state.project_id or ""
                )
            with col2:
                st.session_state.location = st.text_input(
                    "GCP Location:", value=st.session_state.location or ""
                )

            st.session_state.credentials = st.text_input(
                "Path to GCP Service Account JSON:",
                value=st.session_state.credentials,
                help="Enter path to your GCP service account credentials JSON file",
            )


def render_video_to_audio() -> None:
    with st.expander("Video to Audio Conversion", expanded=True):
        video_folder = st.text_input("Video Folder Path:", "./videos")

        if st.button("Convert Videos to Audio"):
            folder = Path(video_folder)
            if folder.is_dir():
                with st.spinner("Converting videos to audio..."):
                    audio_files = process_videos_in_directory(folder)
                    st.session_state.processed_audio_files = audio_files

                if st.session_state.processed_audio_files:
                    success_message(
                        f"Converted {len(st.session_state.processed_audio_files)} videos to audio."
                    )
                else:
                    warning_message("No videos were converted.")
            else:
                error_message("Invalid folder path. Please enter a valid directory.")


def _render_analysis_tabs(display_name: str, content: str) -> None:
    raw_tab, rendered_tab = st.tabs(["Raw Text", "Rendered Markdown"])
    with raw_tab:
        show_text_area(label=f"Raw analysis for {display_name}", value=content, height=200)
    with rendered_tab:
        render_markdown(content)


def render_audio_analysis() -> None:
    with st.expander("Analyze Audio Files", expanded=True):
        skip_reanalysis = st.checkbox("Skip re-analysis if file already exists?", value=True)

        existing_audio_files = list_audio_files()
        if existing_audio_files:
            st.session_state.processed_audio_files = existing_audio_files

        if st.button("Run Analysis"):
            audio_files = st.session_state.processed_audio_files
            if not audio_files:
                warning_message("No audio files found to analyze.")
                return

            if not st.session_state.credentials:
                error_message("Please provide your API key or GCP credentials JSON file.")
                return

            try:
                client = initialize_genai_client(
                    st.session_state.api_choice,
                    st.session_state.credentials,
                    st.session_state.project_id,
                    st.session_state.location,
                )
            except RuntimeError as exc:
                error_message(str(exc))
                return

            st.markdown("### Starting Analysis")
            for audio_file in audio_files:
                audio_name = Path(audio_file).name

                if skip_reanalysis and should_skip_analysis(audio_file, skip_reanalysis=True):
                    info_message(f"Skipping `{audio_name}` (analysis file exists).")
                    exists, content = load_existing_analysis(audio_file)
                    if exists and content:
                        st.markdown("---")
                        st.markdown(f"#### Existing Analysis: `{audio_name}`")
                        _render_analysis_tabs(audio_name, content)
                    continue

                st.markdown("---")
                st.markdown(f"#### Analyzing: `{audio_name}`")
                try:
                    response_text = analyze_audio_with_genai(
                        audio_file,
                        st.session_state.analysis_prompt,
                        client,
                        st.session_state.model_name,
                    )
                except RuntimeError as exc:
                    error_message(f"Failed to analyze {audio_file}. Error: {exc}")
                    continue

                save_analysis(audio_file, response_text)
                _render_analysis_tabs(audio_name, response_text)
                success_message(f"Saved analysis for `{audio_name}`")

            success_message("Analysis complete!")


def render_analysis_viewer() -> None:
    """Renders a viewer for existing analysis files."""

    with st.expander("View Existing Analyses", expanded=True):
        existing_analyses = get_all_existing_analyses()

        if not existing_analyses:
            info_message("No existing analysis files found in output/analysis directory.")
            return

        st.write(f"Found {len(existing_analyses)} existing analysis files.")
        analysis_options = ["Select an analysis..."] + [audio_file for audio_file, _ in existing_analyses]
        selected_analysis = st.selectbox("Choose an analysis to view:", analysis_options)

        if selected_analysis and selected_analysis != "Select an analysis...":
            selected_file = next(
                (
                    analysis_path
                    for audio_file, analysis_path in existing_analyses
                    if audio_file == selected_analysis
                ),
                None,
            )

            if selected_file and selected_file.exists():
                content = selected_file.read_text(encoding="utf-8")
                _render_analysis_tabs(selected_analysis, content)


###############################################################################
# Main Streamlit App
###############################################################################


def main() -> None:
    initialise_session_state()

    st.title("NeedleInAVidStack")
    st.write("Bulk process video audio to find specific examples, timestamps, or segments using Google Gen AI.")

    render_prompt_input()
    render_api_configuration()
    render_video_to_audio()
    render_audio_analysis()
    render_analysis_viewer()


if __name__ == "__main__":
    if "__streamlitmagic__" not in globals():
        import streamlit.web.bootstrap

        streamlit.web.bootstrap.run(
            __file__,
            is_hello=False,
            args=[],
            flag_options={},
            main=main,
        )
    else:
        main()
