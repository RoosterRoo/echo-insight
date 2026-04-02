import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}}) # Allowing React to talk to this API

UPLOAD_FOLDER = 'uploads'
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

if __name__ == "__main__":
    app.run(debug=True, port=5001)