import cv2
import numpy as np
import mediapipe as mp
import time
import os

# NOTE: Import your existing mathematical and ML functions here!
# from src.signal_processing import filter_signal, calculate_hrv
# from src.classifier import predict_stress

def process_video_file(input_video_path, output_video_path):
    print(f"Loading video: {input_video_path}")
    
    # 1. Initialize Video Capture & Video Writer
    cap = cv2.VideoCapture(input_video_path)
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Define the codec and create VideoWriter object (mp4 format)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # 2. Initialize MediaPipe FaceMesh
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    # 3. Initialize Variables & Buffers
    # 3. Initialize Variables & Buffers
    prev_box = None
    SMOOTHING = 0.15 # Your EMA shock absorber
    
    raw_signal_buffer = []
    window_size = fps * 10 # 10-second rolling window to calculate HRV
    
    # State variables to hold the latest UI metrics (THIS IS THE FIX)
    current_stress = "CALIBRATING BUFFER..."
    current_bpm = "BPM: --"
    current_sdnn = "SDNN: --"
    current_rmssd = "RMSSD: --"
    current_pnn50 = "pNN50: --"
    box_color = (0, 165, 255) # Orange for calibrating
    
    frame_count = 0

    print("Processing frames...")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)
        
        # 4. Face Tracking & ROI Extraction
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                raw_y_min = int(face_landmarks.landmark[10].y * height)
                raw_y_max = int(face_landmarks.landmark[151].y * height)
                raw_x_min = int(face_landmarks.landmark[67].x * width)
                raw_x_max = int(face_landmarks.landmark[297].x * width)
                
                if raw_y_min < raw_y_max and raw_x_min < raw_x_max and raw_y_min > 0 and raw_x_min > 0:
                    
                    # Apply EMA Smoothing
                    if prev_box is None:
                        y_min, y_max, x_min, x_max = raw_y_min, raw_y_max, raw_x_min, raw_x_max
                    else:
                        y_min = int(SMOOTHING * raw_y_min + (1 - SMOOTHING) * prev_box[0])
                        y_max = int(SMOOTHING * raw_y_max + (1 - SMOOTHING) * prev_box[1])
                        x_min = int(SMOOTHING * raw_x_min + (1 - SMOOTHING) * prev_box[2])
                        x_max = int(SMOOTHING * raw_x_max + (1 - SMOOTHING) * prev_box[3])
                        
                    prev_box = (y_min, y_max, x_min, x_max)
                    
                    # Draw the bounding box on the frame
                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), box_color, 2)
                    
                    # Extract rPPG (Green Channel Mean)
                    roi_frame = frame[y_min:y_max, x_min:x_max]
                    g_mean = np.mean(roi_frame[:, :, 1]) # Index 1 is Green in BGR
                    raw_signal_buffer.append(g_mean)
                    
        # 5. Sliding Window Math (Triggered every frame once buffer is full)
        # 5. Sliding Window Math (Triggered every frame once buffer is full)
        if len(raw_signal_buffer) >= window_size:
            # Pop the oldest frame so we slide forward
            if len(raw_signal_buffer) > window_size:
                raw_signal_buffer.pop(0)
                
            # ---> INSERT YOUR PIPELINE HERE <---
            # 1. filtered_wave = filter_signal(raw_signal_buffer)
            # 2. bpm, sdnn, rmssd, pnn50 = calculate_hrv(filtered_wave)
            # 3. is_stressed = predict_stress([bpm, sdnn, rmssd, pnn50])
            
            # --- SIMULATED RESULTS (Remove this when you plug in your real functions) ---
            bpm, sdnn, rmssd, pnn50 = 82.5, 140.2, 45.6, 12.3
            is_stressed = False  # Set to False to test the Green "LOW STRESS" output!
            # ------------------------------------------------------------------------
            
            # Update UI text strings
            current_bpm = f"BPM: {bpm:.1f}"
            current_sdnn = f"SDNN: {sdnn:.1f} ms"
            current_rmssd = f"RMSSD: {rmssd:.1f} ms"
            current_pnn50 = f"pNN50: {pnn50:.1f} %"
            
            # Clinical Color Coding (Note: OpenCV uses BGR format, not RGB)
            if is_stressed:
                current_stress = "HIGH STRESS"
                box_color = (0, 0, 255) # Solid Red
            else:
                current_stress = "LOW STRESS"
                box_color = (0, 255, 0) # Solid Green
                
        # 6. Draw Dashboard Text onto the Frame
        # cv2.putText(image, text, (X, Y), font, scale, color, thickness, anti-aliasing)
        
        # Draw the main Stress Verdict
        cv2.putText(frame, current_stress, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, box_color, 3, cv2.LINE_AA)
        
        # Draw the 4 HRV Biomarkers stacked vertically below it
        cv2.putText(frame, current_bpm, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, current_sdnn, (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, current_rmssd, (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, current_pnn50, (20, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        
        # 7. Write the processed frame to the output video
        out.write(frame)
        
        # Print progress
        if frame_count % 30 == 0:
            print(f"Processed {frame_count}/{total_frames} frames...")

    # Clean up
    cap.release()
    out.release()
    face_mesh.close()
    print(f"Success! Saved processed video to: {output_video_path}")

if __name__ == "__main__":
    print("="*50)
    print(" NeuroStress Offline Video Processor ")
    print("="*50)
    
    # Ask the user for the input video path
    input_video = input("Enter the path to the input video (e.g., test.mp4): ").strip()
    
    # Check if the file actually exists to prevent crashes
    if not os.path.exists(input_video):
        print(f"❌ Error: Could not find a file at '{input_video}'. Please check the spelling and try again.")
    else:
        # Ask where they want to save the result
        output_video = input("Enter the desired output name (e.g., result.mp4): ").strip()
        
        # Start processing
        print(f"\nInitializing AI models for {input_video}...")
        process_video_file(input_video, output_video)