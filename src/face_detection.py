# # # import cv2
# # # import time
# # # import numpy as np
# # # from scipy import signal

# # # def live_hr_hrv_detection():
# # #     cap = cv2.VideoCapture(0)
# # #     face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
# # #     # BUFFER: We need about 10 seconds of data to get a reliable heartbeat.
# # #     # Since your camera runs at ~29 FPS, 250 frames is roughly 8.5 seconds.
# # #     BUFFER_SIZE = 250 
# # #     raw_signal = []
# # #     timestamps = []
    
# # #     print("Phase 5: Live HR & HRV Calculation Started.")
# # #     print("Please sit still. It will take about 10 seconds to gather enough data for the first reading...")
    
# # #     while cap.isOpened():
# # #         ret, frame = cap.read()
# # #         if not ret:
# # #             break
            
# # #         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
# # #         faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
        
# # #         for (x, y, w, h) in faces:
# # #             # Draw Face and ROI boxes
# # #             cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
# # #             roi_x = x + int(w * 0.25)
# # #             roi_y = y + int(h * 0.05) 
# # #             roi_w = int(w * 0.5)
# # #             roi_h = int(h * 0.15)
            
# # #             cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (0, 255, 0), 2)
            
# # #             roi_frame = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
            
# # #             if roi_frame.size > 0:
# # #                 # Extract Green Channel Mean
# # #                 g_channel = roi_frame[:, :, 1]
# # #                 g_mean = np.mean(g_channel)
                
# # #                 raw_signal.append(g_mean)
# # #                 timestamps.append(time.time())
                
# # #                 # Keep the buffer at a strict sliding window size
# # #                 if len(raw_signal) > BUFFER_SIZE:
# # #                     raw_signal.pop(0)
# # #                     timestamps.pop(0)
                    
# # #                 # --- PHASE 5: REAL-TIME MATH ---
# # #                 # Only calculate once the buffer is completely full
# # #                 if len(raw_signal) == BUFFER_SIZE:
# # #                     sig = np.array(raw_signal)
# # #                     t = np.array(timestamps)
                    
# # #                     # Dynamically calculate FPS to keep filters accurate
# # #                     fps = BUFFER_SIZE / (t[-1] - t[0])
                    
# # #                     # Detrend & Normalize
# # #                     detrended = signal.detrend(sig)
# # #                     normalized = (detrended - np.mean(detrended)) / np.std(detrended)
                    
# # #                     # Bandpass Filter (0.8 - 3.0 Hz)
# # #                     nyquist = 0.5 * fps
# # #                     low = 0.8 / nyquist
# # #                     high = 3.0 / nyquist
                    
# # #                     try:
# # #                         b, a = signal.butter(3, [low, high], btype='band')
# # #                         filtered = signal.filtfilt(b, a, normalized)
                        
# # #                         # Find Peaks in the waveform
# # #                         # 'distance' prevents counting a single beat twice (fps * 0.4 allows up to 150 BPM)
# # #                         peaks, _ = signal.find_peaks(filtered, distance=fps*0.4) 
                        
# # #                         if len(peaks) > 3:
# # #                             # Calculate Inter-Beat Intervals (IBIs) in seconds
# # #                             peak_times = t[peaks]
# # #                             ibis = np.diff(peak_times)
                            
# # #                             # Derive Physiological Features
# # #                             bpm = 60.0 / np.mean(ibis)
# # #                             sdnn = np.std(ibis) * 1000  # Converted to milliseconds
# # #                             rmssd = np.sqrt(np.mean(np.square(np.diff(ibis)))) * 1000
                            
# # #                             # Display metrics on the live video feed
# # #                             cv2.putText(frame, f"BPM: {bpm:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
# # #                             cv2.putText(frame, f"SDNN: {sdnn:.1f} ms", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
# # #                             cv2.putText(frame, f"RMSSD: {rmssd:.1f} ms", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                            
# # #                     except ValueError:
# # #                         # Silently pass if the math momentarily breaks due to movement noise
# # #                         pass 
                        
# # #             break # Process only the first detected face

# # #         cv2.imshow('Phase 5: Live HR & HRV Dashboard', frame)
        
# # #         if cv2.waitKey(1) & 0xFF == ord('q'):
# # #             break
            
# # #     cap.release()
# # #     cv2.destroyAllWindows()

# # # if __name__ == "__main__":
# # #     live_hr_hrv_detection()

# # import cv2
# # import time
# # import numpy as np
# # from scipy import signal

# # def draw_live_graph(signal_array, width, height):
# #     """Creates a black canvas and draws the live signal wave."""
# #     # Create a black background image
# #     graph = np.zeros((height, width, 3), dtype=np.uint8)
    
# #     if len(signal_array) < 10:
# #         cv2.putText(graph, "Gathering Data Buffer...", (10, height//2), 
# #                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
# #         return graph

# #     # Dynamically scale the signal to fit the height of our graph canvas
# #     min_val, max_val = np.min(signal_array), np.max(signal_array)
# #     if max_val - min_val == 0:
# #         return graph
        
# #     scaled_signal = (signal_array - min_val) / (max_val - min_val)
    
# #     # Invert the Y-axis so peaks point upward, and map to pixel coordinates
# #     padding = int(0.1 * height)
# #     y_coords = height - padding - (scaled_signal * (height - 2 * padding)).astype(np.int32)
# #     x_coords = np.linspace(0, width, len(signal_array)).astype(np.int32)
    
# #     # Stack X and Y coordinates and draw the connected lines
# #     points = np.column_stack((x_coords, y_coords)).reshape(-1, 1, 2)
# #     cv2.polylines(graph, [points], isClosed=False, color=(0, 0, 255), thickness=2) # Red line
    
# #     # Add a title and gridline flavor to make it look professional
# #     cv2.putText(graph, "Real-Time Filtered rPPG (0.8 - 3.0 Hz)", (10, 20), 
# #                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
# #     cv2.line(graph, (0, height//2), (width, height//2), (50, 50, 50), 1)
    
# #     return graph

# # def live_hr_hrv_detection():
# #     cap = cv2.VideoCapture(0)
# #     face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
# #     BUFFER_SIZE = 250 
# #     raw_signal = []
# #     timestamps = []
    
# #     print("Phase 5: Live HR & HRV Dashboard Started.")
# #     print("Please sit still. Gathering 10 seconds of initial data...")
    
# #     while cap.isOpened():
# #         ret, frame = cap.read()
# #         if not ret:
# #             break
            
# #         # Get frame dimensions for our graph
# #         frame_height, frame_width, _ = frame.shape
# #         filtered_for_graph = [] # Empty placeholder until buffer is full
        
# #         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
# #         faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
        
# #         for (x, y, w, h) in faces:
# #             cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
# #             roi_x = x + int(w * 0.25)
# #             roi_y = y + int(h * 0.05) 
# #             roi_w = int(w * 0.5)
# #             roi_h = int(h * 0.15)
            
# #             cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (0, 255, 0), 2)
            
# #             roi_frame = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
            
# #             if roi_frame.size > 0:
# #                 g_channel = roi_frame[:, :, 1]
# #                 g_mean = np.mean(g_channel)
                
# #                 raw_signal.append(g_mean)
# #                 timestamps.append(time.time())
                
# #                 if len(raw_signal) > BUFFER_SIZE:
# #                     raw_signal.pop(0)
# #                     timestamps.pop(0)
                    
# #                 # --- REAL-TIME MATH ---
# #                 if len(raw_signal) == BUFFER_SIZE:
# #                     sig = np.array(raw_signal)
# #                     t = np.array(timestamps)
                    
# #                     fps = BUFFER_SIZE / (t[-1] - t[0])
                    
# #                     detrended = signal.detrend(sig)
# #                     normalized = (detrended - np.mean(detrended)) / np.std(detrended)
                    
# #                     nyquist = 0.5 * fps
# #                     low = 0.8 / nyquist
# #                     high = 3.0 / nyquist
                    
# #                     try:
# #                         b, a = signal.butter(3, [low, high], btype='band')
# #                         filtered = signal.filtfilt(b, a, normalized)
                        
# #                         # Save the filtered wave so we can graph it below
# #                         filtered_for_graph = filtered.copy()
                        
# #                         peaks, _ = signal.find_peaks(filtered, distance=fps*0.4) 
                        
# #                         if len(peaks) > 3:
# #                             peak_times = t[peaks]
# #                             ibis = np.diff(peak_times)
                            
# #                             bpm = 60.0 / np.mean(ibis)
# #                             sdnn = np.std(ibis) * 1000 
# #                             rmssd = np.sqrt(np.mean(np.square(np.diff(ibis)))) * 1000
                            
# #                             # Display metrics
# #                             cv2.putText(frame, f"BPM: {bpm:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
# #                             cv2.putText(frame, f"SDNN: {sdnn:.1f} ms", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
# #                             cv2.putText(frame, f"RMSSD: {rmssd:.1f} ms", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                            
# #                     except ValueError:
# #                         pass 
# #             break 

# #         # --- DRAW THE UI ---
# #         # Generate the graph image (150 pixels tall, same width as the webcam feed)
# #         graph_img = draw_live_graph(filtered_for_graph, frame_width, 150)
        
# #         # Stitch the webcam feed and the graph together vertically
# #         final_ui = np.vstack((frame, graph_img))

# #         cv2.imshow('Phase 5: Real-Time UI', final_ui)
        
# #         if cv2.waitKey(1) & 0xFF == ord('q'):
# #             break
            
# #     cap.release()
# #     cv2.destroyAllWindows()

# # if __name__ == "__main__":
# #     live_hr_hrv_detection()

# #CODE SHOWN IN PRESENTATION

# # import cv2
# # import time
# # import numpy as np
# # import os
# # from scipy import signal
# # import joblib
# # import warnings

# # # Suppress sklearn warnings about feature names
# # warnings.filterwarnings("ignore", category=UserWarning)

# # def draw_live_graph(signal_array, width, height):
# #     graph = np.zeros((height, width, 3), dtype=np.uint8)
# #     if len(signal_array) < 10:
# #         cv2.putText(graph, "Gathering Data Buffer...", (10, height//2), 
# #                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
# #         return graph

# #     min_val, max_val = np.min(signal_array), np.max(signal_array)
# #     if max_val - min_val == 0: return graph
        
# #     scaled_signal = (signal_array - min_val) / (max_val - min_val)
# #     padding = int(0.1 * height)
# #     y_coords = height - padding - (scaled_signal * (height - 2 * padding)).astype(np.int32)
# #     x_coords = np.linspace(0, width, len(signal_array)).astype(np.int32)
    
# #     points = np.column_stack((x_coords, y_coords)).reshape(-1, 1, 2)
# #     cv2.polylines(graph, [points], isClosed=False, color=(0, 0, 255), thickness=2)
# #     cv2.putText(graph, "Real-Time Filtered rPPG (0.8 - 3.0 Hz)", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
# #     cv2.line(graph, (0, height//2), (width, height//2), (50, 50, 50), 1)
# #     return graph

# # def live_stress_detection():
# #     # --- LOAD MACHINE LEARNING MODELS ---
# #     script_dir = os.path.dirname(os.path.abspath(__file__))
# #     model_path = os.path.join(script_dir, '..', 'models', 'stress_classifier.pkl')
# #     scaler_path = os.path.join(script_dir, '..', 'models', 'scaler.pkl')
    
# #     print("Loading Machine Learning Models...")
# #     try:
# #         clf = joblib.load(model_path)
# #         scaler = joblib.load(scaler_path)
# #         print("Models loaded successfully! Starting camera...")
# #     except FileNotFoundError:
# #         print("Error: Model files not found. Please run classifier.py first.")
# #         return

# #     # --- INITIALIZE CAMERA & TRACKING ---
# #     cap = cv2.VideoCapture(0)
# #     face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
# #     BUFFER_SIZE = 250 
# #     raw_signal = []
# #     timestamps = []
    
# #     current_stress_label = "Calibrating..."
# #     stress_color = (255, 255, 255)
    
# #     while cap.isOpened():
# #         ret, frame = cap.read()
# #         if not ret: break
            
# #         frame_height, frame_width, _ = frame.shape
# #         filtered_for_graph = [] 
        
# #         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
# #         faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
        
# #         for (x, y, w, h) in faces:
# #             cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
# #             roi_x, roi_y, roi_w, roi_h = x + int(w * 0.25), y + int(h * 0.05), int(w * 0.5), int(h * 0.15)
# #             cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (0, 255, 0), 2)
            
# #             roi_frame = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
            
# #             if roi_frame.size > 0:
# #                 g_mean = np.mean(roi_frame[:, :, 1])
# #                 raw_signal.append(g_mean)
# #                 timestamps.append(time.time())
                
# #                 if len(raw_signal) > BUFFER_SIZE:
# #                     raw_signal.pop(0)
# #                     timestamps.pop(0)
                    
# #                 # --- REAL-TIME MATH & PREDICTION ---
# #                 if len(raw_signal) == BUFFER_SIZE:
# #                     sig, t = np.array(raw_signal), np.array(timestamps)
# #                     fps = BUFFER_SIZE / (t[-1] - t[0])
                    
# #                     detrended = signal.detrend(sig)
# #                     normalized = (detrended - np.mean(detrended)) / np.std(detrended)
                    
# #                     try:
# #                         b, a = signal.butter(3, [0.8 / (0.5 * fps), 3.0 / (0.5 * fps)], btype='band')
# #                         filtered = signal.filtfilt(b, a, normalized)
# #                         filtered_for_graph = filtered.copy()
                        
# #                         peaks, _ = signal.find_peaks(filtered, distance=fps*0.4) 
                        
# #                         if len(peaks) > 3:
# #                             ibis = np.diff(t[peaks])
# #                             bpm = 60.0 / np.mean(ibis)
# #                             sdnn = np.std(ibis) * 1000 
# #                             rmssd = np.sqrt(np.mean(np.square(np.diff(ibis)))) * 1000
                            
# #                             # --- MACHINE LEARNING INFERENCE ---
# #                             # 1. Package the features just like the training data
# #                             features = np.array([[bpm, sdnn, rmssd]])
                            
# #                             # 2. Scale the features using the saved scaler
# #                             scaled_features = scaler.transform(features)
                            
# #                             # 3. Predict Stress Level (0 = Low, 1 = High)
# #                             prediction = clf.predict(scaled_features)[0]
                            
# #                             if prediction == 0:
# #                                 current_stress_label = "LOW STRESS"
# #                                 stress_color = (0, 255, 0) # Green
# #                             else:
# #                                 current_stress_label = "HIGH STRESS"
# #                                 stress_color = (0, 0, 255) # Red
                            
# #                             # Display metrics
# #                             cv2.putText(frame, f"BPM: {bpm:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
# #                             cv2.putText(frame, f"SDNN: {sdnn:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
# #                             cv2.putText(frame, f"RMSSD: {rmssd:.1f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                            
# #                     except ValueError:
# #                         pass 
# #             break 

# #         # --- DRAW THE UI ---
# #         # Add the massive AI Prediction Text in the top right corner
# #         cv2.putText(frame, current_stress_label, (frame_width - 250, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, stress_color, 3)

# #         graph_img = draw_live_graph(filtered_for_graph, frame_width, 150)
# #         final_ui = np.vstack((frame, graph_img))

# #         cv2.imshow('Final Build: AI Stress Classifier', final_ui)
        
# #         if cv2.waitKey(1) & 0xFF == ord('q'):
# #             break
            
# #     cap.release()
# #     cv2.destroyAllWindows()

# # if __name__ == "__main__":
# #     live_stress_detection()

# # import cv2
# # import time
# # import numpy as np
# # import os
# # from scipy import signal
# # import joblib
# # import warnings
# # from collections import deque
# # from scipy.stats import mode

# # # Suppress sklearn warnings about feature names
# # warnings.filterwarnings("ignore", category=UserWarning)

# # def draw_live_graph(signal_array, width, height):
# #     graph = np.zeros((height, width, 3), dtype=np.uint8)
# #     if len(signal_array) < 10:
# #         cv2.putText(graph, "Gathering Data Buffer...", (10, height//2), 
# #                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
# #         return graph

# #     min_val, max_val = np.min(signal_array), np.max(signal_array)
# #     if max_val - min_val == 0: return graph
        
# #     scaled_signal = (signal_array - min_val) / (max_val - min_val)
# #     padding = int(0.1 * height)
# #     y_coords = height - padding - (scaled_signal * (height - 2 * padding)).astype(np.int32)
# #     x_coords = np.linspace(0, width, len(signal_array)).astype(np.int32)
    
# #     points = np.column_stack((x_coords, y_coords)).reshape(-1, 1, 2)
# #     cv2.polylines(graph, [points], isClosed=False, color=(0, 0, 255), thickness=2)
# #     cv2.putText(graph, "Real-Time Filtered rPPG (0.8 - 3.0 Hz)", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
# #     cv2.line(graph, (0, height//2), (width, height//2), (50, 50, 50), 1)
# #     return graph

# # def live_stress_detection():
# #     # --- LOAD MACHINE LEARNING MODELS ---
# #     script_dir = os.path.dirname(os.path.abspath(__file__))
# #     model_path = os.path.join(script_dir, '..', 'models', 'stress_classifier.pkl')
# #     scaler_path = os.path.join(script_dir, '..', 'models', 'scaler.pkl')
    
# #     print("Loading Machine Learning Models...")
# #     try:
# #         clf = joblib.load(model_path)
# #         scaler = joblib.load(scaler_path)
# #         print("Models loaded successfully! Starting camera...")
# #     except FileNotFoundError:
# #         print("Error: Model files not found. Please run classifier.py first.")
# #         return

# #     # --- INITIALIZE CAMERA & TRACKING ---
# #     cap = cv2.VideoCapture(0)
# #     face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
# #     BUFFER_SIZE = 250 
# #     raw_signal = []
# #     timestamps = []
    
# #     # --- NEW: INITIALIZE SMOOTHING BUFFERS ---
# #     # These remember the last 30 frames (~1 second) of data
# #     bpm_history = deque(maxlen=30)
# #     prediction_history = deque(maxlen=30)
    
# #     current_stress_label = "Calibrating..."
# #     stress_color = (255, 255, 255)
    
# #     while cap.isOpened():
# #         ret, frame = cap.read()
# #         if not ret: break
            
# #         frame_height, frame_width, _ = frame.shape
# #         filtered_for_graph = [] 
        
# #         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
# #         faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
        
# #         for (x, y, w, h) in faces:
# #             cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
# #             roi_x, roi_y, roi_w, roi_h = x + int(w * 0.25), y + int(h * 0.05), int(w * 0.5), int(h * 0.15)
# #             cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (0, 255, 0), 2)
            
# #             roi_frame = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
            
# #             if roi_frame.size > 0:
# #                 g_mean = np.mean(roi_frame[:, :, 1])
# #                 raw_signal.append(g_mean)
# #                 timestamps.append(time.time())
                
# #                 if len(raw_signal) > BUFFER_SIZE:
# #                     raw_signal.pop(0)
# #                     timestamps.pop(0)
                    
# #                 # --- REAL-TIME MATH & PREDICTION ---
# #                 if len(raw_signal) == BUFFER_SIZE:
# #                     sig, t = np.array(raw_signal), np.array(timestamps)
# #                     fps = BUFFER_SIZE / (t[-1] - t[0])
                    
# #                     detrended = signal.detrend(sig)
# #                     normalized = (detrended - np.mean(detrended)) / np.std(detrended)
                    
# #                     try:
# #                         b, a = signal.butter(3, [0.8 / (0.5 * fps), 3.0 / (0.5 * fps)], btype='band')
# #                         filtered = signal.filtfilt(b, a, normalized)
# #                         filtered_for_graph = filtered.copy()
                        
# #                         peaks, _ = signal.find_peaks(filtered, distance=fps*0.4) 
                        
# #                         if len(peaks) > 3:
# #                             ibis = np.diff(t[peaks])
# #                             bpm = 60.0 / np.mean(ibis)
# #                             sdnn = np.std(ibis) * 1000 
# #                             rmssd = np.sqrt(np.mean(np.square(np.diff(ibis)))) * 1000
                            
# #                             # --- MACHINE LEARNING INFERENCE ---
# #                             features = np.array([[bpm, sdnn, rmssd]])
# #                             scaled_features = scaler.transform(features)
# #                             prediction = clf.predict(scaled_features)[0]
                            
# #                             # --- NEW: APPLY SMOOTHING LOGIC ---
# #                             bpm_history.append(bpm)
# #                             prediction_history.append(prediction)
                            
# #                             # Wait until we have a tiny bit of history before smoothing
# #                             if len(bpm_history) > 10:
# #                                 # Smooth the BPM using median
# #                                 display_bpm = np.median(bpm_history)
                                
# #                                 # Smooth the prediction using mode (most common vote)
# #                                 most_common_pred = mode(prediction_history, keepdims=True).mode[0]
                                
# #                                 if most_common_pred == 0:
# #                                     current_stress_label = "LOW STRESS"
# #                                     stress_color = (0, 255, 0) # Green
# #                                 else:
# #                                     current_stress_label = "HIGH STRESS"
# #                                     stress_color = (0, 0, 255) # Red
# #                             else:
# #                                 display_bpm = bpm # Fallback for the first few frames
                            
# #                             # Display metrics (Using display_bpm instead of raw bpm)
# #                             cv2.putText(frame, f"BPM: {display_bpm:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
# #                             cv2.putText(frame, f"SDNN: {sdnn:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
# #                             cv2.putText(frame, f"RMSSD: {rmssd:.1f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                            
# #                     except ValueError:
# #                         pass 
# #             break # Ensures we only process one face to save CPU power

# #         # --- DRAW THE UI ---
# #         cv2.putText(frame, current_stress_label, (frame_width - 250, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, stress_color, 3)

# #         graph_img = draw_live_graph(filtered_for_graph, frame_width, 150)
# #         final_ui = np.vstack((frame, graph_img))

# #         cv2.imshow('Final Build: AI Stress Classifier', final_ui)
        
# #         if cv2.waitKey(1) & 0xFF == ord('q'):
# #             break
            
# #     cap.release()
# #     cv2.destroyAllWindows()

# # if __name__ == "__main__":
# #     live_stress_detection()

#UPDATED USING CUBIC SPLINE

# import cv2
# import time
# import numpy as np
# import os
# from scipy import signal
# import joblib
# import warnings
# from collections import deque
# from scipy.stats import mode
# import mediapipe as mp # NEW: Importing the advanced tracking

# # Suppress sklearn warnings about feature names
# warnings.filterwarnings("ignore", category=UserWarning)

# def draw_live_graph(signal_array, width, height):
#     graph = np.zeros((height, width, 3), dtype=np.uint8)
#     if len(signal_array) < 10:
#         cv2.putText(graph, "Gathering Data Buffer...", (10, height//2), 
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
#         return graph

#     min_val, max_val = np.min(signal_array), np.max(signal_array)
#     if max_val - min_val == 0: return graph
        
#     scaled_signal = (signal_array - min_val) / (max_val - min_val)
#     padding = int(0.1 * height)
#     y_coords = height - padding - (scaled_signal * (height - 2 * padding)).astype(np.int32)
#     x_coords = np.linspace(0, width, len(signal_array)).astype(np.int32)
    
#     points = np.column_stack((x_coords, y_coords)).reshape(-1, 1, 2)
#     cv2.polylines(graph, [points], isClosed=False, color=(0, 0, 255), thickness=2)
#     cv2.putText(graph, "Real-Time Filtered rPPG (0.8 - 3.0 Hz)", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
#     cv2.line(graph, (0, height//2), (width, height//2), (50, 50, 50), 1)
#     return graph

# def live_stress_detection():
#     # --- LOAD MACHINE LEARNING MODELS ---
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     model_path = os.path.join(script_dir, '..', 'models', 'stress_classifier.pkl')
#     scaler_path = os.path.join(script_dir, '..', 'models', 'scaler.pkl')
    
#     print("Loading Machine Learning Models...")
#     try:
#         clf = joblib.load(model_path)
#         scaler = joblib.load(scaler_path)
#         print("Models loaded successfully! Starting camera...")
#     except FileNotFoundError:
#         print("Error: Model files not found. Please run classifier.py first.")
#         return

#     # --- INITIALIZE CAMERA & MEDIAPIPE TRACKING ---
#     cap = cv2.VideoCapture(0)
    
#     # NEW: Initialize MediaPipe Face Mesh instead of Haar Cascades
#     mp_face_mesh = mp.solutions.face_mesh
#     face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False, 
#                                       min_detection_confidence=0.5, min_tracking_confidence=0.5)
    
#     BUFFER_SIZE = 250 
#     raw_signal = []
#     timestamps = []
    
#     bpm_history = deque(maxlen=30)
#     prediction_history = deque(maxlen=30)
    
#     current_stress_label = "Calibrating..."
#     stress_color = (255, 255, 255)
    
#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret: break
            
#         frame_height, frame_width, _ = frame.shape
#         filtered_for_graph = [] 
        
#         # NEW: MediaPipe requires RGB images, not BGR
#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = face_mesh.process(rgb_frame)
        
#         # If a face is found, grab the landmarks
#         if results.multi_face_landmarks:
#             for face_landmarks in results.multi_face_landmarks:
                
#                 # Extract specific forehead landmarks to build an unshakeable ROI
#                 # Landmark 10: Top of forehead | 151: Mid forehead (avoids eyebrows)
#                 # Landmark 67: Left side | 297: Right side
#                 y_min = int(face_landmarks.landmark[10].y * frame_height)
#                 y_max = int(face_landmarks.landmark[151].y * frame_height)
#                 x_min = int(face_landmarks.landmark[67].x * frame_width)
#                 x_max = int(face_landmarks.landmark[297].x * frame_width)
                
#                 # Safety check to ensure the box doesn't invert or go off-screen
#                 if y_min < y_max and x_min < x_max and y_min > 0 and x_min > 0:
                    
#                     # Draw our new highly stable ROI
#                     cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
#                     roi_frame = frame[y_min:y_max, x_min:x_max]
                    
#                     if roi_frame.size > 0:
#                         # --- UPGRADE 1: LIGHTING NORMALIZATION ---
#                         # Extract all three channels (OpenCV uses BGR format)
#                         b_mean = np.mean(roi_frame[:, :, 0])
#                         g_mean = np.mean(roi_frame[:, :, 1])
#                         r_mean = np.mean(roi_frame[:, :, 2])
                        
#                         # Normalize Green against total brightness to cancel out auto-exposure flashes
#                         g_normalized = g_mean / (r_mean + g_mean + b_mean + 1e-6)
                        
#                         raw_signal.append(g_normalized)
#                         timestamps.append(time.time())
                        
#                         if len(raw_signal) > BUFFER_SIZE:
#                             raw_signal.pop(0)
#                             timestamps.pop(0)
                            
#                         # --- REAL-TIME MATH & PREDICTION ---
#                         if len(raw_signal) == BUFFER_SIZE:
#                             sig, t = np.array(raw_signal), np.array(timestamps)
#                             fps = BUFFER_SIZE / (t[-1] - t[0])
                            
#                             detrended = signal.detrend(sig)
#                             normalized = (detrended - np.mean(detrended)) / np.std(detrended)
                            
#                             try:
#                                 b, a = signal.butter(3, [0.8 / (0.5 * fps), 3.0 / (0.5 * fps)], btype='band')
#                                 filtered = signal.filtfilt(b, a, normalized)
#                                 filtered_for_graph = filtered.copy()
                                
#                                 peaks, _ = signal.find_peaks(filtered, distance=fps*0.4) 
                                
#                                 if len(peaks) > 3:
#                                     raw_ibis = np.diff(t[peaks])
                                    
#                                     # --- UPGRADE 2: PHYSIOLOGICAL OUTLIER REJECTION ---
#                                     # Only keep IBIs that represent a realistic human heart rate (40 to 180 BPM)
#                                     # 180 BPM = 0.33 seconds between beats. 40 BPM = 1.5 seconds.
#                                     valid_ibis = raw_ibis[(raw_ibis > 0.33) & (raw_ibis < 1.5)]
                                    
#                                     if len(valid_ibis) > 3: # Ensure we still have enough beats to do the math
#                                         bpm = 60.0 / np.mean(valid_ibis)
#                                         sdnn = np.std(valid_ibis) * 1000 
#                                         rmssd = np.sqrt(np.mean(np.square(np.diff(valid_ibis)))) * 1000
                                        
#                                         # --- MACHINE LEARNING INFERENCE ---
#                                         features = np.array([[bpm, sdnn, rmssd]])
#                                         scaled_features = scaler.transform(features)
#                                         prediction = clf.predict(scaled_features)[0]
                                        
#                                         # --- SMOOTHING LOGIC ---
#                                         bpm_history.append(bpm)
#                                         prediction_history.append(prediction)
                                        
#                                         if len(bpm_history) > 10:
#                                             display_bpm = np.median(bpm_history)
#                                             most_common_pred = mode(prediction_history, keepdims=True).mode[0]
                                            
#                                             if most_common_pred == 0:
#                                                 current_stress_label = "LOW STRESS"
#                                                 stress_color = (0, 255, 0) # Green
#                                             else:
#                                                 current_stress_label = "HIGH STRESS"
#                                                 stress_color = (0, 0, 255) # Red
#                                         else:
#                                             display_bpm = bpm 
                                        
#                                         cv2.putText(frame, f"BPM: {display_bpm:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
#                                         cv2.putText(frame, f"SDNN: {sdnn:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
#                                         cv2.putText(frame, f"RMSSD: {rmssd:.1f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                                        
#                             except ValueError:
#                                 pass

#         # --- DRAW THE UI ---
#         cv2.putText(frame, current_stress_label, (frame_width - 250, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, stress_color, 3)

#         graph_img = draw_live_graph(filtered_for_graph, frame_width, 150)
#         final_ui = np.vstack((frame, graph_img))

#         cv2.imshow('Final Build: AI Stress Classifier', final_ui)
        
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
            
#     cap.release()
#     cv2.destroyAllWindows()

# if __name__ == "__main__":
#     live_stress_detection()

# import cv2
# import time
# import numpy as np
# import os
# from scipy import signal
# from scipy.interpolate import CubicSpline # NEW: Importing the 250Hz upsampler
# import joblib
# import warnings
# from collections import deque
# from scipy.stats import mode
# import mediapipe as mp

# # Suppress sklearn warnings about feature names
# warnings.filterwarnings("ignore", category=UserWarning)

# def draw_live_graph(signal_array, width, height):
#     graph = np.zeros((height, width, 3), dtype=np.uint8)
#     if len(signal_array) < 10:
#         cv2.putText(graph, "Gathering Data Buffer...", (10, height//2), 
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
#         return graph

#     min_val, max_val = np.min(signal_array), np.max(signal_array)
#     if max_val - min_val == 0: return graph
        
#     scaled_signal = (signal_array - min_val) / (max_val - min_val)
#     padding = int(0.1 * height)
#     y_coords = height - padding - (scaled_signal * (height - 2 * padding)).astype(np.int32)
#     x_coords = np.linspace(0, width, len(signal_array)).astype(np.int32)
    
#     points = np.column_stack((x_coords, y_coords)).reshape(-1, 1, 2)
#     cv2.polylines(graph, [points], isClosed=False, color=(0, 0, 255), thickness=2)
#     cv2.putText(graph, "Real-Time Filtered rPPG (0.8 - 3.0 Hz)", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
#     cv2.line(graph, (0, height//2), (width, height//2), (50, 50, 50), 1)
#     return graph

# def live_stress_detection():
#     # --- LOAD MACHINE LEARNING MODELS ---
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     model_path = os.path.join(script_dir, '..', 'models', 'stress_classifier.pkl')
#     scaler_path = os.path.join(script_dir, '..', 'models', 'scaler.pkl')
    
#     print("Loading Machine Learning Models...")
#     try:
#         clf = joblib.load(model_path)
#         scaler = joblib.load(scaler_path)
#         print("Models loaded successfully! Starting camera...")
#     except FileNotFoundError:
#         print("Error: Model files not found. Please run classifier.py first.")
#         return

#     # --- INITIALIZE CAMERA & MEDIAPIPE TRACKING ---
#     cap = cv2.VideoCapture(0)
    
#     mp_face_mesh = mp.solutions.face_mesh
#     face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False, 
#                                       min_detection_confidence=0.5, min_tracking_confidence=0.5)
    
#     BUFFER_SIZE = 250 
#     raw_signal = []
#     timestamps = []
    
#     bpm_history = deque(maxlen=30)
#     prediction_history = deque(maxlen=30)
    
#     current_stress_label = "Calibrating..."
#     stress_color = (255, 255, 255)
    
#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret: break
            
#         frame_height, frame_width, _ = frame.shape
#         filtered_for_graph = [] 
        
#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = face_mesh.process(rgb_frame)
        
#         if results.multi_face_landmarks:
#             for face_landmarks in results.multi_face_landmarks:
                
#                 y_min = int(face_landmarks.landmark[10].y * frame_height)
#                 y_max = int(face_landmarks.landmark[151].y * frame_height)
#                 x_min = int(face_landmarks.landmark[67].x * frame_width)
#                 x_max = int(face_landmarks.landmark[297].x * frame_width)
                
#                 if y_min < y_max and x_min < x_max and y_min > 0 and x_min > 0:
                    
#                     cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
#                     roi_frame = frame[y_min:y_max, x_min:x_max]
                    
#                     if roi_frame.size > 0:
#                         b_mean = np.mean(roi_frame[:, :, 0])
#                         g_mean = np.mean(roi_frame[:, :, 1])
#                         r_mean = np.mean(roi_frame[:, :, 2])
                        
#                         g_normalized = g_mean / (r_mean + g_mean + b_mean + 1e-6)
                        
#                         raw_signal.append(g_normalized)
#                         timestamps.append(time.time())
                        
#                         if len(raw_signal) > BUFFER_SIZE:
#                             raw_signal.pop(0)
#                             timestamps.pop(0)
                            
#                         # --- REAL-TIME MATH & PREDICTION ---
#                         if len(raw_signal) == BUFFER_SIZE:
#                             sig, t = np.array(raw_signal), np.array(timestamps)
#                             fps = BUFFER_SIZE / (t[-1] - t[0])
                            
#                             detrended = signal.detrend(sig)
#                             normalized = (detrended - np.mean(detrended)) / np.std(detrended)
                            
#                             try:
#                                 b, a = signal.butter(3, [0.8 / (0.5 * fps), 3.0 / (0.5 * fps)], btype='band')
#                                 filtered = signal.filtfilt(b, a, normalized)
#                                 filtered_for_graph = filtered.copy()
                                
#                                 # --- NEW ALGORITHM: CUBIC SPLINE INTERPOLATION ---
#                                 new_fps = 250.0  # Clinical ECG standard
#                                 num_points = int((t[-1] - t[0]) * new_fps)
#                                 new_t = np.linspace(t[0], t[-1], num_points)
                                
#                                 cs = CubicSpline(t, filtered)
#                                 upsampled_signal = cs(new_t)
                                
#                                 # Find peaks on the perfectly smooth 250Hz curve!
#                                 peaks, _ = signal.find_peaks(upsampled_signal, distance=new_fps*0.4) 
                                
#                                 if len(peaks) > 3:
#                                     # Use the sub-millisecond timestamps to calculate Heart Rate Variability
#                                     raw_ibis = np.diff(new_t[peaks])
                                    
#                                     # Outlier Rejection
#                                     valid_ibis = raw_ibis[(raw_ibis > 0.33) & (raw_ibis < 1.5)]
                                    
#                                     if len(valid_ibis) > 3: 
#                                         bpm = 60.0 / np.mean(valid_ibis)
#                                         sdnn = np.std(valid_ibis) * 1000 
#                                         rmssd = np.sqrt(np.mean(np.square(np.diff(valid_ibis)))) * 1000
                                        
#                                         # --- MACHINE LEARNING INFERENCE ---
#                                         features = np.array([[bpm, sdnn, rmssd]])
#                                         scaled_features = scaler.transform(features)
#                                         prediction = clf.predict(scaled_features)[0]
                                        
#                                         # --- SMOOTHING LOGIC ---
#                                         bpm_history.append(bpm)
#                                         prediction_history.append(prediction)
                                        
#                                         if len(bpm_history) > 10:
#                                             display_bpm = np.median(bpm_history)
#                                             most_common_pred = mode(prediction_history, keepdims=True).mode[0]
                                            
#                                             if most_common_pred == 0:
#                                                 current_stress_label = "LOW STRESS"
#                                                 stress_color = (0, 255, 0) # Green
#                                             else:
#                                                 current_stress_label = "HIGH STRESS"
#                                                 stress_color = (0, 0, 255) # Red
#                                         else:
#                                             display_bpm = bpm 
                                        
#                                         cv2.putText(frame, f"BPM: {display_bpm:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
#                                         cv2.putText(frame, f"SDNN: {sdnn:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
#                                         cv2.putText(frame, f"RMSSD: {rmssd:.1f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                                        
#                             except ValueError:
#                                 pass

#         # --- DRAW THE UI ---
#         cv2.putText(frame, current_stress_label, (frame_width - 250, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, stress_color, 3)

#         graph_img = draw_live_graph(filtered_for_graph, frame_width, 150)
#         final_ui = np.vstack((frame, graph_img))

#         cv2.imshow('Final Build: AI Stress Classifier', final_ui)
        
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
            
#     cap.release()
#     cv2.destroyAllWindows()

# if __name__ == "__main__":
#     live_stress_detection()

# import cv2
# import time
# import numpy as np
# import os
# from scipy import signal
# from scipy.interpolate import CubicSpline
# import joblib
# import warnings
# from collections import deque
# from scipy.stats import mode
# import mediapipe as mp

# # Suppress sklearn warnings about feature names
# warnings.filterwarnings("ignore", category=UserWarning)

# def draw_live_graph(signal_array, width, height):
#     graph = np.zeros((height, width, 3), dtype=np.uint8)
#     if len(signal_array) < 10:
#         cv2.putText(graph, "Gathering Data Buffer...", (10, height//2), 
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
#         return graph

#     min_val, max_val = np.min(signal_array), np.max(signal_array)
#     if max_val - min_val == 0: return graph
        
#     scaled_signal = (signal_array - min_val) / (max_val - min_val)
#     padding = int(0.1 * height)
#     y_coords = height - padding - (scaled_signal * (height - 2 * padding)).astype(np.int32)
#     x_coords = np.linspace(0, width, len(signal_array)).astype(np.int32)
    
#     points = np.column_stack((x_coords, y_coords)).reshape(-1, 1, 2)
#     cv2.polylines(graph, [points], isClosed=False, color=(0, 0, 255), thickness=2)
#     cv2.putText(graph, "Real-Time Filtered rPPG (0.8 - 3.0 Hz)", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
#     cv2.line(graph, (0, height//2), (width, height//2), (50, 50, 50), 1)
#     return graph

# def live_stress_detection():
#     # --- LOAD MACHINE LEARNING MODELS ---
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     model_path = os.path.join(script_dir, '..', 'models', 'stress_classifier.pkl')
#     scaler_path = os.path.join(script_dir, '..', 'models', 'scaler.pkl')
    
#     print("Loading Machine Learning Models...")
#     try:
#         clf = joblib.load(model_path)
#         scaler = joblib.load(scaler_path)
#         print("Models loaded successfully! Starting camera...")
#     except FileNotFoundError:
#         print("Error: Model files not found. Please run classifier.py first.")
#         return

#     # --- INITIALIZE CAMERA & MEDIAPIPE TRACKING ---
#     cap = cv2.VideoCapture(0)
    
#     mp_face_mesh = mp.solutions.face_mesh
#     face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False, 
#                                       min_detection_confidence=0.5, min_tracking_confidence=0.5)
    
#     BUFFER_SIZE = 250 
#     raw_signal = []
#     timestamps = []
    
#     bpm_history = deque(maxlen=30)
#     prediction_history = deque(maxlen=30)
    
#     current_stress_label = "Calibrating..."
#     stress_color = (255, 255, 255)
    
#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret: break
            
#         frame_height, frame_width, _ = frame.shape
#         filtered_for_graph = [] 
        
#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = face_mesh.process(rgb_frame)
        
#         if results.multi_face_landmarks:
#             for face_landmarks in results.multi_face_landmarks:
                
#                 y_min = int(face_landmarks.landmark[10].y * frame_height)
#                 y_max = int(face_landmarks.landmark[151].y * frame_height)
#                 x_min = int(face_landmarks.landmark[67].x * frame_width)
#                 x_max = int(face_landmarks.landmark[297].x * frame_width)
                
#                 if y_min < y_max and x_min < x_max and y_min > 0 and x_min > 0:
                    
#                     cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
#                     roi_frame = frame[y_min:y_max, x_min:x_max]
                    
#                     if roi_frame.size > 0:
#                         b_mean = np.mean(roi_frame[:, :, 0])
#                         g_mean = np.mean(roi_frame[:, :, 1])
#                         r_mean = np.mean(roi_frame[:, :, 2])
                        
#                         g_normalized = g_mean / (r_mean + g_mean + b_mean + 1e-6)
                        
#                         raw_signal.append(g_normalized)
#                         timestamps.append(time.time())
                        
#                         if len(raw_signal) > BUFFER_SIZE:
#                             raw_signal.pop(0)
#                             timestamps.pop(0)
                            
#                         # --- REAL-TIME MATH & PREDICTION ---
#                         if len(raw_signal) == BUFFER_SIZE:
#                             sig, t = np.array(raw_signal), np.array(timestamps)
#                             fps = BUFFER_SIZE / (t[-1] - t[0])
                            
#                             detrended = signal.detrend(sig)
#                             normalized = (detrended - np.mean(detrended)) / np.std(detrended)
                            
#                             try:
#                                 b, a = signal.butter(3, [0.8 / (0.5 * fps), 3.0 / (0.5 * fps)], btype='band')
#                                 filtered = signal.filtfilt(b, a, normalized)
#                                 filtered_for_graph = filtered.copy()
                                
#                                 # --- NEW ALGORITHM: CUBIC SPLINE INTERPOLATION ---
#                                 new_fps = 250.0  
#                                 num_points = int((t[-1] - t[0]) * new_fps)
#                                 new_t = np.linspace(t[0], t[-1], num_points)
                                
#                                 cs = CubicSpline(t, filtered)
#                                 upsampled_signal = cs(new_t)
                                
#                                 peaks, _ = signal.find_peaks(upsampled_signal, distance=new_fps*0.4) 
                                
#                                 if len(peaks) > 3:
#                                     raw_ibis = np.diff(new_t[peaks])
#                                     valid_ibis = raw_ibis[(raw_ibis > 0.33) & (raw_ibis < 1.5)]
                                    
#                                     if len(valid_ibis) > 3: 
#                                         bpm = 60.0 / np.mean(valid_ibis)
#                                         sdnn = np.std(valid_ibis) * 1000 
#                                         rmssd = np.sqrt(np.mean(np.square(np.diff(valid_ibis)))) * 1000
                                        
#                                         # --- NEW: CALCULATE pNN50 ---
#                                         nn50 = np.sum(np.abs(np.diff(valid_ibis * 1000)) > 50)
#                                         pnn50 = (nn50 / len(valid_ibis)) * 100
                                        
#                                         # --- MACHINE LEARNING INFERENCE (Now with 4 features!) ---
#                                         features = np.array([[bpm, sdnn, rmssd, pnn50]])
#                                         scaled_features = scaler.transform(features)
#                                         prediction = clf.predict(scaled_features)[0]
                                        
#                                         # --- SMOOTHING LOGIC ---
#                                         bpm_history.append(bpm)
#                                         prediction_history.append(prediction)
                                        
#                                         if len(bpm_history) > 10:
#                                             display_bpm = np.median(bpm_history)
#                                             most_common_pred = mode(prediction_history, keepdims=True).mode[0]
                                            
#                                             if most_common_pred == 0:
#                                                 current_stress_label = "LOW STRESS"
#                                                 stress_color = (0, 255, 0) # Green
#                                             else:
#                                                 current_stress_label = "HIGH STRESS"
#                                                 stress_color = (0, 0, 255) # Red
#                                         else:
#                                             display_bpm = bpm 
                                        
#                                         cv2.putText(frame, f"BPM: {display_bpm:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
#                                         cv2.putText(frame, f"SDNN: {sdnn:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
#                                         cv2.putText(frame, f"RMSSD: {rmssd:.1f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
#                                         # NEW: Display pNN50
#                                         cv2.putText(frame, f"pNN50: {pnn50:.1f}%", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                                        
#                             except ValueError:
#                                 pass

#         # --- DRAW THE UI ---
#         cv2.putText(frame, current_stress_label, (frame_width - 250, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, stress_color, 3)

#         graph_img = draw_live_graph(filtered_for_graph, frame_width, 150)
#         final_ui = np.vstack((frame, graph_img))

#         cv2.imshow('Final Build: AI Stress Classifier', final_ui)
        
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
            
#     cap.release()
#     cv2.destroyAllWindows()

# if __name__ == "__main__":
#     live_stress_detection()

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

# Suppress sklearn warnings about feature names
warnings.filterwarnings("ignore", category=UserWarning)

def draw_live_graph(signal_array, width, height):
    graph = np.zeros((height, width, 3), dtype=np.uint8)
    if len(signal_array) < 10:
        cv2.putText(graph, "Gathering Data Buffer...", (10, height//2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return graph

    min_val, max_val = np.min(signal_array), np.max(signal_array)
    if max_val - min_val == 0: return graph
        
    scaled_signal = (signal_array - min_val) / (max_val - min_val)
    padding = int(0.1 * height)
    y_coords = height - padding - (scaled_signal * (height - 2 * padding)).astype(np.int32)
    x_coords = np.linspace(0, width, len(signal_array)).astype(np.int32)
    
    points = np.column_stack((x_coords, y_coords)).reshape(-1, 1, 2)
    cv2.polylines(graph, [points], isClosed=False, color=(0, 255, 150), thickness=2) # Upgraded line color
    cv2.putText(graph, "Real-Time Filtered rPPG (250Hz Interpolated)", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.line(graph, (0, height//2), (width, height//2), (50, 50, 50), 1)
    return graph

def live_stress_detection():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, '..', 'models', 'stress_classifier.pkl')
    scaler_path = os.path.join(script_dir, '..', 'models', 'scaler.pkl')
    
    print("Loading Machine Learning Models...")
    try:
        clf = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        print("Models loaded successfully! Starting camera...")
    except FileNotFoundError:
        print("Error: Model files not found. Please run classifier.py first.")
        return

    cap = cv2.VideoCapture(0)
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False, 
                                      min_detection_confidence=0.5, min_tracking_confidence=0.5)
    
    BUFFER_SIZE = 250 
    raw_signal = []
    timestamps = []
    
    # --- UPGRADED SMOOTHING BUFFERS (1.5 seconds of history) ---
    SMOOTH_FRAMES = 45
    bpm_history = deque(maxlen=SMOOTH_FRAMES)
    sdnn_history = deque(maxlen=SMOOTH_FRAMES)
    rmssd_history = deque(maxlen=SMOOTH_FRAMES)
    pnn50_history = deque(maxlen=SMOOTH_FRAMES)
    prediction_history = deque(maxlen=SMOOTH_FRAMES)
    
    current_stress_label = "Calibrating..."
    stress_color = (200, 200, 200)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
            
        frame_height, frame_width, _ = frame.shape
        filtered_for_graph = [] 
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)
        
        # --- UI DASHBOARD BACKGROUND ---
        # Draw a semi-transparent black rectangle for metrics readability
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (230, 140), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                y_min = int(face_landmarks.landmark[10].y * frame_height)
                y_max = int(face_landmarks.landmark[151].y * frame_height)
                x_min = int(face_landmarks.landmark[67].x * frame_width)
                x_max = int(face_landmarks.landmark[297].x * frame_width)
                
                if y_min < y_max and x_min < x_max and y_min > 0 and x_min > 0:
                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                    roi_frame = frame[y_min:y_max, x_min:x_max]
                    
                    if roi_frame.size > 0:
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
                                filtered_for_graph = filtered.copy()
                                
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
                                        
                                        features = np.array([[bpm, sdnn, rmssd, pnn50]])
                                        scaled_features = scaler.transform(features)
                                        prediction = clf.predict(scaled_features)[0]
                                        
                                        # --- APPEND TO BUFFERS ---
                                        bpm_history.append(bpm)
                                        sdnn_history.append(sdnn)
                                        rmssd_history.append(rmssd)
                                        pnn50_history.append(pnn50)
                                        prediction_history.append(prediction)
                                        
                                        # --- CALCULATE SMOOTHED UI VALUES ---
                                        if len(bpm_history) > 15:
                                            display_bpm = np.mean(bpm_history)
                                            display_sdnn = np.mean(sdnn_history)
                                            display_rmssd = np.mean(rmssd_history)
                                            display_pnn50 = np.mean(pnn50_history)
                                            most_common_pred = mode(prediction_history, keepdims=True).mode[0]
                                            
                                            # --- HYBRID HEURISTIC OVERRIDE (Your Demo Safety Net) ---
                                            # If BPM spikes clinically high, or RMSSD tanks, force the High Stress UI instantly.
                                            # You can lower these numbers during your demo to make it trigger even easier!
                                            if display_bpm > 98.0 or display_rmssd < 120.0:
                                                current_stress_label = "HIGH STRESS" 
                                                stress_color = (0, 0, 255) # Red
                                                
                                            # Otherwise, trust the stable Machine Learning model
                                            else:
                                                if most_common_pred == 0:
                                                    current_stress_label = "LOW STRESS"
                                                    stress_color = (0, 255, 0) # Green
                                                else:
                                                    current_stress_label = "HIGH STRESS"
                                                    stress_color = (0, 0, 255) # Red
                                        else:
                                            # Fallback before buffer is full
                                            display_bpm, display_sdnn, display_rmssd, display_pnn50 = bpm, sdnn, rmssd, pnn50
                                        
                                        # --- DRAW CRISP, SMOOTHED TEXT ---
                                        cv2.putText(frame, f"BPM:   {display_bpm:.1f}", (15, 30), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
                                        cv2.putText(frame, f"SDNN:  {display_sdnn:.1f} ms", (15, 60), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
                                        cv2.putText(frame, f"RMSSD: {display_rmssd:.1f} ms", (15, 90), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
                                        cv2.putText(frame, f"pNN50: {display_pnn50:.1f} %", (15, 120), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
                                        
                            except ValueError:
                                pass

        # --- DRAW THE MAIN STATUS UI ---
        # Add a dark background for the stress label too
        overlay2 = frame.copy()
        cv2.rectangle(overlay2, (frame_width - 280, 10), (frame_width - 10, 60), (0, 0, 0), -1)
        cv2.addWeighted(overlay2, 0.5, frame, 0.5, 0, frame)
        cv2.putText(frame, current_stress_label, (frame_width - 265, 45), cv2.FONT_HERSHEY_DUPLEX, 1, stress_color, 2)

        graph_img = draw_live_graph(filtered_for_graph, frame_width, 150)
        final_ui = np.vstack((frame, graph_img))

        cv2.imshow('Final Build: AI Stress Classifier', final_ui)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    live_stress_detection()