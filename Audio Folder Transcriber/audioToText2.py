import speech_recognition as sr
from pydub import AudioSegment
import math
import os

def convert_to_wav(input_file, output_file="temp.wav"):
    """Convert audio file to WAV format."""
    try:
        audio = AudioSegment.from_file(input_file)
        audio.export(output_file, format="wav")
        return output_file
    except Exception as e:
        raise Exception(f"Error converting audio: {str(e)}")

def transcribe_audio(audio_path, chunk_duration=30):
    """
    Transcribe audio file in chunks to handle longer files.
    Parameters:
    audio_path: Path to the audio file
    chunk_duration: Duration of each chunk in seconds
    """
    # Initialize recognizer
    recognizer = sr.Recognizer()
    
    # Load audio file
    audio = AudioSegment.from_wav(audio_path)
    
    # Calculate duration and chunks
    duration = len(audio) / 1000  # Convert to seconds
    chunks = math.ceil(duration / chunk_duration)
    
    full_transcript = []
    
    for i in range(chunks):
        # Extract chunk
        start_time = i * chunk_duration * 1000
        end_time = min((i + 1) * chunk_duration * 1000, len(audio))
        chunk = audio[start_time:end_time]
        
        # Export chunk to temporary file
        chunk_path = f"temp_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
        
        # Transcribe chunk
        with sr.AudioFile(chunk_path) as source:
            try:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
                full_transcript.append(text)
                print(f"Processed chunk {i+1}/{chunks}")
            except sr.UnknownValueError:
                print(f"Could not understand audio in chunk {i+1}")
            except sr.RequestError as e:
                print(f"Error with the speech recognition service in chunk {i+1}: {str(e)}")
                
        # Clean up temporary chunk file
        os.remove(chunk_path)
        
    return " ".join(full_transcript)

def main():
    # Get input folder path
    input_folder = input("Enter the path to your folder containing audio files: ")
    
    # Get list of audio files
    audio_files = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]
    
    # Filter audio files (common audio extensions)
    audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma']
    audio_files = [f for f in audio_files if os.path.splitext(f.lower())[1] in audio_extensions]
    
    if not audio_files:
        print("No audio files found in the specified folder.")
        return
    
    # Output transcript file
    output_file = os.path.join(input_folder, "combined_transcript.txt")
    
    # Process each audio file
    all_transcripts = []
    
    for i, audio_file in enumerate(audio_files):
        print(f"\nProcessing file {i+1}/{len(audio_files)}: {audio_file}")
        full_path = os.path.join(input_folder, audio_file)
        
        try:
            # Convert to WAV if needed
            wav_file = convert_to_wav(full_path)
            
            # Add file name to transcript
            file_transcript = f"\n\n--- TRANSCRIPT FOR: {audio_file} ---\n\n"
            
            # Perform transcription
            transcript = transcribe_audio(wav_file)
            file_transcript += transcript
            
            # Add to collection of all transcripts
            all_transcripts.append(file_transcript)
            
            print(f"Transcription completed for {audio_file}")
            
        except Exception as e:
            print(f"An error occurred with {audio_file}: {str(e)}")
            
        finally:
            # Clean up temporary WAV file if it was created
            if wav_file != full_path and os.path.exists(wav_file):
                os.remove(wav_file)
    
    # Save all transcripts to a single file
    with open(output_file, "w") as f:
        f.write("\n".join(all_transcripts))
    
    print(f"\nAll transcriptions completed! Combined transcript saved to {output_file}")

if __name__ == "__main__":
    main()