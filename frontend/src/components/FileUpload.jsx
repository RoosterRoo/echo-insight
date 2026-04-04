import React, { useState, useRef } from 'react';
import axios from 'axios';
import AudioReport from './AudioReport';

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0); // 0 to 100
  const [status, setStatus] = useState('idle');
  const [analysisData, setAnalysisData] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    const MAX_SIZE_MB = 150;

    if (file && file.size > MAX_SIZE_MB * 1024 * 1024) {
      alert(
        `File is too large (${(file.size / 1024 / 1024).toFixed(2)}MB). Please keep it under 15MB.`,
      );
      e.target.value = null; // Clear the input
      return;
    }
    setFile(file);
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setStatus('uploading');
    setUploadProgress(0);

    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/upload`,
        formData,
        {
          // --- THE MAGIC HAPPENS HERE ---
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total,
            );
            setUploadProgress(percentCompleted);

            // If we hit 100% but the server hasn't responded, it's likely "Waking up"
            if (percentCompleted === 100) {
              setStatus('processing');
            }
          },
        },
      );

      setStatus('success');
      setAnalysisData(response.data);
      // Reset the input after a short delay
      setTimeout(() => {
        setFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
        setUploadProgress(0);
        setStatus('idle');
      }, 2000);
    } catch (err) {
      setStatus('error');
      console.error('Upload failed:', err);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white shadow-md rounded-lg">
      <h2 className="text-xl font-bold mb-4">AI Content Analyzer</h2>

      <input
        type="file"
        ref={fileInputRef}
        accept="video/*,audio/*"
        onChange={handleFileChange}
        className="block w-full text-sm text-gray-500 mb-4"
      />

      <button
        onClick={handleUpload}
        disabled={!file || status === 'uploading' || status === 'processing'}
        className={`w-full py-2 px-4 rounded text-white font-semibold ${
          !file ? 'bg-gray-400' : 'bg-indigo-600 hover:bg-indigo-700'
        }`}
      >
        {status === 'uploading'
          ? 'Uploading...'
          : status === 'processing'
            ? 'Processing...'
            : 'Upload File'}
      </button>

      {/* Progress Bar UI */}
      {(status === 'uploading' ||
        status === 'processing' ||
        status === 'success') && (
        <div className="mt-6">
          <div className="flex justify-between mb-1">
            <span className="text-sm font-medium text-indigo-700">
              {status === 'processing'
                ? 'Server is processing...'
                : 'Uploading...'}
            </span>
            <span className="text-sm font-medium text-indigo-700">
              {uploadProgress}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
        </div>
      )}

      {status === 'success' && (
        <p className="mt-4 text-center text-green-600 font-medium">
          ✓ Upload Complete!
        </p>
      )}
      {analysisData && <AudioReport data={analysisData} />}
    </div>
  );
};

export default FileUpload;
