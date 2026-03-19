import os
import time
import numpy as np
import pandas as pd

def generate_rppg_dataset():
    print("Initializing synthetic rPPG dataset generation...")
    
    # Configuration
    num_samples_per_class = 8000
    np.random.seed(42) # For reproducible distributions
    
    # Simulating 30 FPS extraction (1 frame every ~33.3ms)
    # We will generate sequential timestamps starting from current time
    start_time = time.time()
    timestamps_0 = start_time + np.arange(num_samples_per_class) * (1/30.0)
    timestamps_1 = timestamps_0[-1] + (1/30.0) + np.arange(num_samples_per_class) * (1/30.0)

    print("Generating Class 0 (Low Stress / Resting Baseline)...")
    bpm_0 = np.random.normal(loc=75.0, scale=4.0, size=num_samples_per_class)
    sdnn_0 = np.random.normal(loc=75.0, scale=8.0, size=num_samples_per_class)
    rmssd_0 = np.random.normal(loc=65.0, scale=7.0, size=num_samples_per_class)
    pnn50_0 = np.random.normal(loc=25.0, scale=4.0, size=num_samples_per_class)
    label_0 = np.zeros(num_samples_per_class, dtype=int)

    print("Generating Class 1 (High Stress / Sympathetic Arousal)...")
    bpm_1 = np.random.normal(loc=98.0, scale=5.0, size=num_samples_per_class)
    sdnn_1 = np.random.normal(loc=55.0, scale=6.0, size=num_samples_per_class)
    rmssd_1 = np.random.normal(loc=45.0, scale=5.0, size=num_samples_per_class)
    pnn50_1 = np.random.normal(loc=12.0, scale=3.0, size=num_samples_per_class)
    label_1 = np.ones(num_samples_per_class, dtype=int)

    # Compile into DataFrames
    df_0 = pd.DataFrame({
        'timestamp': timestamps_0,
        'bpm': bpm_0,
        'sdnn': sdnn_0,
        'rmssd': rmssd_0,
        'pnn50': pnn50_0,
        'label': label_0
    })

    df_1 = pd.DataFrame({
        'timestamp': timestamps_1,
        'bpm': bpm_1,
        'sdnn': sdnn_1,
        'rmssd': rmssd_1,
        'pnn50': pnn50_1,
        'label': label_1
    })

    # Combine the classes
    df = pd.concat([df_0, df_1], ignore_index=True)

    # --- ENFORCE HARDWARE CONSTRAINTS ---
    print("Applying 30 FPS hardware noise floor constraints...")
    # It is mathematically impossible to have an HRV below ~33.3ms at 30Hz
    df['sdnn'] = df['sdnn'].clip(lower=35.0)
    df['rmssd'] = df['rmssd'].clip(lower=35.0)
    
    # Prevent biologically impossible negative values for boundary edge cases
    df['pnn50'] = df['pnn50'].clip(lower=0.0)
    df['bpm'] = df['bpm'].clip(lower=40.0)

    # Round the physiological metrics to 2 decimal places
    metrics = ['bpm', 'sdnn', 'rmssd', 'pnn50']
    df[metrics] = df[metrics].round(2)
    df['timestamp'] = df['timestamp'].round(3)

    # Shuffle the dataset to ensure the model doesn't learn sequential bias
    print("Shuffling dataset...")
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # Ensure output directory exists
    output_dir = os.path.join('data', 'processed')
    os.makedirs(output_dir, exist_ok=True)
    
    # Save to CSV
    output_path = os.path.join(output_dir, 'dataset_gemini.csv')
    df.to_csv(output_path, index=False)

    print("\n" + "="*40)
    print(f"SUCCESS: Dataset saved to {output_path}")
    print(f"Total Rows: {len(df)}")
    print("="*40)
    
    # Verify the constraints worked
    print("\nVerification of Hardware Constraints (Minimums):")
    print(df.groupby('label')[['sdnn', 'rmssd']].min())

if __name__ == "__main__":
    generate_rppg_dataset()