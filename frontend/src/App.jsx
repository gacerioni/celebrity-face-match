import { useState, useRef, useEffect, useCallback } from 'react';
import Webcam from 'react-webcam';
import './App.css';

// Get WebSocket URL from environment or default to localhost
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
const FRAME_INTERVAL = 500; // Send frame every 500ms

function App() {
  const webcamRef = useRef(null);
  const wsRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState('Connecting...');
  const [matches, setMatches] = useState([]);
  const [processingTime, setProcessingTime] = useState(null);
  const [searchTime, setSearchTime] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket(WS_URL);
      
      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        setStatus('Ready! Position your face in the frame');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'result') {
          setIsProcessing(false);
          
          if (data.status === 'success') {
            setMatches(data.matches);
            setProcessingTime(data.processing_time);
            setSearchTime(data.search_time);
            setStatus(`✅ Match found! Top: ${data.matches[0].name}`);
          } else if (data.status === 'no_face') {
            setStatus(data.message);
            setMatches([]);
          } else if (data.status === 'no_matches') {
            setStatus(data.message);
            setMatches([]);
          }
        } else if (data.type === 'error') {
          setIsProcessing(false);
          setStatus(`❌ Error: ${data.message}`);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatus('❌ Connection error');
        setIsConnected(false);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setStatus('Disconnected. Reconnecting...');
        // Reconnect after 2 seconds
        setTimeout(connectWebSocket, 2000);
      };
      
      wsRef.current = ws;
    };
    
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Capture and send frames
  useEffect(() => {
    if (!isConnected || !webcamRef.current) return;

    const interval = setInterval(() => {
      const imageSrc = webcamRef.current?.getScreenshot();
      if (imageSrc && wsRef.current?.readyState === WebSocket.OPEN && !isProcessing) {
        setIsProcessing(true);
        wsRef.current.send(JSON.stringify({
          type: 'frame',
          image: imageSrc
        }));
      }
    }, FRAME_INTERVAL);

    return () => clearInterval(interval);
  }, [isConnected, isProcessing]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-sm border-b border-white/10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-4xl">🎭</span>
              <div>
                <h1 className="text-2xl font-bold text-white">Celebrity Face Match</h1>
                <p className="text-sm text-gray-300">Powered by Redis Vector Search</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'} animate-pulse`}></div>
              <span className="text-white text-sm">{isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Webcam Section */}
          <div className="space-y-4">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
              <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <span>📹</span> Live Webcam Feed
              </h2>
              
              <div className="relative rounded-xl overflow-hidden bg-black/50 aspect-video">
                <Webcam
                  ref={webcamRef}
                  audio={false}
                  screenshotFormat="image/jpeg"
                  className="w-full h-full object-cover"
                  videoConstraints={{
                    width: 1280,
                    height: 720,
                    facingMode: 'user'
                  }}
                />
                
                {isProcessing && (
                  <div className="absolute top-4 right-4 bg-blue-500/80 backdrop-blur-sm px-3 py-1 rounded-full">
                    <span className="text-white text-sm">🔍 Processing...</span>
                  </div>
                )}
              </div>
              
              {/* Status */}
              <div className="mt-4 p-4 bg-black/30 rounded-lg border border-white/10">
                <p className="text-white text-center">{status}</p>
                {processingTime && (
                  <div className="mt-2 flex justify-center gap-4 text-sm text-gray-300">
                    <span>⚡ Total: {processingTime}s</span>
                    <span>🔍 Redis: {searchTime}s</span>
                  </div>
                )}
              </div>
            </div>

            {/* Info Card */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
              <h3 className="text-lg font-semibold text-white mb-3">💡 Tips for Best Results</h3>
              <ul className="space-y-2 text-gray-200 text-sm">
                <li>📸 Ensure good lighting</li>
                <li>👤 Face the camera directly</li>
                <li>🎯 Position your face to fill the frame</li>
                <li>⚡ Processing happens automatically every 0.5s</li>
              </ul>
            </div>
          </div>

          {/* Matches Section */}
          <div className="space-y-4">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
              <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <span>🏆</span> Top 5 Celebrity Matches
              </h2>

              {matches.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <p className="text-6xl mb-4">🎭</p>
                  <p>Waiting for face detection...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {matches.map((match, index) => (
                    <div
                      key={index}
                      className={`flex items-center gap-4 p-4 rounded-xl transition-all duration-300 ${
                        index === 0
                          ? 'bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border-2 border-yellow-400/50'
                          : 'bg-white/5 border border-white/10'
                      }`}
                    >
                      {/* Rank Badge */}
                      <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${
                        index === 0 ? 'bg-yellow-400 text-black' :
                        index === 1 ? 'bg-gray-300 text-black' :
                        index === 2 ? 'bg-orange-400 text-black' :
                        'bg-white/20 text-white'
                      }`}>
                        {index + 1}
                      </div>

                      {/* Celebrity Image */}
                      {match.image_data ? (
                        <img
                          src={`data:image/jpeg;base64,${match.image_data}`}
                          alt={match.name}
                          className="w-20 h-20 rounded-lg object-cover border-2 border-white/20"
                        />
                      ) : (
                        <div className="w-20 h-20 rounded-lg bg-gray-700 flex items-center justify-center">
                          <span className="text-3xl">👤</span>
                        </div>
                      )}

                      {/* Match Info */}
                      <div className="flex-1">
                        <h3 className="text-white font-semibold text-lg">{match.name}</h3>
                        <p className="text-gray-300 text-sm capitalize">{match.category}</p>
                        <div className="mt-1 flex items-center gap-2">
                          <div className="flex-1 bg-white/10 rounded-full h-2 overflow-hidden">
                            <div
                              className="bg-gradient-to-r from-green-400 to-blue-500 h-full transition-all duration-500"
                              style={{ width: `${match.similarity}%` }}
                            ></div>
                          </div>
                          <span className="text-white font-semibold text-sm">
                            {match.similarity.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Tech Info */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
              <h3 className="text-lg font-semibold text-white mb-3">🔧 Technical Details</h3>
              <div className="space-y-2 text-sm text-gray-200">
                <div className="flex justify-between">
                  <span>Face Detection:</span>
                  <span className="text-white font-mono">dlib ResNet-34</span>
                </div>
                <div className="flex justify-between">
                  <span>Vector Dimensions:</span>
                  <span className="text-white font-mono">128-d embeddings</span>
                </div>
                <div className="flex justify-between">
                  <span>Search Engine:</span>
                  <span className="text-white font-mono">Redis Vector Search</span>
                </div>
                <div className="flex justify-between">
                  <span>Similarity Metric:</span>
                  <span className="text-white font-mono">Cosine Distance</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 pb-8 text-center text-gray-400 text-sm">
        <p>Powered by FastAPI + React + Redis Vector Search</p>
        <p className="mt-1">Modern, responsive, production-ready demo 🚀</p>
      </footer>
    </div>
  );
}

export default App;

