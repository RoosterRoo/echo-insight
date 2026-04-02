import os
import shutil
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

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
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify(
        {"message": "File saved locally!", 
         "filename": filename, 
         "size": os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], filename)), 
         "status": "Ready for AI Analysis"})

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

if __name__ == "__main__":
    app.run(debug=True, port=5001)