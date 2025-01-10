import os
from moviepy import VideoFileClip
from pydub import AudioSegment

def ensure_directories():
    """
    Ensure that both audio and analysis output directories exist.
    
    Returns:
        tuple: (audio_dir, analysis_dir)
    """
    audio_dir = "output/audio"
    analysis_dir = "output/analysis"
    
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(analysis_dir, exist_ok=True)
    
    return audio_dir, analysis_dir


def video_to_audio(video_path, max_size_mb=15):
    """
    Convert video to audio (MP3) and ensure the output is under the specified size limit.
    Saves the result in the 'output/audio/' subdirectory.
    
    Args:
        video_path (str): Path to input video file.
        max_size_mb (int): Maximum size in megabytes for the output audio.
    
    Returns:
        str | None: Path to the processed audio file (MP3) or None if there's an error.
    """
    audio_dir, _ = ensure_directories()
    
    # Extract base filename without extension
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    temp_audio = os.path.join(audio_dir, f"{base_name}_temp.wav")
    final_audio = os.path.join(audio_dir, f"{base_name}.mp3")
    
    # If the final file already exists, optionally skip re-conversion:
    if os.path.isfile(final_audio):
        print(f"Audio file already exists for {video_path}, skipping conversion.")
        return final_audio
    
    # Convert video to audio
    try:
        video = VideoFileClip(video_path)
        if not video.audio:
            print(f"No audio track found in {video_path}.")
            return None
        video.audio.write_audiofile(temp_audio)
        video.close()
    except Exception as e:
        print(f"Error extracting audio from {video_path}: {e}")
        return None
    
    # Convert to MP3 with size management
    try:
        audio = AudioSegment.from_file(temp_audio, format="wav")
        current_size = os.path.getsize(temp_audio) / (1024 * 1024)  # MB

        if current_size <= max_size_mb:
            audio.export(final_audio, format="mp3", bitrate="192k")
        else:
            # Calculate required bitrate to meet size limit
            duration_s = len(audio) / 1000
            target_bitrate = int((max_size_mb * 8192) / duration_s)  # kbps
            bitrate = max(32, min(192, target_bitrate))
            audio.export(final_audio, format="mp3", bitrate=f"{bitrate}k")
    except Exception as e:
        print(f"Error processing audio file {temp_audio}: {e}")
        return None
    finally:
        # Clean up temporary file if it exists
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
    
    return final_audio


def process_videos_in_directory(directory):
    """
    Process all videos in a directory, converting them to MP3.
    
    Args:
        directory (str): Path to directory containing videos
        
    Returns:
        list: Paths to processed audio files
    """
    import os
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv')
    processed_audio_files = []
    
    if not os.path.isdir(directory):
        print(f"Invalid directory: {directory}")
        return []
    
    for filename in os.listdir(directory):
        if filename.lower().endswith(video_extensions):
            video_path = os.path.join(directory, filename)
            print(f"Processing {filename}...")
            output_path = video_to_audio(video_path)
            if output_path:
                processed_audio_files.append(output_path)
                print(f"Created audio file: {output_path}")
            else:
                print(f"Failed to process {filename}")
    
    return processed_audio_files