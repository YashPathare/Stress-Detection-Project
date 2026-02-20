import cv2
import time
import numpy as np
from scipy import signal
import csv
import os

def collect_training_data():
    # 1. Ask the user for the current stress label
    print("--- DATA COLLECTION MODE ---")
    print("0: Low Stress (Resting, calm)")
    print("1: High Stress (Cognitive load, gaming, math test)")
    label_input = input("Enter the label for this session (0 or 1): ")
    
    if label_input not in ['0', '1']:
        print("Invalid input. Exiting.")
        return
        
    stress_label = int(label_input)
    
    # 2. Ensure the data directory exists (using absolute paths to prevent errors)
    # This finds the exact folder this script is in (src/), goes up one level, and into data/processed/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    processed_dir = os.path.join(script_dir, '..', 'data', 'processed')
    
    os.makedirs(processed_dir, exist_ok=True)
    csv_file_path = os.path.join(processed_dir, 'stress_dataset.csv')
    
    # Write headers if the file doesn't exist yet
    file_exists = os.path.isfile(csv_file_path)
    
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    BUFFER_SIZE = 250 
    raw_signal = []
    timestamps = []
    
    print(f"\nRecording Data for Label: {'High' if stress_label == 1 else 'Low'} Stress")
    print("Press 'q' to stop recording and save.")
    
    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['timestamp', 'bpm', 'sdnn', 'rmssd', 'label'])
            
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                roi_x, roi_y, roi_w, roi_h = x + int(w * 0.25), y + int(h * 0.05), int(w * 0.5), int(h * 0.15)
                cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (0, 255, 0), 2)
                
                roi_frame = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
                if roi_frame.size > 0:
                    g_mean = np.mean(roi_frame[:, :, 1])
                    raw_signal.append(g_mean)
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
                                ibis = np.diff(t[peaks])
                                bpm = 60.0 / np.mean(ibis)
                                sdnn = np.std(ibis) * 1000 
                                rmssd = np.sqrt(np.mean(np.square(np.diff(ibis)))) * 1000
                                
                                # 3. LOG THE DATA TO CSV
                                writer.writerow([time.time(), round(bpm, 2), round(sdnn, 2), round(rmssd, 2), stress_label])
                                
                                # UI Feedback
                                cv2.putText(frame, "RECORDING DATA TO CSV...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                                cv2.putText(frame, f"BPM: {bpm:.1f} | RMSSD: {rmssd:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        except ValueError:
                            pass 
                break 

            cv2.imshow('Data Collection Mode', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    cap.release()
    cv2.destroyAllWindows()
    print(f"Data successfully appended to {csv_file_path}")

if __name__ == "__main__":
    collect_training_data()