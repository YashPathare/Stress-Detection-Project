import base64
import cv2
import numpy as np
import time
import os
import joblib
import warnings
from collections import deque
from scipy import signal
from scipy.interpolate import CubicSpline
from scipy.stats import mode
import mediapipe as mp
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import asyncio

warnings.filterwarnings("ignore", category=UserWarning)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- 1. LOAD AI MODELS GLOBALLY ---
script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, 'models', 'stress_classifier.pkl')
scaler_path = os.path.join(script_dir, 'models', 'scaler.pkl')

try:
    clf = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    print("✅ AI Models Loaded Successfully")
except Exception as e:
    print(f"❌ ERROR LOADING MODELS: Run classifier.py first. Details: {e}")
    clf, scaler = None, None

mp_face_mesh = mp.solutions.face_mesh

@app.websocket("/ws/stress-engine")
async def stress_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🟢 React Frontend Connected! Booting AI Math Pipeline...")
    
    # Initialize connection-specific variables
    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False)
    BUFFER_SIZE = 250
    raw_signal = []
    timestamps = []
    
    # Smoothing Buffers
    bpm_history, sdnn_history, rmssd_history = deque(maxlen=45), deque(maxlen=45), deque(maxlen=45)
    pnn50_history, prediction_history = deque(maxlen=45), deque(maxlen=45)
    
    display_bpm, display_sdnn, display_rmssd, display_pnn50 = "--", "--", "--", "--"
    status_text = "WAITING FOR DATA"
    live_wave = []
    
    try:
        while True:
            # Add this above your while loop
            prev_box = None
            SMOOTHING = 0.15  # 15% new frame, 85% old frame (Shock absorber)

            # 1. Receive Base64 Image from React
            data = await websocket.receive_text()
            
            # Strip the HTML header and decode into an OpenCV Frame
            encoded_data = data.split(',')[1] if ',' in data else data
            nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None: continue

# ... (keep the base64 decoding part the same) ...

            # 2. Extract rPPG Data via MediaPipe
            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            
            box_data = None # NEW: Store the bounding box coordinates
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    # 1. Get RAW coordinates from MediaPipe
                    raw_y_min = int(face_landmarks.landmark[10].y * h)
                    raw_y_max = int(face_landmarks.landmark[151].y * h)
                    raw_x_min = int(face_landmarks.landmark[67].x * w)
                    raw_x_max = int(face_landmarks.landmark[297].x * w)
                    
                    if raw_y_min < raw_y_max and raw_x_min < raw_x_max and raw_y_min > 0 and raw_x_min > 0:
                        
                        # 2. Apply EMA Smoothing (The Fix)
                        if prev_box is None:
                            y_min, y_max, x_min, x_max = raw_y_min, raw_y_max, raw_x_min, raw_x_max
                        else:
                            y_min = int(SMOOTHING * raw_y_min + (1 - SMOOTHING) * prev_box[0])
                            y_max = int(SMOOTHING * raw_y_max + (1 - SMOOTHING) * prev_box[1])
                            x_min = int(SMOOTHING * raw_x_min + (1 - SMOOTHING) * prev_box[2])
                            x_max = int(SMOOTHING * raw_x_max + (1 - SMOOTHING) * prev_box[3])
                            
                        # Save for the next frame
                        prev_box = (y_min, y_max, x_min, x_max)

                        # 3. Calculate percentages using the SMOOTHED coordinates
                        box_data = {
                            "x": (x_min / w) * 100,
                            "y": (y_min / h) * 100,
                            "w": ((x_max - x_min) / w) * 100,
                            "h": ((y_max - y_min) / h) * 100
                        }

                        # Crop using the SMOOTHED coordinates
                        roi_frame = frame[y_min:y_max, x_min:x_max]

                        if roi_frame.size > 0:
                            b_mean, g_mean, r_mean = np.mean(roi_frame[:, :, 0]), np.mean(roi_frame[:, :, 1]), np.mean(roi_frame[:, :, 2])
                            g_normalized = g_mean / (r_mean + g_mean + b_mean + 1e-6)
                            
                            raw_signal.append(g_normalized)
                            timestamps.append(time.time())
                            
            # ... (keep the buffer management and math pipeline the same) ...
            else:
                # THE FIX: Camera covered or face lost
                # 1. Clear the box history
                prev_box = None 
                
                # 2. Destroy the signal arrays so math instantly stops
                raw_signal.clear() 
                timestamps.clear()
                live_wave.clear()
                
                # 3. Wipe the smoothing history so old data doesn't ruin the next scan
                bpm_history.clear()
                sdnn_history.clear()
                rmssd_history.clear()
                pnn50_history.clear()
                
                # 4. Force the UI to reset
                display_bpm, display_sdnn, display_rmssd, display_pnn50 = "--", "--", "--", "--"
                status_text = "FACE LOST - WAITING"

            # Manage Buffer Size
            if len(raw_signal) > BUFFER_SIZE:
                raw_signal.pop(0)
                timestamps.pop(0)

            # 3. MATH & MACHINE LEARNING PIPELINE
            progress = min(100, (len(raw_signal) / BUFFER_SIZE) * 100)
            
            if len(raw_signal) == BUFFER_SIZE:
                sig, t = np.array(raw_signal), np.array(timestamps)
                fps = BUFFER_SIZE / (t[-1] - t[0])
                detrended = signal.detrend(sig)
                
                if np.std(detrended) > 0:
                    normalized = (detrended - np.mean(detrended)) / np.std(detrended)
                    try:
                        b, a = signal.butter(3, [0.8 / (0.5 * fps), 3.0 / (0.5 * fps)], btype='band')
                        filtered = signal.filtfilt(b, a, normalized)
                        
                        new_fps = 250.0
                        num_points = int((t[-1] - t[0]) * new_fps)
                        new_t = np.linspace(t[0], t[-1], num_points)
                        cs = CubicSpline(t, filtered)
                        upsampled_signal = cs(new_t)
                        
                        # Grab the last 150 data points for the React Canvas Graph
                        live_wave = upsampled_signal[-150:].tolist() 
                        
                        peaks, _ = signal.find_peaks(upsampled_signal, distance=new_fps*0.4)
                        
                        if len(peaks) > 3:
                            raw_ibis = np.diff(new_t[peaks])
                            valid_ibis = raw_ibis[(raw_ibis > 0.33) & (raw_ibis < 1.5)]
                            
                            if len(valid_ibis) > 3:
                                bpm = 60.0 / np.mean(valid_ibis)
                                sdnn = np.std(valid_ibis) * 1000
                                rmssd = np.sqrt(np.mean(np.square(np.diff(valid_ibis)))) * 1000
                                nn50 = np.sum(np.abs(np.diff(valid_ibis * 1000)) > 50)
                                pnn50 = (nn50 / len(valid_ibis)) * 100
                                
                                if clf and scaler:
                                    features = np.array([[bpm, sdnn, rmssd, pnn50]])
                                    scaled_features = scaler.transform(features)
                                    prediction = clf.predict(scaled_features)[0]
                                    
                                    bpm_history.append(bpm)
                                    sdnn_history.append(sdnn)
                                    rmssd_history.append(rmssd)
                                    pnn50_history.append(pnn50)
                                    prediction_history.append(prediction)
                                    
                                    if len(bpm_history) > 15:
                                        display_bpm = round(np.mean(bpm_history), 1)
                                        display_sdnn = round(np.mean(sdnn_history), 1)
                                        display_rmssd = round(np.mean(rmssd_history), 1)
                                        display_pnn50 = round(np.mean(pnn50_history), 1)
                                        most_common_pred = mode(prediction_history, keepdims=True).mode[0]
                                    else:
                                        display_bpm, display_sdnn, display_rmssd, display_pnn50 = round(bpm, 1), round(sdnn, 1), round(rmssd, 1), round(pnn50, 1)
                                        most_common_pred = prediction
                                        
                                    # HYBRID LOGIC OVERRIDE
                                    if display_bpm > 95.0 or display_rmssd < 80.0:
                                        status_text = "HIGH STRESS"
                                    else:
                                        status_text = "LOW STRESS" if most_common_pred == 0 else "HIGH STRESS"
                            else:
                                status_text = "NOISY SIGNAL"
                        else:
                            status_text = "ANALYZING..."
                    except ValueError:
                        pass

# 4. Transmit the calculated payload back to React
            response = {
                "bpm": display_bpm,
                "sdnn": display_sdnn,
                "rmssd": display_rmssd,
                "pnn50": display_pnn50,
                "status": status_text if (progress == 100 or "FACE LOST" in status_text) else f"BUFFERING {int(progress)}%",
                "progress": progress,
                "graphData": live_wave,
                "box": box_data  # NEW: Send the coordinates to React!
            }
            await websocket.send_text(json.dumps(response))
            
            # Yield control back to the event loop so the server doesn't freeze
            await asyncio.sleep(0.01)
            
    except Exception as e:
        print(f"🔴 Connection Closed: {e}")
    finally:
        face_mesh.close()

if __name__ == "__main__":
    print("Starting Final Year AI Microservice on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)