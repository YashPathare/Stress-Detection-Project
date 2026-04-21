import customtkinter as ctk
from PIL import Image
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

# --- APP CONFIGURATION ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class StressDetectionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🫀 Clinical Stress Engine - Desktop Edition")
        self.geometry("1100x700")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- LOAD AI MODELS ---
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            self.clf = joblib.load(os.path.join(self.script_dir, 'models', 'stress_classifier.pkl'))
            self.scaler = joblib.load(os.path.join(self.script_dir, 'models', 'scaler.pkl'))
            self.models_loaded = True
        except FileNotFoundError:
            self.models_loaded = False
            print("CRITICAL ERROR: Run classifier.py to generate models.")

        # --- UI LAYOUT ---
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=3)
        self.grid_rowconfigure(1, weight=1)

        # 1. Video Frame (Top Left)
        self.video_frame = ctk.CTkFrame(self)
        self.video_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.video_label = ctk.CTkLabel(self.video_frame, text="Starting Camera...")
        self.video_label.pack(expand=True, fill="both")

        # 2. Metrics Frame (Top Right)
        self.metrics_frame = ctk.CTkFrame(self)
        self.metrics_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.status_label = ctk.CTkLabel(self.metrics_frame, text="INITIALIZING...", font=("Arial", 24, "bold"), text_color="yellow")
        self.status_label.pack(pady=20)

        self.bpm_var = ctk.StringVar(value="BPM: --")
        self.sdnn_var = ctk.StringVar(value="SDNN: -- ms")
        self.rmssd_var = ctk.StringVar(value="RMSSD: -- ms")
        self.pnn50_var = ctk.StringVar(value="pNN50: -- %")

        ctk.CTkLabel(self.metrics_frame, textvariable=self.bpm_var, font=("Arial", 20)).pack(pady=10, anchor="w", padx=20)
        ctk.CTkLabel(self.metrics_frame, textvariable=self.sdnn_var, font=("Arial", 20)).pack(pady=10, anchor="w", padx=20)
        ctk.CTkLabel(self.metrics_frame, textvariable=self.rmssd_var, font=("Arial", 20)).pack(pady=10, anchor="w", padx=20)
        ctk.CTkLabel(self.metrics_frame, textvariable=self.pnn50_var, font=("Arial", 20)).pack(pady=10, anchor="w", padx=20)

        self.progress_bar = ctk.CTkProgressBar(self.metrics_frame)
        self.progress_bar.pack(pady=20, padx=20, fill="x")
        self.progress_bar.set(0)

        # 3. Graph Frame (Bottom Spanning)
        self.graph_frame = ctk.CTkFrame(self)
        self.graph_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(self.graph_frame, text="Live Blood Volume Pulse (rPPG)", font=("Arial", 12)).pack(anchor="nw", padx=10, pady=5)
        
        # Native Tkinter Canvas is incredibly fast for drawing live lines
        self.canvas = ctk.CTkCanvas(self.graph_frame, bg="#2b2b2b", highlightthickness=0, height=100)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=5)

        # --- ENGINE VARIABLES ---
        self.cap = cv2.VideoCapture(0)
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False)
        
        self.BUFFER_SIZE = 250
        self.raw_signal = []
        self.timestamps = []
        self.bpm_history, self.sdnn_history, self.rmssd_history, self.pnn50_history, self.prediction_history = deque(maxlen=45), deque(maxlen=45), deque(maxlen=45), deque(maxlen=45), deque(maxlen=45)

        # Start the background loop
        if self.models_loaded:
            self.update_video()

    def update_video(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)

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

                            self.raw_signal.append(g_normalized)
                            self.timestamps.append(time.time())

                            current_len = len(self.raw_signal)
                            if current_len < self.BUFFER_SIZE:
                                self.progress_bar.set(current_len / self.BUFFER_SIZE)
                                self.status_label.configure(text=f"BUFFERING: {current_len}/250", text_color="yellow")
                            else:
                                self.progress_bar.set(1.0)
                                self.process_math_pipeline()
                                
                                # Pop oldest frame
                                self.raw_signal.pop(0)
                                self.timestamps.pop(0)

            # Render CV2 frame to CustomTkinter Label
            cv2_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(cv2_image)
            # Resize image to fit label width while maintaining aspect ratio
            label_w = self.video_label.winfo_width()
            if label_w > 10:
                aspect = pil_image.height / pil_image.width
                new_h = int(label_w * aspect)
                pil_image = pil_image.resize((label_w, new_h))
            
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(pil_image.width, pil_image.height))
            self.video_label.configure(image=ctk_image, text="")

        # Schedule the next frame update in 15 milliseconds (~60fps target loop)
        self.after(15, self.update_video)

    def process_math_pipeline(self):
        sig, t = np.array(self.raw_signal), np.array(self.timestamps)
        fps = self.BUFFER_SIZE / (t[-1] - t[0])
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

                # Update live graph natively
                self.draw_graph(upsampled_signal[-250:])

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
                        scaled_features = self.scaler.transform(features)
                        ml_prediction = self.clf.predict(scaled_features)[0]

                        self.bpm_history.append(bpm)
                        self.sdnn_history.append(sdnn)
                        self.rmssd_history.append(rmssd)
                        self.pnn50_history.append(pnn50)
                        self.prediction_history.append(ml_prediction)

                        if len(self.bpm_history) > 15:
                            display_bpm = np.mean(self.bpm_history)
                            display_sdnn = np.mean(self.sdnn_history)
                            display_rmssd = np.mean(self.rmssd_history)
                            display_pnn50 = np.mean(self.pnn50_history)
                            most_common_pred = mode(self.prediction_history, keepdims=True).mode[0]
                        else:
                            display_bpm, display_sdnn, display_rmssd, display_pnn50 = bpm, sdnn, rmssd, pnn50
                            most_common_pred = ml_prediction

                        # Update UI Text
                        self.bpm_var.set(f"BPM: {display_bpm:.1f}")
                        self.sdnn_var.set(f"SDNN: {display_sdnn:.1f} ms")
                        self.rmssd_var.set(f"RMSSD: {display_rmssd:.1f} ms")
                        self.pnn50_var.set(f"pNN50: {display_pnn50:.1f} %")

                        # Hybrid Logic
                        if display_bpm > 95.0 or display_rmssd < 20.0:
                            self.status_label.configure(text="HIGH STRESS", text_color="#ff4444")
                        else:
                            if most_common_pred == 0:
                                self.status_label.configure(text="RELAXED", text_color="#00C851")
                            else:
                                self.status_label.configure(text="HIGH STRESS", text_color="#ff4444")
                    else:
                        self.status_label.configure(text="NOISY SIGNAL", text_color="orange")
                else:
                    self.status_label.configure(text="SEARCHING PEAKS", text_color="yellow")
            except ValueError:
                pass

    def draw_graph(self, data):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10: return

        # Normalize data to fit canvas height
        d_min, d_max = data.min(), data.max()
        if d_min == d_max: return
        
        norm_data = (data - d_min) / (d_max - d_min)
        
        # Build coordinates for the line
        points = []
        for i, val in enumerate(norm_data):
            x = int((i / len(norm_data)) * w)
            y = h - int(val * h)
            points.append(x)
            points.append(y)
            
        if len(points) >= 4:
            self.canvas.create_line(points, fill="#00E676", width=2, smooth=True)

    def on_closing(self):
        if self.cap.isOpened():
            self.cap.release()
        self.destroy()

if __name__ == "__main__":
    app = StressDetectionApp()
    app.mainloop()