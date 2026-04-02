import os
import shutil
import gc
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
# try:
#     from moviepy.editor import VideoFileClip
# except ImportError:
#     from moviepy.video.io.VideoFileClip import VideoFileClip

import imageio_ffmpeg

import librosa
import numpy as np

os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CORS(app, resources={r"/*": {"origins": "*"}})

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print(f"Created missing folder: {UPLOAD_FOLDER}")


def analyze_audio(file_path):
    try:
        print(f"DEBUG: Starting load for {file_path}")
        # Load only 5 seconds for the absolute minimum RAM usage
        y, sr = librosa.load(file_path, sr=11025, mono=True, duration=5)
        print("DEBUG: File loaded into memory")

        duration = librosa.get_duration(y=y, sr=sr)
        print(f"DEBUG: Duration calculated: {duration}")

        # This line is the most CPU/RAM intensive
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        print(f"DEBUG: Tempo calculated: {tempo}")

        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        mean_chroma = np.mean(chroma, axis=1)
        print("DEBUG: Chroma analysis complete")
        
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        main_note = notes[np.argmax(mean_chroma)]

        # 4. Get Brightness
        cent = librosa.feature.spectral_centroid(y=y, sr=sr)
        avg_brightness = np.mean(cent)

        # Store results in a plain dictionary
        output = {
            "tempo": round(float(tempo), 2),
            "key": str(main_note),
            "brightness": round(float(avg_brightness), 2),
            "duration_sec": round(float(duration), 2),
            "chroma_data": mean_chroma.tolist()
        }

        # CLEANUP LAST
        del y
        gc.collect()
        
        return output

    except Exception as e:
        print(f"Analysis Crash: {str(e)}")
        raise e # Let the upload route catch this
    
    
# This tells MoviePy exactly where the portable FFmpeg binary is located
# Allowing React to talk to this API


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filename = secure_filename(file.filename)
    original_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(original_file_path)
    print("File saved. Starting analysis...")
    # return jsonify(
    #     {"message": "File saved locally!", 
    #      "filename": filename, 
    #      "size": os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], filename)), 
    #      "status": "Ready for AI Analysis"})
    try:
        audio_path, is_temp = get_audio_path(original_file_path)

        # IF IT WAS A VIDEO: Delete the original video NOW to free up space/RAM
        if is_temp and os.path.exists(original_file_path):
            os.remove(original_file_path)

        # Now run analysis on the much smaller audio file
        results = analyze_audio(audio_path)

        # Cleanup the temporary audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return jsonify(results)

    except Exception as e:
        # Emergency cleanup if something crashes
        if os.path.exists(original_file_path): os.remove(original_file_path)
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/debug/files', methods=['GET'])
def list_files():
    # This lists everything in your upload folder
    upload_path = app.config['UPLOAD_FOLDER']
    
    if os.path.exists(upload_path):
        files = os.listdir(upload_path)
        return jsonify({
            "folder": upload_path,
            "files": files,
            "count": len(files)
        })
    else:
        return jsonify({"error": "Upload folder does not exist"}), 404
    
@app.route('/debug/clear-uploads', methods=['POST'])
def clear_uploads():
    
    folder = app.config['UPLOAD_FOLDER']
    
    try:
        # Delete everything inside the folder
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path) # Delete file
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path) # Delete subfolder
        
        return {"status": "success", "message": "Uploads folder cleared!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500    
    
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}

def get_audio_path(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in VIDEO_EXTENSIONS:
        audio_path = file_path.replace(ext, "_temp.mp3")
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        
        # This runs FFmpeg as a separate process, which is lighter on your Flask RAM
        command = [
            ffmpeg_exe, '-y', '-i', file_path, 
            '-vn', '-acodec', 'libmp3lame', '-q:a', '2', audio_path
        ]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return audio_path, True
    return file_path, False   

if __name__ == "__main__":
    app.run(debug=True, port=5001)