import os
import glob
import streamlit as st

# Local imports
from video_processing import process_videos_in_directory
from app_utils import (
    should_skip_analysis,
    save_analysis
    # show_progress_bar  # No longer used
)
from analysis_utils import (
    analyze_with_vertex_ai,
    analyze_with_gemini_api
)


##############################################################################
# Constants and Defaults
##############################################################################
DEFAULT_PROMPT = """
Analyze this audio for specific examples of [target topic] - these are instances where [explain what you're looking for]. 

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

If no clear examples are found, simply state that.
"""

DEFAULT_MODEL = "gemini-1.5-flash-002"
DEFAULT_GCP_PROJECT = "my-gcp-project"
DEFAULT_GCP_LOCATION = "us-east1"


##############################################################################
# Helper Functions
##############################################################################
def analyze_audio(
    audio_path,
    prompt,
    api_choice,
    credentials,
    model_name=DEFAULT_MODEL,
    project_id=DEFAULT_GCP_PROJECT,
    location=DEFAULT_GCP_LOCATION
):
    """
    Analyzes audio using the selected API and returns text.
    """
    if api_choice == "Vertex AI":
        response_text = analyze_with_vertex_ai(
            audio_path,
            prompt,
            credentials_path=credentials,
            project_id=project_id,
            location=location,
            model_name=model_name
        )
    else:
        # Gemini API
        response_text = analyze_with_gemini_api(
            audio_path,
            prompt,
            api_key=credentials,
            model_name=model_name
        )
    return response_text


def get_gemini_api_key_from_secrets():
    """
    Safely retrieve the GEMINI_API_KEY from Streamlit secrets if it exists.
    If secrets.toml doesn't exist or doesn't contain GEMINI_API_KEY, return None.
    """
    if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
        return st.secrets["GEMINI_API_KEY"]
    return None


def get_vertex_secrets():
    """
    Safely retrieve Vertex AI secrets from Streamlit secrets if they exist.
    Returns a dict with keys: project_id, location, credentials_file (or empty).
    """
    if "vertex_ai" in st.secrets:
        return {
            "project_id": st.secrets["vertex_ai"].get("project_id", DEFAULT_GCP_PROJECT),
            "location": st.secrets["vertex_ai"].get("location", DEFAULT_GCP_LOCATION),
            "credentials_file": st.secrets["vertex_ai"].get("credentials_file", "./gcp_credentials.json")
        }
    else:
        return {
            "project_id": DEFAULT_GCP_PROJECT,
            "location": DEFAULT_GCP_LOCATION,
            "credentials_file": "./gcp_credentials.json"
        }


##############################################################################
# UI Sections
##############################################################################
def render_prompt_input():
    with st.expander("Prompt Configuration", expanded=True):
        # Initialize session state if not present
        if "analysis_prompt" not in st.session_state:
            st.session_state.analysis_prompt = DEFAULT_PROMPT

        st.write("Customize the analysis prompt below. Use the button to reset it to the default template.")

        if st.button("Reset to Default Prompt"):
            st.session_state.analysis_prompt = DEFAULT_PROMPT

        st.session_state.analysis_prompt = st.text_area(
            "Analysis Prompt:",
            value=st.session_state.analysis_prompt,
            height=250
        )


def render_api_configuration():
    with st.expander("API Configuration", expanded=True):
        api_choice = st.radio(
            "Choose API:",
            ["Gemini API", "Vertex AI"],
            help="Select which API to use for analysis."
        )
        
        model_name = st.text_input("Model Name:", value=DEFAULT_MODEL)

        st.write("---")
        st.markdown("#### Credentials")
        
        if api_choice == "Gemini API":
            # Check if there's a secrets-based API key
            gemini_secrets_key = get_gemini_api_key_from_secrets()
            if gemini_secrets_key:
                st.info("Using GEMINI_API_KEY from secrets.toml.")
                credentials = gemini_secrets_key
            else:
                credentials = st.text_input("Gemini API Key:", type="password", help="Enter your Gemini API key")

            project_id = None
            location = None

        else:
            # Vertex AI
            vertex_info = get_vertex_secrets()  # fetch defaults or secrets-based
            col1, col2 = st.columns(2)
            with col1:
                project_id = st.text_input("GCP Project ID:", value=vertex_info["project_id"])
            with col2:
                location = st.text_input("GCP Location:", value=vertex_info["location"])

            credentials = st.text_input(
                "Path to GCP Service Account JSON:",
                value=vertex_info["credentials_file"],
                help="Enter path to your GCP service account credentials JSON file"
            )

        # Store them in session state
        st.session_state.api_choice = api_choice
        st.session_state.credentials = credentials
        st.session_state.project_id = project_id
        st.session_state.location = location
        st.session_state.model_name = model_name


def render_video_to_audio():
    with st.expander("Video to Audio Conversion", expanded=True):
        video_folder = st.text_input("Video Folder Path:", "./videos",
                                     help="Enter the path to a folder with video files")
        
        if "processed_audio_files" not in st.session_state:
            st.session_state.processed_audio_files = []

        if st.button("Convert Videos to Audio"):
            if os.path.isdir(video_folder):
                with st.spinner("Converting videos to audio..."):
                    audio_files = process_videos_in_directory(video_folder)
                    st.session_state.processed_audio_files = audio_files
                
                if st.session_state.processed_audio_files:
                    st.success(f"Converted {len(st.session_state.processed_audio_files)} videos to audio.")
                else:
                    st.warning("No videos were converted. Check logs for details.")
            else:
                st.error("Invalid folder path. Please enter a valid directory.")


def render_audio_analysis():
    with st.expander("Analyze Audio Files", expanded=True):
        skip_reanalysis = st.checkbox("Skip re-analysis if file already exists?", value=True)

        if st.button("Run Analysis"):
            # Check if any audio files are in session state
            if not st.session_state.processed_audio_files:
                st.warning("No audio files found in session state. Checking output/audio folder instead.")
                
                # Attempt to load existing audio from 'output/audio'
                existing_audio_files = glob.glob("output/audio/*.mp3")
                st.session_state.processed_audio_files = existing_audio_files

            audio_files = st.session_state.processed_audio_files
            if not audio_files:
                st.warning("No audio files found to analyze. Please convert videos or ensure .mp3 files exist.")
                return

            # Check credentials
            if not st.session_state.credentials:
                if st.session_state.api_choice == "Vertex AI":
                    st.error("Please provide path to your GCP credentials JSON file.")
                else:
                    st.error("Please provide your Gemini API key.")
                return

            st.write(f"**Starting analysis for {len(audio_files)} audio files...**")
            for audio_file in audio_files:
                if skip_reanalysis and should_skip_analysis(audio_file, skip_reanalysis=True):
                    st.info(f"Skipping re-analysis for `{os.path.basename(audio_file)}` (analysis file exists).")
                    continue

                st.write(f"Analyzing: `{os.path.basename(audio_file)}`")
                try:
                    response_text = analyze_audio(
                        audio_file,
                        st.session_state.analysis_prompt,
                        st.session_state.api_choice,
                        st.session_state.credentials,
                        model_name=st.session_state.model_name,
                        project_id=st.session_state.project_id,
                        location=st.session_state.location
                    )
                    save_analysis(audio_file, response_text)
                    
                    st.write("**Analysis Result:**")
                    st.text_area(
                        label=f"Analysis for {os.path.basename(audio_file)}",
                        value=response_text,
                        height=200
                    )
                    st.success(f"Saved analysis to output/analysis/{os.path.basename(audio_file).replace('.mp3', '_analysis.txt')}")
                except Exception as e:
                    st.error(f"Failed to analyze {audio_file}. Error: {str(e)}")

            st.success("Analysis complete!")


##############################################################################
# Main Streamlit App
##############################################################################
def main():
    st.title("NeedleInAVidStack")
    st.write(
        "Bulk process video audio to find specific examples, timestamps, or segments "
        "based on semantic descriptions via Google Gemini or Vertex AI."
    )

    # Render UI sections
    render_prompt_input()
    render_api_configuration()
    render_video_to_audio()
    render_audio_analysis()


if __name__ == "__main__":
    # UV run snippet
    if "__streamlitmagic__" not in locals():
        import streamlit.web.bootstrap
        streamlit.web.bootstrap.run(__file__, False, [], {})
    main()