import { useState, useRef, useEffect } from 'react';
import Webcam from 'react-webcam';
import './App.css';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
const FRAME_INTERVAL = 500;

// Brand palette (matches platformengineer.io — dark + neon, no Redis red)
const NEON_BLUE = '#38BDF8';   // active / scanning
const NEON_GREEN = '#34D399';  // match / success
const NEON_PURPLE = '#A78BFA'; // secondary accent

function App() {
  const webcamRef = useRef(null);
  const wsRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [matches, setMatches] = useState([]);
  const [processingTime, setProcessingTime] = useState(null);
  const [searchTime, setSearchTime] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [scanStatus, setScanStatus] = useState('idle'); // idle | scanning | match | no_face
  const [indexed, setIndexed] = useState(null);

  // Live count of indexed faces — a small flex that it is all in Redis.
  useEffect(() => {
    fetch('/api/stats')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (d && typeof d.total_celebrities === 'number') setIndexed(d.total_celebrities); })
      .catch(() => {});
  }, []);

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
  const accent = isMatch ? NEON_GREEN : NEON_BLUE;

  return (
    <div className="min-h-screen bg-[#0B0D12] text-white flex flex-col relative overflow-hidden">
      {/* ambient glow */}
      <div className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[700px] rounded-full blur-[130px] opacity-[0.10]"
           style={{ background: `radial-gradient(circle, ${isMatch ? NEON_GREEN : NEON_BLUE}, transparent 70%)` }} />

      <header className="relative z-10 border-b border-white/[0.06] px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <a href="https://platformengineer.io" className="flex items-center gap-2 group">
            <span className="text-[15px] font-semibold tracking-tight bg-gradient-to-r from-[#38BDF8] via-[#34D399] to-[#A78BFA] bg-clip-text text-transparent">
              platformengineer.io
            </span>
          </a>
          <span className="text-white/15 text-lg font-thin">/</span>
          <span className="text-sm text-white/45 font-light tracking-widest uppercase">Celebrity Face Match</span>
        </div>
        <div className="flex items-center gap-3">
          {indexed !== null && (
            <span className="hidden sm:inline-flex items-center gap-1.5 text-[11px] text-white/40 bg-white/[0.03] border border-white/[0.08] rounded-full px-3 py-1.5">
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: NEON_PURPLE }} />
              <span className="text-white/70 font-medium tabular-nums">{indexed.toLocaleString()}</span> faces indexed
            </span>
          )}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors ${
            isConnected
              ? 'border-emerald-500/30 bg-emerald-500/[0.08] text-emerald-300'
              : 'border-white/[0.08] bg-white/[0.04] text-white/30'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-white/20'}`} />
            {isConnected ? 'Live' : 'Connecting'}
          </div>
        </div>
      </header>

      <main className="relative z-10 flex-1 grid grid-cols-1 lg:grid-cols-2 gap-5 p-5 lg:p-8 xl:p-10 2xl:p-12">

        {/* Webcam panel */}
        <div className="flex flex-col gap-3">
          <div className="relative bg-black rounded-xl overflow-hidden aspect-video border border-white/[0.08]">
            <Webcam
              ref={webcamRef}
              audio={false}
              screenshotFormat="image/jpeg"
              className="w-full h-full object-cover"
              videoConstraints={{ width: 1280, height: 720, facingMode: 'user' }}
            />

            {/* Overlay */}
            <div className="absolute inset-0 pointer-events-none">
              {/* Corner brackets — tint to the active accent */}
              <div className="absolute top-3 left-3 w-5 h-5 border-t-2 border-l-2 opacity-70 transition-colors" style={{ borderColor: accent }} />
              <div className="absolute top-3 right-3 w-5 h-5 border-t-2 border-r-2 opacity-70 transition-colors" style={{ borderColor: accent }} />
              <div className="absolute bottom-3 left-3 w-5 h-5 border-b-2 border-l-2 opacity-70 transition-colors" style={{ borderColor: accent }} />
              <div className="absolute bottom-3 right-3 w-5 h-5 border-b-2 border-r-2 opacity-70 transition-colors" style={{ borderColor: accent }} />

              {/* Scan line */}
              {isProcessing && (
                <div className="scan-line absolute left-4 right-4 h-px"
                     style={{ background: `linear-gradient(to right, transparent, ${NEON_BLUE}99, transparent)` }} />
              )}

              {/* Match rings */}
              {isMatch && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="match-ring w-28 h-28 rounded-full border" style={{ borderColor: `${NEON_GREEN}99` }} />
                  <div className="match-ring-outer absolute w-40 h-40 rounded-full border" style={{ borderColor: `${NEON_GREEN}33` }} />
                </div>
              )}

              {/* Status badge */}
              {(isProcessing || isMatch) && (
                <div className="absolute top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-[10px] font-semibold tracking-widest border uppercase transition-all"
                     style={{ background: `${accent}1a`, borderColor: `${accent}66`, color: accent }}>
                  {isMatch ? 'Match found' : 'Scanning'}
                </div>
              )}
            </div>
          </div>

          {/* Status bar */}
          <div className="bg-[#12161F] rounded-lg border border-white/[0.06] px-4 py-2.5 flex items-center justify-between min-h-[42px]">
            <span className="text-sm">
              {isMatch ? (
                <>
                  <span className="font-medium" style={{ color: NEON_GREEN }}>{matches[0]?.name}</span>
                  <span className="text-white/25"> is your closest match</span>
                </>
              ) : isConnected ? (
                <span className="text-white/30">Look at the camera…</span>
              ) : (
                <span className="text-white/20">Connecting…</span>
              )}
            </span>
            {processingTime && (
              <div className="flex gap-2">
                <span className="text-[11px] bg-white/[0.04] border border-white/[0.08] rounded px-2 py-0.5 text-white/30">
                  <span className="text-white/60">{processingTime}s</span> total
                </span>
                <span className="text-[11px] rounded px-2 py-0.5 border" style={{ background: `${NEON_PURPLE}14`, borderColor: `${NEON_PURPLE}33`, color: `${NEON_PURPLE}` }}>
                  <span className="font-medium">{searchTime}s</span> redis
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Matches panel */}
        <div className="bg-[#12161F] rounded-xl border border-white/[0.06] overflow-hidden flex flex-col">
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
                  className="flex-1 flex items-center gap-5 px-6 border-l-2 transition-colors min-h-0"
                  style={index === 0
                    ? { borderColor: NEON_GREEN, background: `${NEON_GREEN}0a` }
                    : { borderColor: 'transparent' }}
                >
                  <span className="text-sm font-medium w-6 text-center flex-shrink-0"
                        style={{ color: index === 0 ? NEON_GREEN : 'rgba(255,255,255,0.2)' }}>
                    {index + 1}
                  </span>

                  {match.image_url ? (
                    <img
                      src={match.image_url}
                      alt={match.name}
                      referrerPolicy="no-referrer"
                      loading="lazy"
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
                    <p className="text-lg font-medium truncate" style={{ color: index === 0 ? '#fff' : 'rgba(255,255,255,0.6)' }}>
                      {match.name}
                    </p>
                    <p className="text-sm text-white/25 capitalize mt-0.5">{match.category}</p>
                  </div>

                  <div className="flex flex-col items-end gap-2 flex-shrink-0 w-24">
                    <span className="text-xl font-semibold tabular-nums"
                          style={{ color: index === 0 ? NEON_GREEN : 'rgba(255,255,255,0.4)' }}>
                      {match.similarity.toFixed(1)}%
                    </span>
                    <div className="w-full h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-700"
                           style={{ width: `${match.similarity}%`, background: index === 0 ? NEON_GREEN : 'rgba(255,255,255,0.15)' }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      <footer className="relative z-10 border-t border-white/[0.06] px-6 py-3 flex items-center justify-between">
        <div className="flex gap-5 text-[11px] text-white/25">
          <span>face embeddings <span className="text-white/45">dlib ResNet-34</span></span>
          <span className="hidden sm:inline">128-dim embeddings</span>
          <span className="hidden sm:inline">cosine KNN</span>
        </div>
        <span className="text-[11px] text-white/30">
          powered by <span style={{ color: NEON_GREEN }}>Redis 8</span> vector search
        </span>
      </footer>
    </div>
  );
}

export default App;
