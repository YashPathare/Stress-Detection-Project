import pandas as pd
import numpy as np
import os

# ==============================
# Configuration
# ==============================
NUM_SAMPLES_PER_CLASS = 8000
TOTAL_SAMPLES = NUM_SAMPLES_PER_CLASS * 2

# Noise floor constraint (IMPORTANT)
HRV_LOWER_BOUND = 35.0

# Output path
output_path = "data/processed/dataset_chatgpt.csv"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# ==============================
# Helper Function
# ==============================
def generate_class_data(mean_dict, std_dict, label, n):
    data = {}

    for feature in mean_dict:
        values = np.random.normal(loc=mean_dict[feature],
                                  scale=std_dict[feature],
                                  size=n)

        # Apply physiological constraint for HRV features
        if feature in ["sdnn", "rmssd"]:
            values = np.clip(values, HRV_LOWER_BOUND, None)

        data[feature] = values

    df = pd.DataFrame(data)
    df["label"] = label
    return df

# ==============================
# Class 0 (Low Stress)
# ==============================
mean_0 = {
    "bpm": 75.0,
    "sdnn": 75.0,
    "rmssd": 65.0,
    "pnn50": 25.0
}

std_0 = {
    "bpm": 4.0,
    "sdnn": 8.0,
    "rmssd": 7.0,
    "pnn50": 4.0
}

df_0 = generate_class_data(mean_0, std_0, label=0, n=NUM_SAMPLES_PER_CLASS)

# ==============================
# Class 1 (High Stress)
# ==============================
mean_1 = {
    "bpm": 98.0,
    "sdnn": 55.0,
    "rmssd": 45.0,
    "pnn50": 12.0
}

std_1 = {
    "bpm": 5.0,
    "sdnn": 6.0,
    "rmssd": 5.0,
    "pnn50": 3.0
}

df_1 = generate_class_data(mean_1, std_1, label=1, n=NUM_SAMPLES_PER_CLASS)

# ==============================
# Combine & Shuffle
# ==============================
df = pd.concat([df_0, df_1], ignore_index=True)

# Add timestamp column (simulate sequential sampling)
df["timestamp"] = np.arange(0, TOTAL_SAMPLES)

# Reorder columns
df = df[["timestamp", "bpm", "sdnn", "rmssd", "pnn50", "label"]]

# Shuffle dataset
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Round values to 2 decimal places
df[["bpm", "sdnn", "rmssd", "pnn50"]] = df[["bpm", "sdnn", "rmssd", "pnn50"]].round(2)

# ==============================
# Save CSV
# ==============================
df.to_csv(output_path, index=False)

print(f"Dataset generated successfully with {len(df)} rows.")
print(f"Saved to: {output_path}")