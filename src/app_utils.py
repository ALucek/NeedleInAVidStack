import os
import streamlit as st
from video_processing import ensure_directories

def should_skip_analysis(audio_file, skip_reanalysis):
    """
    Check if analysis file already exists and whether we should skip re-analysis.
    """
    if not skip_reanalysis:
        return False
    
    import os
    from video_processing import ensure_directories

    base_name = os.path.splitext(os.path.basename(audio_file))[0]
    _, analysis_dir = ensure_directories()
    analysis_file = os.path.join(analysis_dir, f"{base_name}_analysis.txt")
    
    return os.path.isfile(analysis_file)



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
