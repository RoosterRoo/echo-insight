import os
import shutil
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    from moviepy.video.io.VideoFileClip import VideoFileClip

import imageio_ffmpeg

import librosa
import numpy as np

def analyze_audio(file_path):
    # 1. Load the audio file (y = audio array, sr = sample rate)
    y, sr = librosa.load(file_path)

    # 2. Extract Tempo (Beats Per Minute)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    # 3. Extract Pitch (Chroma Features)
    # This tells us which musical notes (C, C#, D...) are strongest
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    mean_chroma = np.mean(chroma, axis=1)
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    main_note = notes[np.argmax(mean_chroma)]

    # 4. Extract Spectral Centroid (Indicates "Brightness" of the voice)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)
    avg_brightness = np.mean(cent)

    return {
        "tempo": round(float(tempo), 2),
        "key": main_note,
        "brightness": round(float(avg_brightness), 2),
        "duration_sec": round(librosa.get_duration(y=y, sr=sr), 2),
        "chroma_data": mean_chroma.tolist() # Array for a bar chart in React
    }

# This tells MoviePy exactly where the portable FFmpeg binary is located
os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": [          # For local development
            "https://echo-insight-kappa.vercel.app"  # Your production frontend
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
}) # Allowing React to talk to this API

UPLOAD_FOLDER = 'uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print(f"Created missing folder: {UPLOAD_FOLDER}")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filename = secure_filename(file.filename)
    original_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(original_file_path)
    # return jsonify(
    #     {"message": "File saved locally!", 
    #      "filename": filename, 
    #      "size": os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], filename)), 
    #      "status": "Ready for AI Analysis"})
    try:
        # 1. Get audio (extract if video)
        audio_path, is_temp = get_audio_path(original_file_path)

        # 2. Run your existing Librosa analysis
        results = analyze_audio(audio_path)
        #results = {"status": "Success", "message": "Ready for analysis!"} 

        # 3. Cleanup: Delete BOTH files immediately
        if os.path.exists(original_file_path):
            os.remove(original_file_path)
        if is_temp and os.path.exists(audio_path):
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
    """Returns a path to an audio file. Extracts from video if necessary."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in VIDEO_EXTENSIONS:
        print(f"Video detected ({ext}). Extracting audio...")
        audio_path = file_path.replace(ext, "_temp_audio.mp3")
        
        # Load video, extract audio, and CLOSE to release memory
        with VideoFileClip(file_path) as video:
            video.audio.write_audiofile(audio_path, logger=None)
        
        return audio_path, True # True means we created a temp file
    
    return file_path, False # It was already audio    

if __name__ == "__main__":
    app.run(debug=True, port=5001)