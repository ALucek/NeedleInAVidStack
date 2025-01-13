import os
import base64
import pathlib
import glob

# Vertex AI imports
import vertexai
from vertexai.generative_models import GenerativeModel as VertexGenerativeModel
from vertexai.generative_models import GenerationConfig, Part

# Gemini API imports
import google.generativeai as genai


def analyze_with_vertex_ai(
    audio_path,
    prompt,
    credentials_path,
    project_id,
    location,
    model_name
):
    """
    Analyzes audio using Vertex AI (Google Cloud).
    """
    try:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        vertexai.init(project=project_id, location=location)
        model = VertexGenerativeModel(model_name)

        with open(audio_path, "rb") as audio_file:
            audio_data = base64.b64encode(audio_file.read())

        # Build the audio Part
        audio_part = Part.from_data(
            data=base64.b64decode(audio_data),
            mime_type="audio/mpeg"  # or audio/mp3
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
    except Exception as e:
        raise RuntimeError(f"Vertex AI analysis error: {e}")


def analyze_with_gemini_api(audio_path, prompt, api_key, model_name):
    """
    Analyzes audio using Gemini API.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        audio_bytes = pathlib.Path(audio_path).read_bytes()
        response = model.generate_content([
            prompt,
            {
                "mime_type": "audio/mp3",  # or audio/mpeg
                "data": audio_bytes
            }
        ])
        return response.text
    except Exception as e:
        raise RuntimeError(f"Gemini API analysis error: {e}")

def load_existing_analysis(audio_file):
    """
    Load existing analysis file for a given audio file if it exists.
    
    Args:
        audio_file (str): Path to the audio file
        
    Returns:
        tuple: (bool, str) - (exists, content)
    """
    analysis_path = f"output/analysis/{os.path.basename(audio_file).replace('.mp3', '_analysis.txt')}"
    if os.path.exists(analysis_path):
        with open(analysis_path, 'r', encoding='utf-8') as f:
            return True, f.read()
    return False, None

def get_all_existing_analyses():
    """
    Find all existing analysis files in the output/analysis directory.
    
    Returns:
        list: List of tuples (audio_filename, analysis_path)
    """
    analyses = []
    if os.path.exists("output/analysis"):
        for analysis_file in glob.glob("output/analysis/*_analysis.txt"):
            audio_filename = os.path.basename(analysis_file).replace('_analysis.txt', '.mp3')
            analyses.append((audio_filename, analysis_file))
    return analyses