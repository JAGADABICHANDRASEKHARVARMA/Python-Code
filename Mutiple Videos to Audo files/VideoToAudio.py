import subprocess
import os
from tqdm import tqdm
import time
import argparse
from pathlib import Path

def get_video_duration(video_path):
    """Get the duration of the video in seconds."""
    cmd = [
        'ffprobe', 
        '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        video_path
    ]
    try:
        output = subprocess.check_output(cmd).decode('utf-8').strip()
        return float(output)
    except subprocess.CalledProcessError:
        print(f"Error getting duration for {video_path}")
        return 0

def extract_audio(video_path, output_path, audio_format='mp3', audio_bitrate='192k'):
    """
    Extract audio from video file using FFmpeg.
    
    Parameters:
    - video_path: Path to input video file
    - output_path: Path for output audio file
    - audio_format: Output audio format (mp3, aac, wav, etc.)
    - audio_bitrate: Audio quality bitrate
    
    Returns:
    - Boolean indicating success
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Get video duration for progress tracking
    duration = get_video_duration(video_path)
    if duration == 0:
        return False
    
    # Prepare FFmpeg command
    codec_map = {
        'mp3': 'libmp3lame',
        'aac': 'aac',
        'wav': 'pcm_s16le',
        'flac': 'flac',
        'ogg': 'libvorbis'
    }
    
    codec = codec_map.get(audio_format, audio_format)
    
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vn',  # No video
        '-acodec', codec,
        '-ab', audio_bitrate,
        '-ar', '44100',  # Sample rate
        '-y',  # Overwrite output file if it exists
        output_path
    ]
    
    # Start the process
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    # Setup progress bar
    pbar = tqdm(total=100, desc=f"Extracting {os.path.basename(video_path)}", unit="%")
    
    # Track progress
    last_progress = 0
    while process.poll() is None:
        # Read error output for progress info
        line = process.stderr.readline()
        if 'time=' in line:
            # Extract current time
            time_parts = line.split('time=')[1].split()[0].split(':')
            if len(time_parts) == 3:
                hours, minutes, seconds = time_parts
                # Handle case where seconds might have a decimal part
                seconds = seconds.split('.')[0] if '.' in seconds else seconds
                try:
                    current_time = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
                    progress = min(int((current_time / duration) * 100), 100)
                    
                    # Update progress bar
                    if progress > last_progress:
                        pbar.update(progress - last_progress)
                        last_progress = progress
                except ValueError:
                    pass  # Skip if we can't parse the time properly
        
        time.sleep(0.1)
    
    pbar.close()
    
    # Check if extraction was successful
    if process.returncode != 0:
        print(f"Error extracting audio from {video_path}:")
        print(process.stderr.read())
        return False
    
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✓ Successfully extracted audio to: {output_path} ({file_size_mb:.2f} MB)")
    return True

def process_video_folder(input_folder, output_folder, audio_format='mp3', audio_bitrate='192k'):
    """
    Process all video files in a folder and extract audio from each.
    
    Parameters:
    - input_folder: Path to folder containing video files
    - output_folder: Path to folder where audio files will be saved
    - audio_format: Output audio format
    - audio_bitrate: Audio quality bitrate
    """
    # Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Define common video file extensions
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp']
    
    # Get all video files in the input folder
    video_files = []
    for root, _, files in os.walk(input_folder):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_files.append(os.path.join(root, file))
    
    if not video_files:
        print(f"No video files found in {input_folder}")
        return
    
    print(f"Found {len(video_files)} video files to process")
    
    # Process each video file
    successful = 0
    failed = 0
    
    for i, video_path in enumerate(video_files):
        print(f"\nProcessing video {i+1}/{len(video_files)}: {os.path.basename(video_path)}")
        
        # Create output filename
        rel_path = os.path.relpath(video_path, input_folder)
        output_path = os.path.join(output_folder, os.path.splitext(rel_path)[0] + f".{audio_format}")
        
        # Ensure output directory for this file exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Extract audio
        if extract_audio(video_path, output_path, audio_format, audio_bitrate):
            successful += 1
        else:
            failed += 1
    
    print(f"\nExtraction complete!")
    print(f"Successful extractions: {successful}")
    print(f"Failed extractions: {failed}")
    print(f"Output folder: {os.path.abspath(output_folder)}")

def main():
    parser = argparse.ArgumentParser(description='Extract audio from video files')
    parser.add_argument('--input', '-i', required=True, help='Input folder containing video files')
    parser.add_argument('--output', '-o', required=True, help='Output folder for audio files')
    parser.add_argument('--format', '-f', default='mp3', choices=['mp3', 'wav', 'aac', 'flac', 'ogg'], 
                        help='Audio format (default: mp3)')
    parser.add_argument('--bitrate', '-b', default='192k', help='Audio bitrate (default: 192k)')
    
    args = parser.parse_args()
    
    process_video_folder(args.input, args.output, args.format, args.bitrate)

if __name__ == "__main__":
    # If no arguments provided, use the example with input prompts
    if len(os.sys.argv) == 1:
        print("No command line arguments provided. Running in interactive mode.")
        input_folder = input("Enter the path to your folder containing video files: ")
        output_folder = input("Enter the path where audio files should be saved: ")
        audio_format = input("Enter the desired audio format (mp3, wav, aac, flac, ogg) [default: mp3]: ") or "mp3"
        audio_bitrate = input("Enter the desired audio bitrate [default: 192k]: ") or "192k"
        
        process_video_folder(input_folder, output_folder, audio_format, audio_bitrate)
    else:
        main()
