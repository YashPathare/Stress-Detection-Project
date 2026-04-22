// import { useEffect, useRef, useState } from 'react';
// import './App.css';

// function App() {
//   const videoRef = useRef(null);
//   const hiddenCanvasRef = useRef(null);
//   const graphCanvasRef = useRef(null);
//   const wsRef = useRef(null);

//   // Added 'box' to store the targeting coordinates
//   const [metrics, setMetrics] = useState({
//     bpm: "--", sdnn: "--", rmssd: "--", pnn50: "--", status: "WAITING FOR CAMERA", progress: 0, graphData: [], box: null
//   });

//   const isStressed = metrics.status.includes("HIGH");
//   const themeColor = isStressed ? "#ff4444" : "#00E676"; 
//   const glowEffect = `0 0 15px ${themeColor}40`;

//   // --- 1. WEBSOCKET & CAMERA SETUP ---
//   useEffect(() => {
//     wsRef.current = new WebSocket('ws://localhost:8000/ws/stress-engine');
    
//     wsRef.current.onmessage = (event) => {
//       const data = JSON.parse(event.data);
//       setMetrics(data);
//     };

//     navigator.mediaDevices.getUserMedia({ video: true })
//       .then((stream) => {
//         if (videoRef.current) videoRef.current.srcObject = stream;
//       })
//       .catch((err) => console.error("Camera error:", err));

//     const interval = setInterval(() => {
//       if (videoRef.current && hiddenCanvasRef.current && wsRef.current.readyState === WebSocket.OPEN) {
//         const context = hiddenCanvasRef.current.getContext('2d');
//         context.drawImage(videoRef.current, 0, 0, 320, 240);
//         const base64Frame = hiddenCanvasRef.current.toDataURL('image/jpeg', 0.5);
//         wsRef.current.send(base64Frame);
//       }
//     }, 100); 

//     return () => clearInterval(interval);
//   }, []);

//   // --- 2. UPGRADED CLINICAL GRAPH ENGINE ---
//   useEffect(() => {
//     const canvas = graphCanvasRef.current;
//     if (!canvas || !metrics.graphData || metrics.graphData.length === 0) return;
    
//     const ctx = canvas.getContext('2d');
//     const width = canvas.width;
//     const height = canvas.height;
    
//     ctx.clearRect(0, 0, width, height);
    
//     // DRAW CLINICAL BACKGROUND GRID
//     ctx.strokeStyle = '#2a2a2a'; // Dark grey grid lines
//     ctx.lineWidth = 1;
//     for (let i = 0; i < width; i += 20) {
//       ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, height); ctx.stroke();
//     }
//     for (let i = 0; i < height; i += 20) {
//       ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(width, i); ctx.stroke();
//     }

//     // DRAW THE SIGNAL WAVE
//     ctx.beginPath();
//     ctx.strokeStyle = themeColor; 
//     ctx.lineWidth = 2.5;

//     const data = metrics.graphData;
//     const min = Math.min(...data);
//     const max = Math.max(...data);
//     const range = max - min || 1; 

//     data.forEach((val, index) => {
//       const x = (index / data.length) * width;
//       const y = height - 10 - ((val - min) / range) * (height - 20);
//       if (index === 0) ctx.moveTo(x, y);
//       else ctx.lineTo(x, y);
//     });
//     ctx.stroke();

//     // ADD TRANSLUCENT FILL UNDER THE WAVE FOR DEPTH
//     ctx.lineTo(width, height);
//     ctx.lineTo(0, height);
//     ctx.fillStyle = `${themeColor}20`; // Hex opacity (20)
//     ctx.fill();

//   }, [metrics.graphData, themeColor]);

//   return (
//     <div style={{ padding: '30px', fontFamily: 'Segoe UI, sans-serif', backgroundColor: '#0f0f0f', color: 'white', minHeight: '100vh' }}>
      
//       <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
//         <h1 style={{ margin: 0}}>🫀 Clinical Stress Engine</h1>
//         <div style={{ padding: '8px 20px', backgroundColor: '#1e1e1e', borderRadius: '20px', border: `1px solid ${themeColor}`, boxShadow: glowEffect }}>
//           <strong>Status: </strong> 
//           <span style={{ color: themeColor, fontWeight: 'bold', letterSpacing: '1px' }}>{metrics.status}</span>
//         </div>
//       </div>
      
//       <div style={{ display: 'flex', gap: '30px' }}>
//         {/* LEFT COLUMN */}
//         <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
//           <div style={{ backgroundColor: '#1a1a1a', padding: '15px', borderRadius: '12px', border: '1px solid #333' }}>
//             <h3 style={{ marginTop: 0, color: '#aaa' }}>Live Optical Feed</h3>
            
//             {/* VIDEO CONTAINER WITH TARGETING HUD */}
//             <div style={{ position: 'relative', width: '100%', borderRadius: '8px', overflow: 'hidden' }}>
//               <video ref={videoRef} autoPlay playsInline style={{ width: '100%', display: 'block', transform: 'scaleX(-1)' }} />
              
//               {/* THE DYNAMIC BOUNDING BOX */}
//               {metrics.box && (
//                 <div style={{
//                   position: 'absolute',
//                   top: `${metrics.box.y}%`,
//                   // Because the video is mirrored, we must invert the X-axis coordinate!
//                   left: `${100 - metrics.box.x - metrics.box.w}%`, 
//                   width: `${metrics.box.w}%`,
//                   height: `${metrics.box.h}%`,
//                   border: `2px solid ${themeColor}`,
//                   boxShadow: `inset 0 0 10px ${themeColor}50, 0 0 10px ${themeColor}50`,
//                   transition: 'all 0.1s ease',
//                   pointerEvents: 'none'
//                 }}>
//                   {/* Small ROI Label above the box */}
//                   <div style={{ backgroundColor: themeColor, color: '#000', fontSize: '10px', fontWeight: 'bold', padding: '2px 4px', position: 'absolute', top: '-18px', left: '-2px' }}>
//                     Forehead ROI
//                   </div>
//                 </div>
//               )}
//             </div>

//             <canvas ref={hiddenCanvasRef} width="320" height="240" style={{ display: 'none' }} />
//           </div>

//           <div style={{ backgroundColor: '#1a1a1a', padding: '15px', borderRadius: '12px', border: '1px solid #333' }}>
//             <h3 style={{ marginTop: 0, color: '#aaa', marginBottom: '10px' }}>Blood Volume Pulse (250Hz rPPG)</h3>
//             <canvas ref={graphCanvasRef} width="600" height="150" style={{ width: '100%', height: '150px', backgroundColor: '#0a0a0a', borderRadius: '4px', border: '1px solid #222' }} />
//           </div>

//         </div>

//         {/* RIGHT COLUMN */}
//         <div style={{ flex: 1, backgroundColor: '#1a1a1a', padding: '30px', borderRadius: '12px', border: `1px solid ${themeColor}`, boxShadow: glowEffect, transition: 'all 0.3s ease' }}>
          
//           <h2 style={{ borderBottom: '1px solid #333', paddingBottom: '10px', marginTop: 0 }}>Physiological Biomarkers</h2>
          
//           <div style={{ marginBottom: '30px' }}>
//             <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
//               <span style={{ color: '#aaa' }}>AI Buffer Progress</span>
//               <span style={{ fontWeight: 'bold' }}>{Math.round(metrics.progress)}%</span>
//             </div>
//             <div style={{ width: '100%', backgroundColor: '#222', height: '12px', borderRadius: '6px', overflow: 'hidden' }}>
//               <div style={{ width: `${metrics.progress}%`, backgroundColor: themeColor, height: '100%', transition: 'width 0.2s ease' }}></div>
//             </div>
//           </div>

//           <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
//             <MetricCard title="Heart Rate" value={metrics.bpm} unit="BPM" />
//             <MetricCard title="SDNN" value={metrics.sdnn} unit="ms" />
//             <MetricCard title="RMSSD" value={metrics.rmssd} unit="ms" />
//             <MetricCard title="pNN50" value={metrics.pnn50} unit="%" />
//           </div>

//         </div>
//       </div>
//     </div>
//   );
// }

// function MetricCard({ title, value, unit }) {
//   return (
//     <div style={{ backgroundColor: '#222', padding: '25px', borderRadius: '10px', textAlign: 'center', border: '1px solid #333' }}>
//       <div style={{ color: '#888', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '10px' }}>{title}</div>
//       <div style={{ fontSize: '32px', fontWeight: 'bold', color: 'white' }}>
//         {value} <span style={{ fontSize: '16px', color: '#666', fontWeight: 'normal' }}>{unit}</span>
//       </div>
//     </div>
//   );
// }

// export default App;

import { useEffect, useRef, useState } from 'react';
import './App.css';

function App() {
  const videoRef = useRef(null);
  const hiddenCanvasRef = useRef(null);
  const graphCanvasRef = useRef(null);
  const wsRef = useRef(null);

  const [metrics, setMetrics] = useState({
    bpm: "--", sdnn: "--", rmssd: "--", pnn50: "--",
    status: "WAITING FOR CAMERA", progress: 0, graphData: [], box: null
  });

  const [tick, setTick] = useState(false);

  const isStressed = metrics.status.includes("HIGH");
  const isWaiting = metrics.status.includes("WAITING") || metrics.status.includes("CALIBRAT");
  const themeColor = isStressed ? "#ef4444" : isWaiting ? "#f59e0b" : "#10b981";
  const statusLabel = isStressed ? "STRESS DETECTED" : isWaiting ? "CALIBRATING" : "NOMINAL";

  useEffect(() => {
    const pulse = setInterval(() => setTick(t => !t), 800);
    return () => clearInterval(pulse);
  }, []);

  useEffect(() => {
    wsRef.current = new WebSocket('ws://localhost:8000/ws/stress-engine');

    // 1. Create a dedicated function to grab and send exactly ONE frame
    const sendNextFrame = () => {
      if (videoRef.current && hiddenCanvasRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        const video = videoRef.current;
        
        // Only draw if the camera has fully booted
        if (video.videoWidth > 0) {
          const canvas = hiddenCanvasRef.current;
          const context = canvas.getContext('2d');
          
          // Lock the canvas to the exact aspect ratio
          const aspect = video.videoWidth / video.videoHeight;
          canvas.width = 480; 
          canvas.height = 480 / aspect; 
          
          context.drawImage(video, 0, 0, canvas.width, canvas.height);
          const base64Frame = canvas.toDataURL('image/jpeg', 0.5);
          wsRef.current.send(base64Frame);
        } else {
          // If camera isn't ready, check again in 50ms
          setTimeout(sendNextFrame, 50); 
        }
      }
    };

    // 2. Start the loop the exact millisecond the WebSocket opens
    wsRef.current.onopen = () => {
      sendNextFrame();
    };

    // 3. The Ping-Pong Loop: Receive Data -> Update UI -> Send Next Frame
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMetrics(data);
      
      // INSTANTLY send the next frame synced to the monitor's refresh rate
      requestAnimationFrame(sendNextFrame); 
    };

    // Boot up the camera
    navigator.mediaDevices.getUserMedia({ video: true })
      .then((stream) => {
        if (videoRef.current) videoRef.current.srcObject = stream;
      })
      .catch((err) => console.error("Camera error:", err));

    // Cleanup when component unmounts
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    const canvas = graphCanvasRef.current;
    if (!canvas || !metrics.graphData || metrics.graphData.length === 0) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    // subtle grid
    ctx.strokeStyle = 'rgba(255,255,255,0.04)';
    ctx.lineWidth = 1;
    for (let i = 0; i < width; i += 30) {
      ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, height); ctx.stroke();
    }
    for (let i = 0; i < height; i += 20) {
      ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(width, i); ctx.stroke();
    }

    const data = metrics.graphData;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    // glow under curve
    ctx.beginPath();
    data.forEach((val, index) => {
      const x = (index / data.length) * width;
      const y = height - 8 - ((val - min) / range) * (height - 20);
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    const grad = ctx.createLinearGradient(0, 0, 0, height);
    grad.addColorStop(0, themeColor + '55');
    grad.addColorStop(1, themeColor + '00');
    ctx.fillStyle = grad;
    ctx.fill();

    // main line
    ctx.beginPath();
    ctx.strokeStyle = themeColor;
    ctx.lineWidth = 2;
    ctx.shadowColor = themeColor;
    ctx.shadowBlur = 6;
    data.forEach((val, index) => {
      const x = (index / data.length) * width;
      const y = height - 8 - ((val - min) / range) * (height - 20);
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.shadowBlur = 0;
  }, [metrics.graphData, themeColor]);

  return (
    <div className="app-shell">
      {/* HEADER */}
      <header className="app-header">
        <div className="header-left">
          <div className="logo-mark">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <circle cx="14" cy="14" r="13" stroke={themeColor} strokeWidth="1.5"/>
              <path d="M4 14h4l3-6 4 12 3-9 2 3h8" stroke={themeColor} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <div className="app-title">NeuroStress Monitor</div>
            <div className="app-subtitle">Facial rPPG Biometric Analysis</div>
          </div>
        </div>

        <div className="header-center">
          <div className="scan-line-container">
            <span className="scan-dot" style={{ background: themeColor, boxShadow: `0 0 8px ${themeColor}` }} />
            <span className="scan-label" style={{ color: themeColor }}>{statusLabel}</span>
          </div>
        </div>

        <div className="header-right">
          <div className="session-info">
            <span className="session-badge">LIVE SESSION</span>
            <span className="session-id">SID-{Math.random().toString(36).substr(2, 8).toUpperCase()}</span>
          </div>
        </div>
      </header>

      {/* MAIN GRID */}
      <main className="main-grid">

        {/* LEFT COLUMN */}
        <div className="left-col">

          {/* Camera feed */}
          <div className="panel camera-panel">
            <div className="panel-header">
              <span className="panel-label">OPTICAL FEED</span>
              <span className="panel-tag" style={{ color: themeColor }}>● LIVE</span>
            </div>
            <div className="video-wrapper">
              <video ref={videoRef} autoPlay playsInline className="video-feed" />

              {/* Corner HUD brackets */}
              <div className="hud-corner hud-tl"/>
              <div className="hud-corner hud-tr"/>
              <div className="hud-corner hud-bl"/>
              <div className="hud-corner hud-br"/>

              {/* Scan line animation */}
              <div className="scan-sweep" style={{ borderColor: themeColor + '60' }}/>

{/* Bounding box */}
              {metrics.box && (
                <div className="roi-box" style={{
                  top: `${metrics.box.y}%`,
                  left: `${100 - metrics.box.x - metrics.box.w}%`,
                  width: `${metrics.box.w}%`,
                  height: `${metrics.box.h}%`,
                  borderColor: themeColor,
                  background: 'transparent',
                  boxShadow: `0 0 8px ${themeColor}40`,
                  transition: 'all 0.15s linear', // ADD THIS LINE: Forces zero-latency tracking
                  pointerEvents: 'none'            // ADD THIS LINE: Stops the box from blocking clicks
                }}>
                </div>
              )}
            </div>
            <canvas ref={hiddenCanvasRef} width="320" height="240" style={{ display: 'none' }} />
          </div>

          {/* Graph */}
          <div className="panel graph-panel">
            <div className="panel-header">
              <span className="panel-label">BLOOD VOLUME PULSE</span>
              <span className="panel-tag">rPPG · 250Hz</span>
            </div>
            <canvas
              ref={graphCanvasRef}
              width={600}
              height={140}
              className="graph-canvas"
            />
            <div className="graph-footer">
              <span>0s</span><span>TEMPORAL AXIS</span><span>30s</span>
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN */}
        <div className="right-col">

          {/* Buffer progress */}
          <div className="panel progress-panel">
            <div className="panel-header">
              <span className="panel-label">AI BUFFER</span>
              <span className="panel-tag" style={{ color: themeColor }}>{Math.round(metrics.progress)}%</span>
            </div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${metrics.progress}%`, background: themeColor, boxShadow: `0 0 10px ${themeColor}80` }}/>
              {[25, 50, 75].map(p => (
                <div key={p} className="progress-tick" style={{ left: `${p}%` }}/>
              ))}
            </div>
            <div className="progress-labels">
              <span>SAMPLING</span><span>ANALYZING</span><span>READY</span>
            </div>
          </div>

          {/* Metrics grid */}
          <div className="panel biomarkers-panel">
            <div className="panel-header">
              <span className="panel-label">PHYSIOLOGICAL BIOMARKERS</span>
            </div>

            <div className="metrics-grid">
              <MetricCard title="Heart Rate" value={metrics.bpm} unit="BPM" icon="♥" accent={themeColor} primary />
              <MetricCard title="SDNN" value={metrics.sdnn} unit="ms" icon="σ" accent={themeColor} />
              <MetricCard title="RMSSD" value={metrics.rmssd} unit="ms" icon="∿" accent={themeColor} />
              <MetricCard title="pNN50" value={metrics.pnn50} unit="%" icon="%" accent={themeColor} />
            </div>
          </div>

          {/* Stress indicator */}
          <div className="panel stress-verdict-panel" style={{ borderColor: themeColor + '60' }}>
            <div className="verdict-content">
              <div className="verdict-icon" style={{ color: themeColor }}>
                {isStressed ? '⚠' : isWaiting ? '◌' : '✓'}
              </div>
              <div className="verdict-text">
                <div className="verdict-title" style={{ color: themeColor }}>{statusLabel}</div>
                <div className="verdict-sub">
                  {isStressed
                    ? 'Elevated autonomic response detected. HRV suppressed.'
                    : isWaiting
                    ? 'Collecting baseline physiological signal...'
                    : 'HRV within normal range. No acute stress markers.'}
                </div>
              </div>
            </div>
            <div className="verdict-bar" style={{ background: themeColor + '20' }}>
              <div className="verdict-bar-fill" style={{
                width: isStressed ? '80%' : isWaiting ? '40%' : '20%',
                background: themeColor
              }}/>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}

function MetricCard({ title, value, unit, icon, accent, primary }) {
  return (
    <div className={`metric-card ${primary ? 'metric-card--primary' : ''}`}
      style={primary ? { borderColor: accent + '80', background: accent + '08' } : {}}>
      <div className="metric-icon" style={{ color: accent }}>{icon}</div>
      <div className="metric-label">{title}</div>
      <div className="metric-value" style={primary ? { color: accent } : {}}>
        {value}
        <span className="metric-unit">{unit}</span>
      </div>
    </div>
  );
}

export default App;
