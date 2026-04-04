import os
import gc
import json
import subprocess
import numpy as np
import librosa
import imageio_ffmpeg
from flask import Flask, request, Response, stream_with_context
from flask_cors import CORS
from werkzeug.utils import secure_filename

# 1. Setup Environment
os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 150 * 1024 * 1024  # 150MB Limit

# 2. CORS - Allow all origins for the "Sharing Phase"
CORS(app, resources={r"/*": {"origins": "*"}})

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_audio_path(file_path):
    """Converts video to audio using a subprocess to save RAM."""
    ext = os.path.splitext(file_path)[1].lower()
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
    
    if ext in video_extensions:
        audio_path = file_path.replace(ext, "_temp.mp3")
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        command = [
            ffmpeg_exe, '-y', '-i', file_path, 
            '-vn', '-acodec', 'libmp3lame', '-q:a', '2', audio_path
        ]
        # Run conversion in the background
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return audio_path, True
    return file_path, False

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return json.dumps({"status": "error", "message": "No file uploaded"}), 400
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(original_path)

    @stream_with_context
    def generate_analysis():
        audio_path = None
        is_temp_audio = False
        
        try:
            # Step 1: Extraction
            yield json.dumps({"status": "starting", "progress": 5}) + "\n"
            audio_path, is_temp_audio = get_audio_path(original_path)
            
            # If we extracted audio, delete the heavy video file immediately
            if is_temp_audio and os.path.exists(original_path):
                os.remove(original_path)

            # Step 2: Chunked Analysis
            total_duration = librosa.get_duration(path=audio_path)
            chunk_size = 30  # 30-second windows
            current_offset = 0
            
            accumulated_chromas = []
            all_tempos = []
            all_brightness = []

            while current_offset < total_duration:
                # Load only the current 30s window
                y, sr = librosa.load(audio_path, sr=11025, mono=True, 
                                     offset=current_offset, duration=chunk_size)
                
                if len(y) > 0:
                    # 1. Chroma Analysis
                    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
                    accumulated_chromas.append(np.mean(chroma, axis=1))
                    
                    # 2. Tempo (Using item() to avoid scalar errors)
                    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                    all_tempos.append(np.atleast_1d(tempo).item(0))
                    
                    # 3. Brightness
                    cent = librosa.feature.spectral_centroid(y=y, sr=sr)
                    all_brightness.append(np.mean(cent))

                # Cleanup RAM after every chunk
                del y
                gc.collect()

                current_offset += chunk_size
                progress = min(int((current_offset / total_duration) * 90) + 5, 95)
                
                yield json.dumps({"status": "processing", "progress": progress}) + "\n"

            # Step 3: Final Aggregation
            final_chroma = np.mean(accumulated_chromas, axis=0).tolist()
            final_tempo = np.mean(all_tempos)
            final_brightness = np.mean(all_brightness)

            yield json.dumps({
                "status": "complete",
                "progress": 100,
                "analysis": {
                    "tempo": round(float(final_tempo), 2),
                    "brightness": round(float(final_brightness), 2),
                    "duration_sec": round(float(total_duration), 2),
                    "chroma_data": final_chroma
                }
            }) + "\n"

        except Exception as e:
            yield json.dumps({"status": "error", "message": str(e)}) + "\n"
        
        finally:
            # Final Cleanup: Remove any remaining files
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
            if not is_temp_audio and os.path.exists(original_path):
                os.remove(original_path)

    response = Response(generate_analysis(), content_type='application/x-ndjson')
    response.headers['X-Accel-Buffering'] = 'no'  # Prevents proxy buffering
    return response

@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True, port=5001)