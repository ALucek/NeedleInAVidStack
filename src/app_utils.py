import os
import streamlit as st
from video_processing import ensure_directories

def should_skip_analysis(audio_file, skip_flag):
    """
    Check if analysis file already exists and whether we should skip re-analysis.
    
    Args:
        audio_file (str): Path to the MP3 file
        skip_flag (bool): If True, skip analysis if file exists
    
    Returns:
        bool: True if we should skip analysis, False otherwise
    """
    base_name = os.path.splitext(os.path.basename(audio_file))[0]
    _, analysis_dir = ensure_directories()
    analysis_file = os.path.join(analysis_dir, f"{base_name}_analysis.txt")
    
    if skip_flag and os.path.isfile(analysis_file):
        # Analysis file already exists, skip
        return True
    
    return False


def save_analysis(audio_file, text):
    """
    Save the analysis text to the appropriate file in the 'analysis' directory.
    
    Args:
        audio_file (str): Original audio file
        text (str): Text to save
    """
    base_name = os.path.splitext(os.path.basename(audio_file))[0]
    _, analysis_dir = ensure_directories()
    analysis_file = os.path.join(analysis_dir, f"{base_name}_analysis.txt")
    with open(analysis_file, "w", encoding="utf-8") as f:
        f.write(text)


def show_progress_bar(i, total, label="Processing"):
    """
    Display or update a progress bar in Streamlit.
    
    Args:
        i (int): Current index (1-based)
        total (int): Total items
        label (str): Label for the progress bar
    """
    fraction = i / total if total else 1.0
    st.progress(fraction, text=f"{label}: {i}/{total}")
