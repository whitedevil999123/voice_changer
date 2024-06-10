import os
from moviepy.editor import VideoFileClip
import pyttsx3
import subprocess
import speech_recognition as sr
from tkinter import Tk, filedialog
import logging
from translations import translation_dict

# Setup logging
logging.basicConfig(level=logging.INFO)

def dummy_translate_to_hindi(text):
    """
    Translate English text to Hindi using a predefined dictionary.

    Parameters:
    text (str): The input text in English.

    Returns:
    str: The translated text in Hindi.
    """
    def translate_word(word):
        # Look up the word in the translation dictionary
        return translation_dict.get(word.lower(), word)

    translated_words = [translate_word(word) for word in text.split()]
    return ' '.join(translated_words)

# Function to extract audio from video
def extract_audio(video_path, audio_path):
    logging.info("Extracting audio from video...")
    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        logging.info("Audio extracted to %s", audio_path)
    except Exception as e:
        logging.error("Error extracting audio: %s", e)

# Function to transcribe audio using Sphinx
def transcribe_audio(audio_path):
    logging.info("Transcribing audio...")
    try:
        recognizer = sr.Recognizer()
        audio_file = sr.AudioFile(audio_path)

        with audio_file as source:
            audio_data = recognizer.record(source)

        transcript = recognizer.recognize_sphinx(audio_data)
        logging.info("Transcript: %s", transcript)
        return transcript
    except Exception as e:
        logging.error("Error transcribing audio: %s", e)
        return "Transcription failed"

# Function to convert text to speech
def text_to_speech(text, output_path):
    logging.info("Converting text to speech...")
    engine = pyttsx3.init()
    try:
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.9)
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        logging.info("Text converted to speech successfully. Output file: %s", output_path)
        return True
    except Exception as e:
        logging.error("Error converting text to speech: %s", e)
        return False

# Function to replace original audio with translated audio in video
def replace_audio_in_video(video_path, new_audio_path, output_video_path):
    logging.info("Replacing audio in video...")
    command = [
        'ffmpeg', '-y', '-i', video_path, '-i', new_audio_path, '-c:v', 'copy',
        '-map', '0:v:0', '-map', '1:a:0', '-shortest', output_video_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logging.info("FFmpeg output: %s", result.stdout)
    logging.error("FFmpeg error: %s", result.stderr)

# Function to select a video file
def select_video_file():
    Tk().withdraw()  # Hide the root Tk window
    video_path = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video Files", "*.mp4 *.avi *.mov")])
    return video_path

# Function to clean up temporary files
def cleanup_files(*files):
    for file in files:
        if os.path.exists(file):
            os.remove(file)

# Main function to process video
def process_video(video_path):
    if not video_path or not os.path.exists(video_path):
        logging.error("Invalid video file.")
        return

    audio_path = "temp_audio.wav"
    tts_audio_path = "translated_audio.wav"
    new_video_path = "translated_video.mp4"

    try:
        # Extract audio from video
        extract_audio(video_path, audio_path)
        if not os.path.exists(audio_path):
            logging.error("Audio extraction failed.")
            return

        # Transcribe audio to text
        transcript = transcribe_audio(audio_path)
        if "Transcription failed" in transcript:
            logging.error("Transcription failed.")
            return

        # Translate text to Hindi (using dummy translation function)
        translated_text = dummy_translate_to_hindi(transcript)

        # Convert translated text to speech
        if text_to_speech(translated_text, tts_audio_path):
            if not os.path.exists(tts_audio_path):
                logging.error("Text-to-speech conversion failed.")
                return

            # Replace the original audio with translated audio
            replace_audio_in_video(video_path, tts_audio_path, new_video_path)
            logging.info("Video processing complete. Translated video saved as %s", new_video_path)
        else:
            logging.error("Text-to-speech conversion failed. Unable to process the video.")
    except Exception as e:
        logging.exception("An error occurred during video processing: %s", e)
    finally:
        cleanup_files(audio_path, tts_audio_path)

# Select a video file
video_path = select_video_file()
if video_path:
    process_video(video_path)
else:
    logging.info("No video file selected.")
