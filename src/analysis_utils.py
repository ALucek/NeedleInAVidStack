import os
import json
import glob
from google import genai
from google.genai import types
from google.oauth2 import service_account

##############################################################################
# Initialize Gen AI Client
##############################################################################

def initialize_genai_client(api_choice, credentials, project_id, location):
    """
    Initializes the Google Gen AI client for Gemini API or Vertex AI.
    """
    if api_choice == "Vertex AI":
        if not credentials or not os.path.exists(credentials):
            raise RuntimeError("Invalid GCP credentials file path. Please check your input.")

        try:
            gcp_credentials = service_account.Credentials.from_service_account_file(credentials).with_scopes(
                ["https://www.googleapis.com/auth/cloud-platform"]
            )
            return genai.Client(
                vertexai=True,
                project=project_id,
                location=location,
                credentials=gcp_credentials
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load GCP credentials: {e}")

    elif api_choice == "Gemini API":
        if not credentials:
            raise RuntimeError("Gemini API key is missing. Please enter your API key.")
        return genai.Client(api_key=credentials)

    else:
        raise RuntimeError("Invalid API selection. Choose 'Gemini API' or 'Vertex AI'.")

##############################################################################
# Analyze Audio
##############################################################################

def analyze_audio_with_genai(audio_path, prompt, client, model_name):
    """
    Analyzes an audio file using Google Gen AI SDK.
    """
    try:
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()

        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/mpeg")

        response = client.models.generate_content(model=model_name, contents=[audio_part, prompt])

        return response.text.strip()
    except Exception as e:
        raise RuntimeError(f"Gen AI analysis error: {e}")
    
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