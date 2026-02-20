# import cv2
# import time
# import numpy as np
# from scipy import signal

# def live_hr_hrv_detection():
#     cap = cv2.VideoCapture(0)
#     face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
#     # BUFFER: We need about 10 seconds of data to get a reliable heartbeat.
#     # Since your camera runs at ~29 FPS, 250 frames is roughly 8.5 seconds.
#     BUFFER_SIZE = 250 
#     raw_signal = []
#     timestamps = []
    
#     print("Phase 5: Live HR & HRV Calculation Started.")
#     print("Please sit still. It will take about 10 seconds to gather enough data for the first reading...")
    
#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret:
#             break
            
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
        
#         for (x, y, w, h) in faces:
#             # Draw Face and ROI boxes
#             cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
#             roi_x = x + int(w * 0.25)
#             roi_y = y + int(h * 0.05) 
#             roi_w = int(w * 0.5)
#             roi_h = int(h * 0.15)
            
#             cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (0, 255, 0), 2)
            
#             roi_frame = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
            
#             if roi_frame.size > 0:
#                 # Extract Green Channel Mean
#                 g_channel = roi_frame[:, :, 1]
#                 g_mean = np.mean(g_channel)
                
#                 raw_signal.append(g_mean)
#                 timestamps.append(time.time())
                
#                 # Keep the buffer at a strict sliding window size
#                 if len(raw_signal) > BUFFER_SIZE:
#                     raw_signal.pop(0)
#                     timestamps.pop(0)
                    
#                 # --- PHASE 5: REAL-TIME MATH ---
#                 # Only calculate once the buffer is completely full
#                 if len(raw_signal) == BUFFER_SIZE:
#                     sig = np.array(raw_signal)
#                     t = np.array(timestamps)
                    
#                     # Dynamically calculate FPS to keep filters accurate
#                     fps = BUFFER_SIZE / (t[-1] - t[0])
                    
#                     # Detrend & Normalize
#                     detrended = signal.detrend(sig)
#                     normalized = (detrended - np.mean(detrended)) / np.std(detrended)
                    
#                     # Bandpass Filter (0.8 - 3.0 Hz)
#                     nyquist = 0.5 * fps
#                     low = 0.8 / nyquist
#                     high = 3.0 / nyquist
                    
#                     try:
#                         b, a = signal.butter(3, [low, high], btype='band')
#                         filtered = signal.filtfilt(b, a, normalized)
                        
#                         # Find Peaks in the waveform
#                         # 'distance' prevents counting a single beat twice (fps * 0.4 allows up to 150 BPM)
#                         peaks, _ = signal.find_peaks(filtered, distance=fps*0.4) 
                        
#                         if len(peaks) > 3:
#                             # Calculate Inter-Beat Intervals (IBIs) in seconds
#                             peak_times = t[peaks]
#                             ibis = np.diff(peak_times)
                            
#                             # Derive Physiological Features
#                             bpm = 60.0 / np.mean(ibis)
#                             sdnn = np.std(ibis) * 1000  # Converted to milliseconds
#                             rmssd = np.sqrt(np.mean(np.square(np.diff(ibis)))) * 1000
                            
#                             # Display metrics on the live video feed
#                             cv2.putText(frame, f"BPM: {bpm:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
#                             cv2.putText(frame, f"SDNN: {sdnn:.1f} ms", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
#                             cv2.putText(frame, f"RMSSD: {rmssd:.1f} ms", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                            
#                     except ValueError:
#                         # Silently pass if the math momentarily breaks due to movement noise
#                         pass 
                        
#             break # Process only the first detected face

#         cv2.imshow('Phase 5: Live HR & HRV Dashboard', frame)
        
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
            
#     cap.release()
#     cv2.destroyAllWindows()

# if __name__ == "__main__":
#     live_hr_hrv_detection()

import cv2
import time
import numpy as np
from scipy import signal

def draw_live_graph(signal_array, width, height):
    """Creates a black canvas and draws the live signal wave."""
    # Create a black background image
    graph = np.zeros((height, width, 3), dtype=np.uint8)
    
    if len(signal_array) < 10:
        cv2.putText(graph, "Gathering Data Buffer...", (10, height//2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return graph

    # Dynamically scale the signal to fit the height of our graph canvas
    min_val, max_val = np.min(signal_array), np.max(signal_array)
    if max_val - min_val == 0:
        return graph
        
    scaled_signal = (signal_array - min_val) / (max_val - min_val)
    
    # Invert the Y-axis so peaks point upward, and map to pixel coordinates
    padding = int(0.1 * height)
    y_coords = height - padding - (scaled_signal * (height - 2 * padding)).astype(np.int32)
    x_coords = np.linspace(0, width, len(signal_array)).astype(np.int32)
    
    # Stack X and Y coordinates and draw the connected lines
    points = np.column_stack((x_coords, y_coords)).reshape(-1, 1, 2)
    cv2.polylines(graph, [points], isClosed=False, color=(0, 0, 255), thickness=2) # Red line
    
    # Add a title and gridline flavor to make it look professional
    cv2.putText(graph, "Real-Time Filtered rPPG (0.8 - 3.0 Hz)", (10, 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.line(graph, (0, height//2), (width, height//2), (50, 50, 50), 1)
    
    return graph

def live_hr_hrv_detection():
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    BUFFER_SIZE = 250 
    raw_signal = []
    timestamps = []
    
    print("Phase 5: Live HR & HRV Dashboard Started.")
    print("Please sit still. Gathering 10 seconds of initial data...")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Get frame dimensions for our graph
        frame_height, frame_width, _ = frame.shape
        filtered_for_graph = [] # Empty placeholder until buffer is full
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
            roi_x = x + int(w * 0.25)
            roi_y = y + int(h * 0.05) 
            roi_w = int(w * 0.5)
            roi_h = int(h * 0.15)
            
            cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (0, 255, 0), 2)
            
            roi_frame = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
            
            if roi_frame.size > 0:
                g_channel = roi_frame[:, :, 1]
                g_mean = np.mean(g_channel)
                
                raw_signal.append(g_mean)
                timestamps.append(time.time())
                
                if len(raw_signal) > BUFFER_SIZE:
                    raw_signal.pop(0)
                    timestamps.pop(0)
                    
                # --- REAL-TIME MATH ---
                if len(raw_signal) == BUFFER_SIZE:
                    sig = np.array(raw_signal)
                    t = np.array(timestamps)
                    
                    fps = BUFFER_SIZE / (t[-1] - t[0])
                    
                    detrended = signal.detrend(sig)
                    normalized = (detrended - np.mean(detrended)) / np.std(detrended)
                    
                    nyquist = 0.5 * fps
                    low = 0.8 / nyquist
                    high = 3.0 / nyquist
                    
                    try:
                        b, a = signal.butter(3, [low, high], btype='band')
                        filtered = signal.filtfilt(b, a, normalized)
                        
                        # Save the filtered wave so we can graph it below
                        filtered_for_graph = filtered.copy()
                        
                        peaks, _ = signal.find_peaks(filtered, distance=fps*0.4) 
                        
                        if len(peaks) > 3:
                            peak_times = t[peaks]
                            ibis = np.diff(peak_times)
                            
                            bpm = 60.0 / np.mean(ibis)
                            sdnn = np.std(ibis) * 1000 
                            rmssd = np.sqrt(np.mean(np.square(np.diff(ibis)))) * 1000
                            
                            # Display metrics
                            cv2.putText(frame, f"BPM: {bpm:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                            cv2.putText(frame, f"SDNN: {sdnn:.1f} ms", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                            cv2.putText(frame, f"RMSSD: {rmssd:.1f} ms", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                            
                    except ValueError:
                        pass 
            break 

        # --- DRAW THE UI ---
        # Generate the graph image (150 pixels tall, same width as the webcam feed)
        graph_img = draw_live_graph(filtered_for_graph, frame_width, 150)
        
        # Stitch the webcam feed and the graph together vertically
        final_ui = np.vstack((frame, graph_img))

        cv2.imshow('Phase 5: Real-Time UI', final_ui)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    live_hr_hrv_detection()