"""Utilities for turning videos into audio clips."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from moviepy.editor import VideoFileClip
from pydub import AudioSegment

from paths import AUDIO_DIR, ensure_output_dirs

# Supported video file extensions.
VIDEO_EXTENSIONS: tuple[str, ...] = (".mp4", ".avi", ".mov", ".mkv")


def _iter_video_files(directory: Path) -> Iterable[Path]:
    for path in directory.iterdir():
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            yield path


def video_to_audio(video_path: str | Path, max_size_mb: int = 15) -> str | None:
    """Convert *video_path* into an MP3 file saved in :data:`AUDIO_DIR`."""

    ensure_output_dirs()
    source = Path(video_path)
    base_name = source.stem

    temp_audio = AUDIO_DIR / f"{base_name}_temp.wav"
    final_audio = AUDIO_DIR / f"{base_name}.mp3"

    if final_audio.exists():
        print(f"Audio file already exists for {source}, skipping conversion.")
        return str(final_audio)

    try:
        with VideoFileClip(str(source)) as clip:
            if clip.audio is None:
                print(f"No audio track found in {source}.")
                return None
            clip.audio.write_audiofile(str(temp_audio), logger=None)
    except Exception as exc:  # pragma: no cover - moviepy raises many runtime errors
        print(f"Error extracting audio from {source}: {exc}")
        return None

    try:
        audio = AudioSegment.from_file(temp_audio, format="wav")
        current_size = temp_audio.stat().st_size / (1024 * 1024)

        if current_size <= max_size_mb:
            audio.export(final_audio, format="mp3", bitrate="192k")
        else:
            duration_s = len(audio) / 1000
            target_bitrate = int((max_size_mb * 8192) / duration_s)
            bitrate = max(32, min(192, target_bitrate))
            audio.export(final_audio, format="mp3", bitrate=f"{bitrate}k")
    except Exception as exc:  # pragma: no cover - depends on external codecs
        print(f"Error processing audio file {temp_audio}: {exc}")
        return None
    finally:
        if temp_audio.exists():
            temp_audio.unlink()

    return str(final_audio)


def process_videos_in_directory(directory: str | Path) -> List[str]:
    """Convert every supported video inside *directory* to audio."""

    directory_path = Path(directory)
    if not directory_path.is_dir():
        print(f"Invalid directory: {directory}")
        return []

    processed_audio_files: List[str] = []

    for video_file in sorted(_iter_video_files(directory_path)):
        print(f"Processing {video_file.name}...")
        output_path = video_to_audio(video_file)
        if output_path:
            processed_audio_files.append(output_path)
            print(f"Created audio file: {output_path}")
        else:
            print(f"Failed to process {video_file.name}")

    return processed_audio_files
