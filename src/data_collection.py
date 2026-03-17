import cv2
import time
import numpy as np
from scipy import signal
import csv
import os
import mediapipe as mp # NEW: Importing advanced tracking

def collect_training_data():
    # 1. Ask the user for the current stress label
    print("--- DATA COLLECTION MODE V2 ---")
    print("0: Low Stress (Resting, calm, stable lighting)")
    print("1: High Stress (Cognitive load, gaming, math test)")
    label_input = input("Enter the label for this session (0 or 1): ")
    
    if label_input not in ['0', '1']:
        print("Invalid input. Exiting.")
        return
        
    stress_label = int(label_input)
    
    # 2. Ensure the data directory exists
    script_dir = os.path.dirname(os.path.abspath(__file__))
    processed_dir = os.path.join(script_dir, '..', 'data', 'processed')
    
    os.makedirs(processed_dir, exist_ok=True)
    csv_file_path = os.path.join(processed_dir, 'stress_dataset.csv')
    
    # Write headers if the file doesn't exist yet
    file_exists = os.path.isfile(csv_file_path)
    
    # --- INITIALIZE CAMERA & MEDIAPIPE TRACKING ---
    cap = cv2.VideoCapture(0)
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False, 
                                      min_detection_confidence=0.5, min_tracking_confidence=0.5)
    
    BUFFER_SIZE = 250 
    raw_signal = []
    timestamps = []
    
    print(f"\nRecording CLEAN Data for Label: {'High' if stress_label == 1 else 'Low'} Stress")
    print("Press 'q' to stop recording and save.")
    
    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['timestamp', 'bpm', 'sdnn', 'rmssd', 'pnn50', 'label'])
            
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            frame_height, frame_width, _ = frame.shape
            
            # MediaPipe requires RGB images
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    
                    # Extract specific forehead landmarks
                    y_min = int(face_landmarks.landmark[10].y * frame_height)
                    y_max = int(face_landmarks.landmark[151].y * frame_height)
                    x_min = int(face_landmarks.landmark[67].x * frame_width)
                    x_max = int(face_landmarks.landmark[297].x * frame_width)
                    
                    if y_min < y_max and x_min < x_max and y_min > 0 and x_min > 0:
                        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                        roi_frame = frame[y_min:y_max, x_min:x_max]
                        
                        if roi_frame.size > 0:
                            # --- UPGRADE 1: LIGHTING NORMALIZATION ---
                            b_mean = np.mean(roi_frame[:, :, 0])
                            g_mean = np.mean(roi_frame[:, :, 1])
                            r_mean = np.mean(roi_frame[:, :, 2])
                            
                            g_normalized = g_mean / (r_mean + g_mean + b_mean + 1e-6)
                            
                            raw_signal.append(g_normalized)
                            timestamps.append(time.time())
                            
                            if len(raw_signal) > BUFFER_SIZE:
                                raw_signal.pop(0)
                                timestamps.pop(0)
                                
                            if len(raw_signal) == BUFFER_SIZE:
                                sig, t = np.array(raw_signal), np.array(timestamps)
                                fps = BUFFER_SIZE / (t[-1] - t[0])
                                
                                detrended = signal.detrend(sig)
                                normalized = (detrended - np.mean(detrended)) / np.std(detrended)
                                
                                try:
                                    b, a = signal.butter(3, [0.8 / (0.5 * fps), 3.0 / (0.5 * fps)], btype='band')
                                    filtered = signal.filtfilt(b, a, normalized)
                                    peaks, _ = signal.find_peaks(filtered, distance=fps*0.4) 
                                    
                                    if len(peaks) > 3:
                                        raw_ibis = np.diff(t[peaks])
                                        
                                        # --- UPGRADE 2: PHYSIOLOGICAL OUTLIER REJECTION ---
                                        valid_ibis = raw_ibis[(raw_ibis > 0.33) & (raw_ibis < 1.5)]
                                        
                                        if len(valid_ibis) > 3:
                                            bpm = 60.0 / np.mean(valid_ibis)
                                            sdnn = np.std(valid_ibis) * 1000 
                                            rmssd = np.sqrt(np.mean(np.square(np.diff(valid_ibis)))) * 1000

                                            # NEW: pNN50 Metric for Prof. Mishra
                                            nn50 = np.sum(np.abs(np.diff(valid_ibis * 1000)) > 50)
                                            pnn50 = (nn50 / len(valid_ibis)) * 100

                                            # 3. LOG THE DATA TO CSV (Don't forget to update your header row at the top of the script too!)
                                            writer.writerow([time.time(), round(bpm, 2), round(sdnn, 2), round(rmssd, 2), round(pnn50, 2), stress_label])
                                            
                                            # UI Feedback
                                            cv2.putText(frame, "RECORDING CLEAN DATA...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                                            cv2.putText(frame, f"BPM: {bpm:.1f} | RMSSD: {rmssd:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                                except ValueError:
                                    pass 
                # Break removed so MediaPipe loops correctly

            cv2.imshow('Data Collection Mode V2', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    cap.release()
    cv2.destroyAllWindows()
    print(f"Data successfully appended to {csv_file_path}")

if __name__ == "__main__":
    collect_training_data()