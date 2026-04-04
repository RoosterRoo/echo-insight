import React, { useState, useRef } from 'react';
import AudioReport from './AudioReport';

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle'); // 'idle', 'uploading', 'processing', 'success', 'error'
  const [analysisData, setAnalysisData] = useState(null);
  const [targetNote, setTargetNote] = useState('C');
  const fileInputRef = useRef(null);

  const noteNames = [
    'C',
    'C#',
    'D',
    'D#',
    'E',
    'F',
    'F#',
    'G',
    'G#',
    'A',
    'A#',
    'B',
  ];

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    const MAX_SIZE_MB = 150;

    if (selectedFile && selectedFile.size > MAX_SIZE_MB * 1024 * 1024) {
      alert(
        `File is too large (${(selectedFile.size / 1024 / 1024).toFixed(2)}MB). Limit is 150MB.`,
      );
      e.target.value = null;
      return;
    }
    setFile(selectedFile);
    setAnalysisData(null); // Clear old results when new file is picked
    setProgress(0);
    setStatus('idle');
  };

  const handleUpload = async () => {
    if (!file) return;

    console.log('1. Starting upload process...');
    setStatus('uploading');
    setAnalysisData(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      console.log('2. Response received from server. Status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Server Error: ${errorText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      console.log('3. Entering stream reader loop...');

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          console.log('4. Stream finished (done: true)');
          break;
        }

        const textChunk = decoder.decode(value, { stream: true });
        console.log('RAW CHUNK RECEIVED:', textChunk);

        const lines = textChunk.split('\n').filter((line) => line.trim());

        for (const line of lines) {
          try {
            // Safety check: ignore non-JSON whitespace/buffer-breakers
            if (!line.startsWith('{')) continue;

            const data = JSON.parse(line);
            console.log('PARSED DATA:', data);

            if (data.status === 'processing' || data.status === 'starting') {
              setStatus('processing');
              setProgress(data.progress || 0);
            }

            if (data.status === 'complete') {
              console.log('5. Analysis Complete! Data received.');
              setAnalysisData(data.analysis);
              setStatus('success');
              setProgress(100);
            }

            if (data.status === 'error') {
              throw new Error(data.message);
            }
          } catch (e) {
            console.warn('Could not parse line as JSON:', line);
          }
        }
      }
    } catch (err) {
      console.error('CRITICAL ERROR:', err);
      setStatus('error');
      alert(`Upload Failed: ${err.message}`);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-gray-900 border border-gray-800 shadow-2xl rounded-xl text-white">
      <h2 className="text-2xl font-bold mb-6 text-center text-indigo-400">
        EchoInsight AI
      </h2>

      {/* Target Note Selector */}
      <div className="mb-6 p-4 bg-gray-800 rounded-lg border border-gray-700">
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
          Target Vocal Note
        </label>
        <select
          value={targetNote}
          onChange={(e) => setTargetNote(e.target.value)}
          className="bg-gray-700 text-white p-2 rounded w-full border border-gray-600 focus:ring-2 focus:ring-indigo-500 outline-none"
        >
          {noteNames.map((note) => (
            <option key={note} value={note}>
              {note}
            </option>
          ))}
        </select>
      </div>

      <input
        type="file"
        ref={fileInputRef}
        accept="video/*,audio/*"
        onChange={handleFileChange}
        className="block w-full text-sm text-gray-400 mb-6 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700 cursor-pointer"
      />

      <button
        onClick={handleUpload}
        disabled={!file || status === 'uploading' || status === 'processing'}
        className={`w-full py-3 px-4 rounded-lg font-bold transition-all ${
          !file || status === 'uploading' || status === 'processing'
            ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
            : 'bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-500/20'
        }`}
      >
        {status === 'uploading'
          ? '🚀 Sending...'
          : status === 'processing'
            ? '🧠 Analyzing...'
            : 'Analyze Performance'}
      </button>

      {/* Progress Section */}
      {(status === 'uploading' || status === 'processing') && (
        <div className="mt-8">
          <div className="flex justify-between mb-2">
            <span className="text-xs font-bold text-indigo-400 uppercase">
              {status === 'processing' ? 'Server Processing' : 'Uploading File'}
            </span>
            <span className="text-xs font-bold text-indigo-400">
              {progress}%
            </span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-2 border border-gray-700">
            <div
              className="bg-indigo-500 h-full rounded-full transition-all duration-500 ease-out shadow-[0_0_10px_rgba(99,102,241,0.5)]"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-[10px] text-gray-500 mt-2 text-center">
            Processing in 30-second chunks to ensure accuracy.
          </p>
        </div>
      )}

      {status === 'success' && (
        <p className="mt-4 text-center text-green-400 font-bold animate-pulse">
          ✓ Analysis Complete!
        </p>
      )}

      {analysisData && (
        <div className="mt-8 border-t border-gray-800 pt-6">
          <AudioReport data={analysisData} targetNote={targetNote} />
        </div>
      )}
    </div>
  );
};

export default FileUpload;
