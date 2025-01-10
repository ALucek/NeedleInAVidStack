from moviepy import VideoFileClip
from pydub import AudioSegment
import os

def ensure_directories():
    """
    Ensure that both audio and analysis output directories exist.
    
    Returns:
        tuple: Paths to audio and analysis directories
    """
    audio_dir = "output/audio"
    analysis_dir = "output/analysis"
    
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(analysis_dir, exist_ok=True)
    
    return audio_dir, analysis_dir

def video_to_audio(video_path, max_size_mb=15):
    """
    Convert video to audio and ensure the output is under the specified size limit.
    Saves the result in the 'output/audio/' subdirectory.
    
    Args:
        video_path (str): Path to input video file.
        max_size_mb (int): Maximum size in megabytes for the output audio.
    
    Returns:
        str: Path to the processed audio file (MP3).
    """
    audio_dir, _ = ensure_directories()
    
    # Extract base filename without extension
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    temp_audio = os.path.join(audio_dir, f"{base_name}_temp.wav")
    final_audio = os.path.join(audio_dir, f"{base_name}.mp3")
    
    # Convert video to audio
    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(temp_audio)
        video.close()
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return None
    
    # Convert to MP3 with size management
    audio = AudioSegment.from_wav(temp_audio)
    
    # Calculate current size in MB
    current_size = os.path.getsize(temp_audio) / (1024 * 1024)
    
    # If size is already OK, just convert to MP3
    if current_size <= max_size_mb:
        audio.export(final_audio, format="mp3", bitrate="192k")
    else:
        # Calculate required bitrate to meet size limit
        duration_s = len(audio) / 1000
        target_bitrate = int((max_size_mb * 8192) / duration_s)  # Convert to kbps
        bitrate = max(32, min(192, target_bitrate))
        audio.export(final_audio, format="mp3", bitrate=f"{bitrate}k")
    
    # Clean up temporary file
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
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv')
    processed_audio_files = []
    
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