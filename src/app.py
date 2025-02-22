import os
import glob
import streamlit as st

# Local imports
from video_processing import process_videos_in_directory
from app_utils import should_skip_analysis, save_analysis
from analysis_utils import (
    analyze_audio_with_genai,
    initialize_genai_client,
    load_existing_analysis,
    get_all_existing_analyses
)

##############################################################################
# Constants and Defaults
##############################################################################
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


##############################################################################
# UI Sections
##############################################################################
def render_prompt_input():
    with st.expander("Prompt Configuration", expanded=True):
        if "analysis_prompt" not in st.session_state:
            st.session_state.analysis_prompt = DEFAULT_PROMPT

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
            credentials = st.text_input("Gemini API Key:", type="password", help="Enter your Gemini API key")
            project_id = None
            location = None
        else:
            col1, col2 = st.columns(2)
            with col1:
                project_id = st.text_input("GCP Project ID:", value=DEFAULT_GCP_PROJECT)
            with col2:
                location = st.text_input("GCP Location:", value=DEFAULT_GCP_LOCATION)

            credentials = st.text_input(
                "Path to GCP Service Account JSON:",
                value="./gcp_credentials.json",
                help="Enter path to your GCP service account credentials JSON file"
            )

        st.session_state.api_choice = api_choice
        st.session_state.credentials = credentials
        st.session_state.project_id = project_id
        st.session_state.location = location
        st.session_state.model_name = model_name


def render_video_to_audio():
    with st.expander("Video to Audio Conversion", expanded=True):
        video_folder = st.text_input("Video Folder Path:", "./videos")

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
                    st.warning("No videos were converted.")
            else:
                st.error("Invalid folder path. Please enter a valid directory.")


def render_audio_analysis():
    with st.expander("Analyze Audio Files", expanded=True):
        skip_reanalysis = st.checkbox("Skip re-analysis if file already exists?", value=True)
        
        # Always check for existing audio files on disk
        existing_audio_files = glob.glob("output/audio/*.mp3")
        st.session_state.processed_audio_files = existing_audio_files if existing_audio_files else []
        
        if st.button("Run Analysis"):
            audio_files = st.session_state.processed_audio_files
            if not audio_files:
                st.warning("No audio files found to analyze.")
                return

            if not st.session_state.credentials:
                st.error("Please provide your API key or GCP credentials JSON file.")
                return

            client = initialize_genai_client(
                st.session_state.api_choice,
                st.session_state.credentials,
                st.session_state.project_id,
                st.session_state.location
            )

            st.markdown("### Starting Analysis")
            for audio_file in audio_files:
                if skip_reanalysis and should_skip_analysis(audio_file, skip_reanalysis=True):
                    st.info(f"Skipping `{os.path.basename(audio_file)}` (analysis file exists).")
                    exists, content = load_existing_analysis(audio_file)
                    if exists:
                        st.markdown("---")
                        st.markdown(f"#### Existing Analysis: `{os.path.basename(audio_file)}`")
                        raw_tab, rendered_tab = st.tabs(["Raw Text", "Rendered Markdown"])
                        with raw_tab:
                            st.text_area(
                                label="Raw analysis",
                                value=content,
                                height=200
                            )
                        with rendered_tab:
                            st.markdown(content)
                    continue
                
                st.markdown("---")
                st.markdown(f"#### Analyzing: `{os.path.basename(audio_file)}`")
                try:
                    response_text = analyze_audio_with_genai(
                        audio_file,
                        st.session_state.analysis_prompt,
                        client,
                        st.session_state.model_name
                    )
                    save_analysis(audio_file, response_text)

                    raw_tab, rendered_tab = st.tabs(["Raw Text", "Rendered Markdown"])
                    with raw_tab:
                        st.text_area("Raw analysis", value=response_text, height=200)
                    with rendered_tab:
                        st.markdown(response_text)

                    st.success(f"Saved analysis for `{os.path.basename(audio_file)}`")
                except Exception as e:
                    st.error(f"Failed to analyze {audio_file}. Error: {str(e)}")

            st.success("Analysis complete!")


def render_analysis_viewer():
    """
    Renders a viewer for existing analysis files.
    """
    with st.expander("View Existing Analyses", expanded=True):
        existing_analyses = get_all_existing_analyses()
        
        if not existing_analyses:
            st.info("No existing analysis files found in output/analysis directory.")
            return
            
        st.write(f"Found {len(existing_analyses)} existing analysis files.")
        
        # Create a selectbox for choosing which analysis to view
        analysis_options = ["Select an analysis..."] + [audio_file for audio_file, _ in existing_analyses]
        selected_analysis = st.selectbox("Choose an analysis to view:", analysis_options)
        
        if selected_analysis and selected_analysis != "Select an analysis...":
            selected_file = next(
                (analysis_path for audio_file, analysis_path in existing_analyses 
                 if audio_file == selected_analysis),
                None
            )
            
            if selected_file:
                with open(selected_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                raw_tab, rendered_tab = st.tabs(["Raw Text", "Rendered Markdown"])
                with raw_tab:
                    st.text_area(
                        label=f"Raw analysis for {selected_analysis}",
                        value=content,
                        height=300
                    )
                with rendered_tab:
                    st.markdown(content)


##############################################################################
# Main Streamlit App
##############################################################################
def main():
    st.title("NeedleInAVidStack")
    st.write("Bulk process video audio to find specific examples, timestamps, or segments using Google Gen AI.")

    render_prompt_input()
    render_api_configuration()
    render_video_to_audio()
    render_audio_analysis()
    render_analysis_viewer()


if __name__ == "__main__":
    # UV run snippet
    if "__streamlitmagic__" not in locals():
        import streamlit.web.bootstrap
        streamlit.web.bootstrap.run(__file__, False, [], {})
    main()