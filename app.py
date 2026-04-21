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
import streamlit as st

warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(page_title="AI Stress Dashboard", page_icon="🫀", layout="wide")
st.title("🫀 Real-Time Biomarker & Stress Analysis")

@st.cache_resource
def load_models():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, 'models', 'stress_classifier.pkl')
    scaler_path = os.path.join(script_dir, 'models', 'scaler.pkl')
    try:
        clf = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        return clf, scaler
    except FileNotFoundError:
        return None, None

clf, scaler = load_models()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Live Optical Feed")
    frame_placeholder = st.empty()
    st.subheader("Live Blood Volume Pulse (rPPG)")
    graph_placeholder = st.empty() # NEW: Live mathematical graph!

with col2:
    st.subheader("Physiological Metrics")
    status_placeholder = st.empty()
    
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        bpm_metric = st.empty()
        rmssd_metric = st.empty()
    with m_col2:
        sdnn_metric = st.empty()
        pnn50_metric = st.empty()
        
    st.markdown("---")
    st.markdown("**System Status:**")
    buffer_progress = st.progress(0)
    buffer_text = st.empty()

run = st.sidebar.checkbox("🟢 Start Camera & AI Engine")

if not clf:
    st.error("Missing ML models! Run classifier.py first.")

if run and clf and scaler:
    cap = cv2.VideoCapture(0) 
    
    if cap.isOpened():
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False)
        
        BUFFER_SIZE = 250 
        raw_signal, timestamps = [], []
        bpm_history, sdnn_history, rmssd_history, pnn50_history, prediction_history = deque(maxlen=45), deque(maxlen=45), deque(maxlen=45), deque(maxlen=45), deque(maxlen=45)
        
        while run:
            ret, frame = cap.read()
            if not ret: break
                
            frame_height, frame_width, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    y_min = int(face_landmarks.landmark[10].y * frame_height)
                    y_max = int(face_landmarks.landmark[151].y * frame_height)
                    x_min = int(face_landmarks.landmark[67].x * frame_width)
                    x_max = int(face_landmarks.landmark[297].x * frame_width)
                    
                    if y_min < y_max and x_min < x_max and y_min > 0 and x_min > 0:
                        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 100), 2)
                        roi_frame = frame[y_min:y_max, x_min:x_max]
                        
                        if roi_frame.size > 0:
                            b_mean, g_mean, r_mean = np.mean(roi_frame[:, :, 0]), np.mean(roi_frame[:, :, 1]), np.mean(roi_frame[:, :, 2])
                            g_normalized = g_mean / (r_mean + g_mean + b_mean + 1e-6)
                            
                            raw_signal.append(g_normalized)
                            timestamps.append(time.time())
                            
                            current_len = len(raw_signal)
                            if current_len < BUFFER_SIZE:
                                buffer_progress.progress(current_len / BUFFER_SIZE)
                                buffer_text.text(f"Filling AI Buffer... {current_len}/{BUFFER_SIZE}")
                            else:
                                buffer_progress.progress(1.0)
                                buffer_text.text("Buffer Full. AI Inference Active 🟢")
                                
                                # --- 1. RUN THE MATH FIRST (While buffer is exactly 250) ---
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
                                        
                                        # DRAW THE LIVE GRAPH 
                                        graph_placeholder.line_chart(upsampled_signal)
                                        
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
                                                    
                                                bpm_metric.metric("Heart Rate", f"{display_bpm:.1f} BPM")
                                                sdnn_metric.metric("SDNN", f"{display_sdnn:.1f} ms")
                                                rmssd_metric.metric("RMSSD", f"{display_rmssd:.1f} ms")
                                                pnn50_metric.metric("pNN50", f"{display_pnn50:.1f} %")
                                                
                                                if display_bpm > 95.0 or display_rmssd < 20.0:
                                                    status_placeholder.error("🚨 HIGH STRESS DETECTED (Heuristic Override)")
                                                else:
                                                    if most_common_pred == 0:
                                                        status_placeholder.success("✅ LOW STRESS (ML Stabilized)")
                                                    else:
                                                        status_placeholder.error("🚨 HIGH STRESS (ML Stabilized)")
                                            else:
                                                status_placeholder.warning("⚠️ Signal noisy. Found peaks, but timings are invalid.")
                                        else:
                                            status_placeholder.warning("⚠️ Analyzing... Hold perfectly still.")
                                            
                                    except ValueError:
                                        pass
                                
                                # --- 2. POP THE OLDEST FRAME NOW THAT MATH IS DONE ---
                                raw_signal.pop(0)
                                timestamps.pop(0)
                                        
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame, channels="RGB", use_container_width=True)

        cap.release()