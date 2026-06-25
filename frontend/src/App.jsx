import { useState, useRef, useEffect } from 'react';
import Webcam from 'react-webcam';
import './App.css';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
const FRAME_INTERVAL = 500;

function App() {
  const webcamRef = useRef(null);
  const wsRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [matches, setMatches] = useState([]);
  const [processingTime, setProcessingTime] = useState(null);
  const [searchTime, setSearchTime] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [scanStatus, setScanStatus] = useState('idle'); // idle | scanning | match | no_face

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        setIsConnected(true);
        setScanStatus('idle');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'result') {
          setIsProcessing(false);
          if (data.status === 'success') {
            setMatches(data.matches);
            setProcessingTime(data.processing_time);
            setSearchTime(data.search_time);
            setScanStatus('match');
          } else {
            setScanStatus('no_face');
            setMatches([]);
          }
        } else if (data.type === 'error') {
          setIsProcessing(false);
          setScanStatus('idle');
        }
      };

      ws.onerror = () => setIsConnected(false);

      ws.onclose = () => {
        setIsConnected(false);
        setScanStatus('idle');
        setTimeout(connect, 2000);
      };

      wsRef.current = ws;
    };

    connect();
    return () => wsRef.current?.close();
  }, []);

  useEffect(() => {
    if (!isConnected) return;
    const interval = setInterval(() => {
      const imageSrc = webcamRef.current?.getScreenshot();
      if (imageSrc && wsRef.current?.readyState === WebSocket.OPEN && !isProcessing) {
        setIsProcessing(true);
        setScanStatus('scanning');
        wsRef.current.send(JSON.stringify({ type: 'frame', image: imageSrc }));
      }
    }, FRAME_INTERVAL);
    return () => clearInterval(interval);
  }, [isConnected, isProcessing]);

  const isMatch = scanStatus === 'match';

  return (
    <div className="min-h-screen bg-[#0D0F14] text-white flex flex-col">

      <header className="border-b border-white/[0.06] px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src="/redis-wordmark.svg" alt="Redis" className="h-[18px] brightness-0 invert opacity-90" />
          <span className="text-white/15 text-xl font-thin">|</span>
          <span className="text-sm text-white/40 font-light tracking-widest uppercase">Face Match</span>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors ${
          isConnected
            ? 'border-emerald-500/30 bg-emerald-500/[0.08] text-emerald-400'
            : 'border-white/[0.08] bg-white/[0.04] text-white/30'
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-400' : 'bg-white/20'}`} />
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </header>

      <main className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-5 p-5 lg:p-8 xl:p-10 2xl:p-12">

        {/* Webcam panel */}
        <div className="flex flex-col gap-3">
          <div className="relative bg-black rounded-xl overflow-hidden aspect-video border border-white/[0.06]">
            <Webcam
              ref={webcamRef}
              audio={false}
              screenshotFormat="image/jpeg"
              className="w-full h-full object-cover"
              videoConstraints={{ width: 1280, height: 720, facingMode: 'user' }}
            />

            {/* Overlay */}
            <div className="absolute inset-0 pointer-events-none">
              {/* Corner brackets */}
              <div className="absolute top-3 left-3 w-5 h-5 border-t-2 border-l-2 border-[#FF4438] opacity-60" />
              <div className="absolute top-3 right-3 w-5 h-5 border-t-2 border-r-2 border-[#FF4438] opacity-60" />
              <div className="absolute bottom-3 left-3 w-5 h-5 border-b-2 border-l-2 border-[#FF4438] opacity-60" />
              <div className="absolute bottom-3 right-3 w-5 h-5 border-b-2 border-r-2 border-[#FF4438] opacity-60" />

              {/* Scan line */}
              {isProcessing && (
                <div className="scan-line absolute left-4 right-4 h-px bg-gradient-to-r from-transparent via-[#FF4438]/50 to-transparent" />
              )}

              {/* Match rings */}
              {isMatch && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="match-ring w-28 h-28 rounded-full border border-[#FF4438]/60" />
                  <div className="match-ring-outer absolute w-40 h-40 rounded-full border border-[#FF4438]/20" />
                </div>
              )}

              {/* Status badge */}
              {(isProcessing || isMatch) && (
                <div className={`absolute top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-[10px] font-semibold tracking-widest border uppercase transition-all ${
                  isMatch
                    ? 'bg-[#FF4438]/10 border-[#FF4438]/40 text-[#FF4438]'
                    : 'bg-white/[0.05] border-white/10 text-white/40'
                }`}>
                  {isMatch ? 'Match found' : 'Scanning'}
                </div>
              )}
            </div>
          </div>

          {/* Status bar */}
          <div className="bg-[#161B24] rounded-lg border border-white/[0.06] px-4 py-2.5 flex items-center justify-between min-h-[42px]">
            <span className="text-sm">
              {isMatch ? (
                <>
                  <span className="text-[#FF4438] font-medium">{matches[0]?.name}</span>
                  <span className="text-white/25"> matched</span>
                </>
              ) : isConnected ? (
                <span className="text-white/30">Waiting for face...</span>
              ) : (
                <span className="text-white/20">Connecting...</span>
              )}
            </span>
            {processingTime && (
              <div className="flex gap-2">
                <span className="text-[11px] bg-white/[0.04] border border-white/[0.08] rounded px-2 py-0.5 text-white/30">
                  <span className="text-white/60">{processingTime}s</span> total
                </span>
                <span className="text-[11px] bg-white/[0.04] border border-white/[0.08] rounded px-2 py-0.5 text-white/30">
                  <span className="text-white/60">{searchTime}s</span> redis
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Matches panel */}
        <div className="bg-[#161B24] rounded-xl border border-white/[0.06] overflow-hidden flex flex-col">
          <div className="px-5 py-3.5 border-b border-white/[0.06] flex items-center justify-between">
            <span className="text-sm font-medium text-white/70">Top matches</span>
            {matches.length > 0 && (
              <span className="text-[11px] text-white/25 bg-white/[0.04] border border-white/[0.08] rounded-full px-2.5 py-0.5">
                {matches.length} results
              </span>
            )}
          </div>

          {matches.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center py-16 gap-3">
              <svg className="w-12 h-12 text-white/10" fill="none" stroke="currentColor" strokeWidth="1" viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="12" cy="8" r="4" />
                <path d="M6 20v-2a6 6 0 0112 0v2" />
              </svg>
              <span className="text-base text-white/20">Position your face in the frame</span>
            </div>
          ) : (
            <div className="flex-1 flex flex-col divide-y divide-white/[0.04]">
              {matches.map((match, index) => (
                <div
                  key={index}
                  className={`flex-1 flex items-center gap-5 px-6 border-l-2 transition-colors min-h-0 ${
                    index === 0
                      ? 'border-[#FF4438] bg-[#FF4438]/[0.04]'
                      : 'border-transparent'
                  }`}
                >
                  <span className={`text-sm font-medium w-6 text-center flex-shrink-0 ${
                    index === 0 ? 'text-[#FF4438]' : 'text-white/20'
                  }`}>
                    {index + 1}
                  </span>

                  {match.image_data ? (
                    <img
                      src={`data:image/jpeg;base64,${match.image_data}`}
                      alt={match.name}
                      className="w-16 h-16 rounded-xl object-cover border border-white/[0.08] flex-shrink-0"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center flex-shrink-0">
                      <svg className="w-7 h-7 text-white/15" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24" aria-hidden="true">
                        <circle cx="12" cy="8" r="4" />
                        <path d="M6 20v-2a6 6 0 0112 0v2" />
                      </svg>
                    </div>
                  )}

                  <div className="flex-1 min-w-0">
                    <p className={`text-lg font-medium truncate ${
                      index === 0 ? 'text-white' : 'text-white/60'
                    }`}>
                      {match.name}
                    </p>
                    <p className="text-sm text-white/25 capitalize mt-0.5">{match.category}</p>
                  </div>

                  <div className="flex flex-col items-end gap-2 flex-shrink-0 w-24">
                    <span className={`text-xl font-semibold ${
                      index === 0 ? 'text-[#FF4438]' : 'text-white/40'
                    }`}>
                      {match.similarity.toFixed(1)}%
                    </span>
                    <div className="w-full h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${
                          index === 0 ? 'bg-[#FF4438]' : 'bg-white/15'
                        }`}
                        style={{ width: `${match.similarity}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      <footer className="border-t border-white/[0.06] px-6 py-3 flex items-center justify-between">
        <div className="flex gap-5 text-[11px] text-white/20">
          <span>dlib <span className="text-white/35">ResNet-34</span></span>
          <span>128-dim embeddings</span>
          <span>cosine distance</span>
        </div>
        <span className="text-[11px] text-white/15">Vector Search</span>
      </footer>

    </div>
  );
}

export default App;
