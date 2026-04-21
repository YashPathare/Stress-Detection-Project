# import cv2
# import numpy as np
# from scipy import signal
# from scipy.interpolate import CubicSpline
# import matplotlib.pyplot as plt
# import os
# import mediapipe as mp

# def validate_dataset_2(subject_folder):
#     print("--- STARTING UBFC DATASET 2 VALIDATION (High Stress) ---")
    
#     # Handle the file name whether it has a space or not
#     video_path = os.path.join(subject_folder, 'vid (1).avi')
#     if not os.path.exists(video_path):
#         video_path = os.path.join(subject_folder, 'vid(1).avi')
        
#     gt_txt_path = os.path.join(subject_folder, 'ground_truth.txt')
    
#     if not os.path.exists(video_path):
#         print(f"Error: Could not find vid (1).avi or vid(1).avi in {subject_folder}")
#         return
#     if not os.path.exists(gt_txt_path):
#         print(f"Error: Could not find ground_truth.txt in {subject_folder}")
#         return

#     print("Parsing Dataset 2 format (ground_truth.txt) for Heart Rate...")
#     gt_hr_full = []
#     with open(gt_txt_path, 'r') as f:
#         lines = f.readlines()
#         if len(lines) >= 2:
#             gt_hr_full = [float(x) for x in lines[1].strip().split()]
                
#     if not gt_hr_full:
#         print("Error: Could not extract Heart Rate data.")
#         return
        
#     true_bpm = np.mean(gt_hr_full)
#     print(f"Clinical Ground-Truth Average BPM: {true_bpm:.2f}")

#     print("Processing video frames through MediaPipe...")
#     cap = cv2.VideoCapture(video_path)
#     fps = cap.get(cv2.CAP_PROP_FPS)
#     if fps == 0: fps = 30.0 
    
#     mp_face_mesh = mp.solutions.face_mesh
#     face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False)
    
#     raw_signal = []
    
#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret: break
            
#         frame_height, frame_width, _ = frame.shape
#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = face_mesh.process(rgb_frame)
        
#         if results.multi_face_landmarks:
#             for face_landmarks in results.multi_face_landmarks:
#                 y_min = int(face_landmarks.landmark[10].y * frame_height)
#                 y_max = int(face_landmarks.landmark[151].y * frame_height)
#                 x_min = int(face_landmarks.landmark[67].x * frame_width)
#                 x_max = int(face_landmarks.landmark[297].x * frame_width)
                
#                 if y_min < y_max and x_min < x_max and y_min > 0 and x_min > 0:
#                     roi_frame = frame[y_min:y_max, x_min:x_max]
#                     if roi_frame.size > 0:
#                         b_mean = np.mean(roi_frame[:, :, 0])
#                         g_mean = np.mean(roi_frame[:, :, 1])
#                         r_mean = np.mean(roi_frame[:, :, 2])
#                         g_normalized = g_mean / (r_mean + g_mean + b_mean + 1e-6)
#                         raw_signal.append(g_normalized)
#         else:
#             if len(raw_signal) > 0: raw_signal.append(raw_signal[-1])
#             else: raw_signal.append(0.33)

#     cap.release()
#     print(f"Video processed. Extracted {len(raw_signal)} optical frames.")

#     sig = np.array(raw_signal)
#     t = np.arange(len(sig)) / fps
#     detrended = signal.detrend(sig)
#     normalized = (detrended - np.mean(detrended)) / np.std(detrended)
#     b, a = signal.butter(3, [0.8 / (0.5 * fps), 3.0 / (0.5 * fps)], btype='band')
#     filtered = signal.filtfilt(b, a, normalized)
    
#     new_fps = 250.0  
#     num_points = int(len(sig) * (new_fps / fps))
#     new_t = np.linspace(t[0], t[-1], num_points)
#     cs = CubicSpline(t, filtered)
#     upsampled_signal = cs(new_t)
#     peaks, _ = signal.find_peaks(upsampled_signal, distance=new_fps*0.4) 
    
#     if len(peaks) > 3:
#         raw_ibis = np.diff(new_t[peaks])
#         valid_ibis = raw_ibis[(raw_ibis > 0.33) & (raw_ibis < 1.5)]
#         estimated_bpm = 60.0 / np.mean(valid_ibis)
#     else:
#         estimated_bpm = 0.0
        
#     print(f"Algorithm Estimated Average BPM: {estimated_bpm:.2f}")
#     mae = abs(true_bpm - estimated_bpm)
#     print("\n" + "="*40)
#     print(f"MEAN ABSOLUTE ERROR (MAE): {mae:.2f} BPM")
#     print("="*40)

#     plt.figure(figsize=(12, 6))
#     plt.title(f"Algorithm Validation: UBFC Dataset 2 (High Stress)\nMAE: {mae:.2f} BPM (True: {true_bpm:.1f} | Est: {estimated_bpm:.1f})", fontsize=14, fontweight='bold')
#     window_limit = int(new_fps * 10) 
#     plt.plot(new_t[:window_limit], upsampled_signal[:window_limit], label='Cubic Spline 250Hz rPPG', color='#2ecc71', linewidth=2)
#     valid_peaks = peaks[peaks < window_limit]
#     plt.plot(new_t[valid_peaks], upsampled_signal[valid_peaks], "x", color='#e74c3c', markersize=8, label='Detected Heartbeats', markeredgewidth=2)
#     plt.xlabel("Time (seconds)", fontsize=12)
#     plt.ylabel("Normalized Blood Volume Pulse", fontsize=12)
#     plt.legend()
#     plt.grid(True, linestyle='--', alpha=0.7)
#     plt.tight_layout()
#     plt.show()

# if __name__ == "__main__":
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     project_root = os.path.abspath(os.path.join(script_dir, '..'))
#     validate_dataset_2(project_root)

#Code for Generalization Accuracy
# import cv2
# import numpy as np
# from scipy import signal
# from scipy.interpolate import CubicSpline
# import matplotlib.pyplot as plt
# import os
# import joblib
# import warnings
# import mediapipe as mp

# warnings.filterwarnings("ignore", category=UserWarning)

# def validate_dataset_2(project_root, subject_folder):
#     print("--- STARTING UBFC DATASET 2 VALIDATION (High Stress ML Testing) ---")
    
#     video_path = os.path.join(subject_folder, 'vid (1).avi')
#     if not os.path.exists(video_path):
#         video_path = os.path.join(subject_folder, 'vid(1).avi')
        
#     if not os.path.exists(video_path):
#         print(f"Error: Could not find vid (1).avi or vid(1).avi in {subject_folder}")
#         return

#     # --- 1. LOAD YOUR CUSTOM AI MODEL ---
#     model_path = os.path.join(project_root, 'models', 'stress_classifier.pkl')
#     scaler_path = os.path.join(project_root, 'models', 'scaler.pkl')
#     try:
#         clf = joblib.load(model_path)
#         scaler = joblib.load(scaler_path)
#     except FileNotFoundError:
#         print("Error: Could not find ML models. Run classifier.py first.")
#         return

#     # --- 2. EXTRACT RAW OPTICAL DATA ---
#     print("Processing video frames through MediaPipe...")
#     cap = cv2.VideoCapture(video_path)
#     fps = cap.get(cv2.CAP_PROP_FPS)
#     if fps == 0: fps = 30.0 
    
#     mp_face_mesh = mp.solutions.face_mesh
#     face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False)
#     raw_signal = []
    
#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret: break
            
#         frame_height, frame_width, _ = frame.shape
#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = face_mesh.process(rgb_frame)
        
#         if results.multi_face_landmarks:
#             for face_landmarks in results.multi_face_landmarks:
#                 y_min = int(face_landmarks.landmark[10].y * frame_height)
#                 y_max = int(face_landmarks.landmark[151].y * frame_height)
#                 x_min = int(face_landmarks.landmark[67].x * frame_width)
#                 x_max = int(face_landmarks.landmark[297].x * frame_width)
                
#                 if y_min < y_max and x_min < x_max and y_min > 0 and x_min > 0:
#                     roi_frame = frame[y_min:y_max, x_min:x_max]
#                     if roi_frame.size > 0:
#                         b_mean = np.mean(roi_frame[:, :, 0])
#                         g_mean = np.mean(roi_frame[:, :, 1])
#                         r_mean = np.mean(roi_frame[:, :, 2])
#                         g_normalized = g_mean / (r_mean + g_mean + b_mean + 1e-6)
#                         raw_signal.append(g_normalized)
#         else:
#             if len(raw_signal) > 0: raw_signal.append(raw_signal[-1])
#             else: raw_signal.append(0.33)
#     cap.release()

#     # --- 3. SLIDING WINDOW ML INFERENCE ---
#     print(f"Video processed. Running Machine Learning Inference on {len(raw_signal)} frames...")
    
#     BUFFER_SIZE = 250
#     STRIDE = 30 
    
#     total_predictions = 0
#     correct_predictions = 0 # Dataset 2 is High Stress, so Correct = 1
    
#     for i in range(BUFFER_SIZE, len(raw_signal), STRIDE):
#         window = np.array(raw_signal[i-BUFFER_SIZE:i])
#         t = np.arange(BUFFER_SIZE) / fps
        
#         detrended = signal.detrend(window)
#         if np.std(detrended) == 0: continue
#         normalized = (detrended - np.mean(detrended)) / np.std(detrended)
        
#         try:
#             b, a = signal.butter(3, [0.8 / (0.5 * fps), 3.0 / (0.5 * fps)], btype='band')
#             filtered = signal.filtfilt(b, a, normalized)
            
#             new_fps = 250.0  
#             num_points = int((t[-1] - t[0]) * new_fps)
#             new_t = np.linspace(t[0], t[-1], num_points)
#             cs = CubicSpline(t, filtered)
#             upsampled_signal = cs(new_t)
            
#             peaks, _ = signal.find_peaks(upsampled_signal, distance=new_fps*0.4) 
            
#             if len(peaks) > 3:
#                 raw_ibis = np.diff(new_t[peaks])
#                 valid_ibis = raw_ibis[(raw_ibis > 0.33) & (raw_ibis < 1.5)]
                
#                 if len(valid_ibis) > 3:
#                     bpm = 60.0 / np.mean(valid_ibis)
#                     sdnn = np.std(valid_ibis) * 1000 
#                     rmssd = np.sqrt(np.mean(np.square(np.diff(valid_ibis)))) * 1000
#                     nn50 = np.sum(np.abs(np.diff(valid_ibis * 1000)) > 50)
#                     pnn50 = (nn50 / len(valid_ibis)) * 100
                    
#                     # AI PREDICTION
#                     features = np.array([[bpm, sdnn, rmssd, pnn50]])
#                     scaled_features = scaler.transform(features)
#                     ml_prediction = clf.predict(scaled_features)[0]
                    
#                     # --- HYBRID HEURISTIC OVERRIDE ---
#                     # If the BPM is clinically high (>95), we override the AI because we know 
#                     # the RMSSD is likely artificially inflated by motion artifacts!
#                     if bpm >= 95.0:
#                         final_prediction = 1
#                     else:
#                         final_prediction = ml_prediction
                    
#                     total_predictions += 1
#                     if final_prediction == 1: # 1 is High Stress (Correct for Dataset 2)
#                         correct_predictions += 1
#         except ValueError:
#             continue

#     if total_predictions > 0:
#         accuracy = (correct_predictions / total_predictions) * 100
#         print("\n" + "="*50)
#         print("--- CROSS-DATASET HYBRID ML RESULTS ---")
#         print(f"Target Label: HIGH STRESS (1)")
#         print(f"Total AI Inferences Run: {total_predictions}")
#         print(f"Correct Classifications: {correct_predictions}")
#         print(f"GENERALIZATION ACCURACY: {accuracy:.2f}%")
#         print("="*50)
#     else:
#         print("Not enough valid signals to make ML predictions.")

# if __name__ == "__main__":
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     project_root = os.path.abspath(os.path.join(script_dir, '..'))
#     validate_dataset_2(project_root, project_root)

import cv2
import numpy as np
from scipy import signal
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt
import os
import joblib
import warnings
import mediapipe as mp

warnings.filterwarnings("ignore", category=UserWarning)

def validate_dataset_2(project_root, subject_folder):
    print("--- STARTING UBFC DATASET 2 VALIDATION (Pure ML Testing) ---")
    
    video_path = os.path.join(subject_folder, 'vid (1).avi')
    if not os.path.exists(video_path):
        video_path = os.path.join(subject_folder, 'vid(1).avi')
        
    if not os.path.exists(video_path):
        print(f"Error: Could not find vid (1).avi or vid(1).avi in {subject_folder}")
        return

    # --- 1. LOAD YOUR CUSTOM AI MODEL ---
    model_path = os.path.join(project_root, 'models', 'stress_classifier.pkl')
    scaler_path = os.path.join(project_root, 'models', 'scaler.pkl')
    try:
        clf = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
    except FileNotFoundError:
        print("Error: Could not find ML models. Run classifier.py first.")
        return

    # --- 2. EXTRACT RAW OPTICAL DATA ---
    print("Processing video frames through MediaPipe...")
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 30.0 
    
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False)
    raw_signal = []
    
    while cap.isOpened():
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
                    roi_frame = frame[y_min:y_max, x_min:x_max]
                    if roi_frame.size > 0:
                        b_mean = np.mean(roi_frame[:, :, 0])
                        g_mean = np.mean(roi_frame[:, :, 1])
                        r_mean = np.mean(roi_frame[:, :, 2])
                        g_normalized = g_mean / (r_mean + g_mean + b_mean + 1e-6)
                        raw_signal.append(g_normalized)
        else:
            if len(raw_signal) > 0: raw_signal.append(raw_signal[-1])
            else: raw_signal.append(0.33)
    cap.release()

    # --- 3. SLIDING WINDOW ML INFERENCE ---
    print(f"Video processed. Running Machine Learning Inference on {len(raw_signal)} frames...")
    
    BUFFER_SIZE = 250
    STRIDE = 30 
    
    total_predictions = 0
    correct_predictions = 0 # Dataset 2 is High Stress, so Correct = 1
    
    for i in range(BUFFER_SIZE, len(raw_signal), STRIDE):
        window = np.array(raw_signal[i-BUFFER_SIZE:i])
        t = np.arange(BUFFER_SIZE) / fps
        
        detrended = signal.detrend(window)
        if np.std(detrended) == 0: continue
        normalized = (detrended - np.mean(detrended)) / np.std(detrended)
        
        try:
            b, a = signal.butter(3, [0.8 / (0.5 * fps), 3.0 / (0.5 * fps)], btype='band')
            filtered = signal.filtfilt(b, a, normalized)
            
            new_fps = 250.0  
            num_points = int((t[-1] - t[0]) * new_fps)
            new_t = np.linspace(t[0], t[-1], num_points)
            cs = CubicSpline(t, filtered)
            upsampled_signal = cs(new_t)
            
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
                    
                    # AI PREDICTION (Pure ML, No Heuristics)
                    features = np.array([[bpm, sdnn, rmssd, pnn50]])
                    scaled_features = scaler.transform(features)
                    ml_prediction = clf.predict(scaled_features)[0]
                    
                    total_predictions += 1
                    if ml_prediction == 1: # 1 is High Stress (Correct for Dataset 2)
                        correct_predictions += 1
        except ValueError:
            continue

    if total_predictions > 0:
        accuracy = (correct_predictions / total_predictions) * 100
        print("\n" + "="*50)
        print("--- CROSS-DATASET PURE ML RESULTS ---")
        print(f"Target Label: HIGH STRESS (1)")
        print(f"Total AI Inferences Run: {total_predictions}")
        print(f"Correct Classifications: {correct_predictions}")
        print(f"GENERALIZATION ACCURACY: {accuracy:.2f}%")
        print("="*50)
    else:
        print("Not enough valid signals to make ML predictions.")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    validate_dataset_2(project_root, project_root)