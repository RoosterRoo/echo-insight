import { useEffect } from 'react';

import axios from 'axios';

import FileUpload from './components/FileUpload';

function App() {
  useEffect(() => {
    // Send a "ping" to the backend as soon as the user lands on the site
    // Even if it fails or times out, it triggers Render to start the server
    axios.get(`${import.meta.env.VITE_API_URL}/health`).catch(() => {
      console.log('Server is waking up in the background...');
    });
  }, []);
  return (
    <div className="container">
      <FileUpload />
    </div>
  );
}

export default App;
