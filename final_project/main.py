import os
from moviepy.editor import VideoFileClip
import pyttsx3
import subprocess
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import make_chunks
from tkinter import Tk, filedialog
import logging
from translations import translation_dict
from gtts import gTTS
import tempfile

# Setup logging
# created by whitedevil999123
logging.basicConfig(level=logging.INFO)

def translate_to_hinglish(text):
    """
    Translate text to Hinglish (a mixture of Hindi and English).
    For simplicity, this function will translate every other word into Hindi.

    Parameters:
    text (str): The input text in English.

    Returns:
    str: The translated text in Hinglish.
    """
    translated_words = []
    words = text.split()
    for i, word in enumerate(words):
        if i % 2 == 0:
            # Preserve English words
            translated_words.append(word)
        else:
            # Translate Hindi words
            translated_words.append(translation_dict.get(word.lower(), word))
    return ' '.join(translated_words)

def extract_audio(video_path, audio_path):
    logging.info("Extracting audio from video...")
    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        logging.info("Audio extracted to %s", audio_path)
    except Exception as e:
        logging.error("Error extracting audio: %s", e)

def transcribe_audio_chunks(audio_path, chunk_length_ms=5000):
    logging.info("Transcribing audio in chunks...")
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(audio_path)
    chunks = make_chunks(audio, chunk_length_ms)
    transcripts = []

    for i, chunk in enumerate(chunks):
        chunk_filename = f"chunk{i}.wav"
        chunk.export(chunk_filename, format="wav")
        with sr.AudioFile(chunk_filename) as source:
            audio_data = recognizer.record(source)
            try:
                transcript = recognizer.recognize_sphinx(audio_data)
                # Calculate start and end times
                start_time = i * chunk_length_ms / 1000
                end_time = start_time + len(chunk) / 1000
                transcripts.append((start_time, end_time, transcript))
            except sr.UnknownValueError:
                transcripts.append((0, 0, ""))
            except sr.RequestError as e:
                logging.error("Sphinx error: %s", e)
                transcripts.append((0, 0, ""))
        os.remove(chunk_filename)
    return transcripts

def text_to_speech_with_timing(transcripts, output_audio_path):
    logging.info("Converting translated text to speech with timing...")
    combined = AudioSegment.silent(duration=0)

    for start, end, text in transcripts:
        translated_text = translate_to_hinglish(text)
        temp_audio_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        if translated_text.isascii():
            tts = gTTS(translated_text, lang='en')  # English
        else:
            tts = gTTS(translated_text, lang='hi')  # Hindi
        tts.save(temp_audio_path)
        audio_segment = AudioSegment.from_file(temp_audio_path, format="mp3")
        combined += audio_segment

    combined.export(output_audio_path, format="wav")

def replace_audio_in_video(video_path, new_audio_path, output_video_path):
    logging.info("Replacing audio in video...")
    command = [
        'ffmpeg', '-y', '-i', video_path, '-i', new_audio_path, '-c:v', 'copy',
        '-map', '0:v:0', '-map', '1:a:0', '-shortest', output_video_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logging.info("FFmpeg output: %s", result.stdout)
    logging.error("FFmpeg error: %s", result.stderr)

def select_video_file():
    Tk().withdraw()  # Hide the root Tk window
    video_path = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video Files", "*.mp4 *.avi *.mov")])
    return video_path

def cleanup_files(*files):
    for file in files:
        if os.path.exists(file):
            os.remove(file)

def process_video(video_path):
    if not video_path or not os.path.exists(video_path):
        logging.error("Invalid video file.")
        return

    audio_path = "temp_audio.wav"
    tts_audio_path = "translated_audio.wav"
    new_video_path = "translated_video.mp4"

    try:
        extract_audio(video_path, audio_path)
        if not os.path.exists(audio_path):
            logging.error("Audio extraction failed.")
            return

        transcripts = transcribe_audio_chunks(audio_path)
        text_to_speech_with_timing(transcripts, tts_audio_path)

        if os.path.exists(tts_audio_path):
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
