import cv2
import time
import numpy as np
import os
from scipy import signal
from scipy.interpolate import CubicSpline
import joblib
import warnings
from collections import deque
from scipy.stats import mode
import mediapipe as mp

warnings.filterwarnings("ignore", category=UserWarning)

# --- HELPER: DRAW THE HUD ---
def draw_ui(frame, bpm, sdnn, rmssd, pnn50, status, color, graph_data):
    h, w, _ = frame.shape
    
    # Draw semi-transparent side panel
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (300, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    # Text Setup
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, "AI STRESS ENGINE", (20, 40), font, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, "-"*30, (20, 60), font, 0.5, (255, 255, 255), 1)
    
    if bpm == 0:
        cv2.putText(frame, "STATUS: ANALYZING...", (20, 100), font, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, "Hold perfectly still", (20, 130), font, 0.5, (200, 200, 200), 1)
    else:
        # Status
        cv2.putText(frame, f"STATUS: {status}", (20, 100), font, 0.6, color, 2)
        
        # Metrics
        cv2.putText(frame, f"BPM:   {bpm:.1f}", (20, 160), font, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"SDNN:  {sdnn:.1f} ms", (20, 200), font, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"RMSSD: {rmssd:.1f} ms", (20, 240), font, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"pNN50: {pnn50:.1f} %", (20, 280), font, 0.7, (255, 255, 255), 2)
        
    # Draw the Live Graph at the bottom
    if len(graph_data) > 0:
        graph_h, graph_w = 150, w - 320
        cv2.rectangle(overlay, (310, h - graph_h - 10), (w - 10, h - 10), (30, 30, 30), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Normalize graph data to fit the box
        norm_data = np.interp(graph_data, (graph_data.min(), graph_data.max()), (0, graph_h - 20))
        pts = []
        for i, val in enumerate(norm_data):
            x = 320 + int(i * (graph_w / len(norm_data)))
            y = h - 20 - int(val)
            pts.append((x, y))
            
        if len(pts) > 1:
            cv2.polylines(frame, [np.array(pts, dtype=np.int32)], False, (0, 255, 100), 2)
            cv2.putText(frame, "Live 250Hz rPPG Signal", (320, h - graph_h + 10), font, 0.5, (200, 200, 200), 1)

# --- MAIN SYSTEM ---
def run_system():
    print("Loading AI Models...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        clf = joblib.load(os.path.join(script_dir, 'models', 'stress_classifier.pkl'))
        scaler = joblib.load(os.path.join(script_dir, 'models', 'scaler.pkl'))
    except FileNotFoundError:
        print("CRITICAL ERROR: Models not found. Run classifier.py first.")
        return

    print("Booting Camera HUD...")
    cap = cv2.VideoCapture(0)
    
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False)
    
    BUFFER_SIZE = 250
    raw_signal, timestamps = [], []
    bpm_history, sdnn_history, rmssd_history, pnn50_history, prediction_history = deque(maxlen=45), deque(maxlen=45), deque(maxlen=45), deque(maxlen=45), deque(maxlen=45)
    
    # UI State Variables
    display_bpm = display_sdnn = display_rmssd = display_pnn50 = 0.0
    status_text = "INITIALIZING"
    status_color = (0, 255, 255) # Yellow
    live_wave = np.zeros(250)
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1) # Mirror image for better UX
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                y_min = int(face_landmarks.landmark[10].y * h)
                y_max = int(face_landmarks.landmark[151].y * h)
                x_min = int(face_landmarks.landmark[67].x * w)
                x_max = int(face_landmarks.landmark[297].x * w)
                
                if y_min < y_max and x_min < x_max and y_min > 0 and x_min > 0:
                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 100), 2)
                    roi_frame = frame[y_min:y_max, x_min:x_max]
                    
                    if roi_frame.size > 0:
                        b_mean, g_mean, r_mean = np.mean(roi_frame[:, :, 0]), np.mean(roi_frame[:, :, 1]), np.mean(roi_frame[:, :, 2])
                        g_normalized = g_mean / (r_mean + g_mean + b_mean + 1e-6)
                        
                        raw_signal.append(g_normalized)
                        timestamps.append(time.time())
                        
                        # Buffer UI Progress
                        if len(raw_signal) < BUFFER_SIZE:
                            status_text = f"BUFFERING: {len(raw_signal)}/{BUFFER_SIZE}"
                            status_color = (0, 255, 255)
                        else:
                            # --- MATH PIPELINE ---
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
                                    live_wave = upsampled_signal[-250:] # Keep last 250 points for drawing
                                    
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
                                            
                                            features = np.array([[bpm, sdnn, rmssd, pnn50]])
                                            scaled_features = scaler.transform(features)
                                            ml_prediction = clf.predict(scaled_features)[0]
                                            
                                            bpm_history.append(bpm)
                                            sdnn_history.append(sdnn)
                                            rmssd_history.append(rmssd)
                                            pnn50_history.append(pnn50)
                                            prediction_history.append(ml_prediction)
                                            
                                            if len(bpm_history) > 15:
                                                display_bpm = np.mean(bpm_history)
                                                display_sdnn = np.mean(sdnn_history)
                                                display_rmssd = np.mean(rmssd_history)
                                                display_pnn50 = np.mean(pnn50_history)
                                                most_common_pred = mode(prediction_history, keepdims=True).mode[0]
                                            else:
                                                display_bpm, display_sdnn, display_rmssd, display_pnn50 = bpm, sdnn, rmssd, pnn50
                                                most_common_pred = ml_prediction
                                                
                                            # Hybrid Logic
                                            if display_bpm > 95.0 or display_rmssd < 20.0:
                                                status_text = "HIGH STRESS"
                                                status_color = (0, 0, 255) # Red
                                            else:
                                                if most_common_pred == 0:
                                                    status_text = "RELAXED"
                                                    status_color = (0, 255, 0) # Green
                                                else:
                                                    status_text = "HIGH STRESS"
                                                    status_color = (0, 0, 255) # Red
                                        else:
                                            status_text = "NOISY SIGNAL"
                                            status_color = (0, 165, 255) # Orange
                                    else:
                                        status_text = "SEARCHING PEAKS"
                                        status_color = (0, 255, 255)
                                except ValueError:
                                    pass
                            
                            raw_signal.pop(0)
                            timestamps.pop(0)

        # Draw the HUD
        draw_ui(frame, display_bpm, display_sdnn, display_rmssd, display_pnn50, status_text, status_color, live_wave)
        
        cv2.imshow("AI Stress Detection System", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_system()