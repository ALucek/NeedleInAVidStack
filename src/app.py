import streamlit as st
import os
import base64
import pathlib

# Vertex AI imports
import vertexai
from vertexai.generative_models import GenerativeModel as VertexGenerativeModel
from vertexai.generative_models import GenerationConfig, Part

# Gemini API imports
import google.generativeai as genai

# Local imports
from video_processing import process_videos_in_directory, ensure_directories

##############################################################################
# Constants and Config
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

# Default GCP settings
DEFAULT_PROJECT = "gcp-project-12345"
DEFAULT_LOCATION = "us-east1"
DEFAULT_MODEL = "gemini-1.5-flash-002"

##############################################################################
# LLM Functions
##############################################################################
def analyze_with_vertex_ai(audio_path, prompt, credentials_path, project_id, location, model_name):
    """
    Analyzes audio using Vertex AI (Google Cloud).
    """
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    vertexai.init(project=project_id, location=location)
    model = VertexGenerativeModel(model_name)

    with open(audio_path, "rb") as audio_file:
        audio_data = base64.b64encode(audio_file.read())

    audio_part = Part.from_data(
        data=base64.b64decode(audio_data),
        mime_type="audio/mpeg"
    )

    generation_config = GenerationConfig(
        temperature=0.2,
        audio_timestamp=True
    )
    
    response = model.generate_content(
        [audio_part, prompt],
        generation_config=generation_config,
    )

    return response.text.strip()

def analyze_with_gemini_api(audio_path, prompt, api_key):
    """
    Analyzes audio using Gemini API.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    audio_bytes = pathlib.Path(audio_path).read_bytes()
    response = model.generate_content([
        prompt,
        {
            "mime_type": "audio/mp3",
            "data": audio_bytes
        }
    ])
    
    return response.text

def analyze_audio(audio_path, prompt, api_choice, credentials, **kwargs):
    """
    Analyzes audio using the selected API and saves results.
    """
    try:
        if api_choice == "Vertex AI":
            response_text = analyze_with_vertex_ai(
                audio_path, 
                prompt, 
                credentials,
                kwargs.get('project_id'),
                kwargs.get('location'),
                kwargs.get('model_name')
            )
        else:  # Gemini API
            response_text = analyze_with_gemini_api(audio_path, prompt, credentials)
        
        # Save analysis to file
        _, analysis_dir = ensure_directories()
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        analysis_file = os.path.join(analysis_dir, f"{base_name}_analysis.txt")
        
        with open(analysis_file, "w") as f:
            f.write(response_text)
            
        return response_text
        
    except Exception as e:
        raise Exception(f"Analysis failed: {str(e)}")

##############################################################################
# Streamlit App
##############################################################################
def main():
    st.title("NeedleInAVidStack")
    st.write(
        "Bulk process video audio to find specific examples, timestamps, or segments based on semantic descriptions via Google Gemini's Audio LLM processing."
    )
    st.write(
        "Created by [Adam Łucek](https://lucek.ai), see source code in the [GitHub Repo](https://github.com/ALucek/NeedleInAVidStack)."
    )
    
    st.write("---")

    # Analysis prompt input at the top
    st.subheader("Analysis Settings")
    prompt = st.text_area(
        "Customize the analysis prompt (or use default):",
        value=DEFAULT_PROMPT,
        height=300
    )
    st.write("*It is recommended to format the prompt in a Description -> Analysis -> Conclusion format to get the best performance.*")
    st.write("---")

    # API Configuration
    st.subheader("API Configuration")
    api_choice = st.radio(
        "Choose API:",
        ["Gemini API", "Vertex AI"],
        help="Select which API to use for analysis"
    )
    
    # Credential input and configuration based on API choice
    if api_choice == "Vertex AI":
        # Create three columns for GCP settings
        col1, col2 = st.columns(2)
        
        with col1:
            project_id = st.text_input(
                "GCP Project ID:",
                value=DEFAULT_PROJECT,
                help="Enter your Google Cloud project ID"
            )
        
        with col2:
            location = st.text_input(
                "GCP Location:",
                value=DEFAULT_LOCATION,
                help="Enter the GCP region (e.g., us-central1)"
            )
        
        model_name = st.text_input(
            "Model Name:",
            value=DEFAULT_MODEL,
            help="Enter the Vertex AI model name"
        )
        
        credentials = st.text_input(
            "Path to Google Cloud credentials JSON file:",
            value="./gcp_credentials.json",
            help="Enter the path to your Google Cloud service account credentials JSON file"
        )
        
    else:
        credentials = st.text_input(
            "Gemini API Key:",
            type="password",
            help="Enter your Gemini API key"
        )
        model_name = st.text_input(
            "Model Name:",
            value=DEFAULT_MODEL,
            help="Enter the Gemini AI model name"
        )
        # Set default values for Vertex AI params even when not used
        project_id = DEFAULT_PROJECT
        location = DEFAULT_LOCATION
        model_name = DEFAULT_MODEL
    
    st.write("---")
    st.subheader("Video to Audio")

    # Initialize session state for storing processed files
    if 'processed_audio_files' not in st.session_state:
        st.session_state.processed_audio_files = []
    
    # Input for directory path
    video_folder = st.text_input("Enter the path to the folder containing videos", "./videos")
    
    # Process Videos button
    if st.button("Convert Videos to Audio"):
        if os.path.isdir(video_folder):
            with st.spinner("Converting videos to audio..."):
                audio_files = process_videos_in_directory(video_folder)
                st.session_state.processed_audio_files = audio_files
            
            if audio_files:
                st.success(f"Converted {len(audio_files)} videos to audio!")
            else:
                st.error("No valid videos found or audio conversion failed.")
        else:
            st.error("Invalid folder path. Please enter a valid directory.")
    
    st.write("---")
    st.subheader("Audio Processing")
    
    # Process Audio button
    if st.button("Analyze Audio Files"):
        if not credentials:
            st.error(f"Please provide {'credentials file path' if api_choice == 'Vertex AI' else 'API key'}")
            return
            
        if st.session_state.processed_audio_files:
            for audio_file in st.session_state.processed_audio_files:
                st.write(f"**Analyzing** `{os.path.basename(audio_file)}`...")
                with st.spinner(f"Running analysis..."):
                    try:
                        response_text = analyze_audio(
                            audio_file, 
                            prompt, 
                            api_choice, 
                            credentials,
                            project_id=project_id,
                            location=location,
                            model_name=model_name
                        )
                        st.write("**Analysis Result:**")
                        st.text_area(
                            label=f"Analysis for {os.path.basename(audio_file)}",
                            value=response_text,
                            height=300
                        )
                        st.success(f"Analysis saved to output/analysis/{os.path.basename(audio_file).replace('.mp3','_analysis.txt')}")
                    except Exception as e:
                        st.error(f"Failed to analyze {audio_file}. Error: {e}")
        else:
            st.warning("No audio files to analyze. Please convert some videos first.")

if __name__ == "__main__":
    if "__streamlitmagic__" not in locals():
        import streamlit.web.bootstrap
        streamlit.web.bootstrap.run(__file__, False, [], {})
    main()