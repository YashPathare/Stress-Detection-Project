import os
import time
import numpy as np
import pandas as pd

def generate_hardware_calibrated_dataset():
    print("Initializing HIGH-MOTION hardware-calibrated dataset...")
    
    num_samples_per_class = 8000
    np.random.seed(42) 
    
    start_time = time.time()
    timestamps_0 = start_time + np.arange(num_samples_per_class) * (1/30.0)
    timestamps_1 = timestamps_0[-1] + (1/30.0) + np.arange(num_samples_per_class) * (1/30.0)

    # --- CLASS 0: LOW STRESS (Resting + Standard Camera Jitter) ---
    print("Generating Class 0: Inflated resting baseline...")
    bpm_0 = np.random.normal(loc=72.0, scale=5.0, size=num_samples_per_class)
    sdnn_0 = np.random.normal(loc=180.0, scale=15.0, size=num_samples_per_class) # INFLATED
    rmssd_0 = np.random.normal(loc=190.0, scale=20.0, size=num_samples_per_class) # INFLATED
    pnn50_0 = np.random.normal(loc=50.0, scale=8.0, size=num_samples_per_class)
    label_0 = np.zeros(num_samples_per_class, dtype=int)

    # --- CLASS 1: HIGH STRESS (Rigid Rhythm + Motion Artifacts from Exercise) ---
    print("Generating Class 1: Inflated stressed baseline (Accounting for movement noise)...")
    bpm_1 = np.random.normal(loc=105.0, scale=7.0, size=num_samples_per_class)
    sdnn_1 = np.random.normal(loc=95.0, scale=12.0, size=num_samples_per_class) # INFLATED
    rmssd_1 = np.random.normal(loc=90.0, scale=15.0, size=num_samples_per_class) # INFLATED
    pnn50_1 = np.random.normal(loc=25.0, scale=5.0, size=num_samples_per_class)
    label_1 = np.ones(num_samples_per_class, dtype=int)

    # Compile into DataFrames
    df_0 = pd.DataFrame({'timestamp': timestamps_0, 'bpm': bpm_0, 'sdnn': sdnn_0, 'rmssd': rmssd_0, 'pnn50': pnn50_0, 'label': label_0})
    df_1 = pd.DataFrame({'timestamp': timestamps_1, 'bpm': bpm_1, 'sdnn': sdnn_1, 'rmssd': rmssd_1, 'pnn50': pnn50_1, 'label': label_1})

    df = pd.concat([df_0, df_1], ignore_index=True)

    # --- ENFORCE HARDWARE CONSTRAINTS ---
    df['sdnn'] = df['sdnn'].clip(lower=35.0)
    df['rmssd'] = df['rmssd'].clip(lower=35.0)
    df['pnn50'] = df['pnn50'].clip(lower=0.0)
    df['bpm'] = df['bpm'].clip(lower=40.0)

    # Round the metrics
    metrics = ['bpm', 'sdnn', 'rmssd', 'pnn50']
    df[metrics] = df[metrics].round(2)
    df['timestamp'] = df['timestamp'].round(3)

    # Shuffle the dataset
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # Ensure output directory exists
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, '..', 'data', 'processed')
    os.makedirs(output_dir, exist_ok=True)
    
    # Save to CSV
    output_path = os.path.join(output_dir, 'corrected_stress_dataset.csv')
    df.to_csv(output_path, index=False)

    print("\n" + "="*40)
    print(f"SUCCESS: High-Motion Calibrated Dataset saved!")
    print("="*40)

if __name__ == "__main__":
    generate_hardware_calibrated_dataset()