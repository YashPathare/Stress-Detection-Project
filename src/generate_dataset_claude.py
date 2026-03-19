"""
Synthetic Dataset Generator for Video-Based Remote Photoplethysmography (rPPG)
Stress Detection System

Hardware Constraint Modelled:
    - Standard 30 FPS webcam (1 frame per ~33.3ms)
    - Enforced lower bound of 35.0 ms on SDNN and RMSSD to respect the
      Nyquist-like noise floor imposed by the 30 FPS sampling rate.

Classes:
    - Class 0: Low Stress / Parasympathetic / Resting
    - Class 1: High Stress / Sympathetic Arousal

Author : Biomedical ML Engineer
"""

import os
import numpy as np
import pandas as pd

# ─── Reproducibility ──────────────────────────────────────────────────────────
SEED = 42
rng  = np.random.default_rng(SEED)

# ─── Dataset Configuration ────────────────────────────────────────────────────
N_PER_CLASS   = 8_000          # samples per class  →  16 000 total
FPS_NOISE_FLOOR = 35.0         # 30 FPS hard lower bound for SDNN & RMSSD (ms)

OUTPUT_PATH = "data/processed/dataset_claude.csv"

# ─── Biological Distribution Parameters ───────────────────────────────────────
DISTRIBUTIONS = {
    # label: {feature: (mean, std)}
    0: {          # ── Low Stress / Resting ──────────────────────────────────
        "bpm"  : (75.0,  4.0),
        "sdnn" : (75.0,  8.0),
        "rmssd": (65.0,  7.0),
        "pnn50": (25.0,  4.0),
    },
    1: {          # ── High Stress / Sympathetic Arousal ─────────────────────
        "bpm"  : (98.0,  5.0),
        "sdnn" : (55.0,  6.0),   # drops under stress
        "rmssd": (45.0,  5.0),   # drops under stress, still > noise floor
        "pnn50": (12.0,  3.0),
    },
}

# ─── Physiological Clipping Bounds ────────────────────────────────────────────
# (min, max) — None means no bound on that side
CLIP_BOUNDS = {
    "bpm"  : (30.0,  220.0),   # physiologically plausible HR range
    "sdnn" : (FPS_NOISE_FLOOR, 200.0),  # 35 ms hard floor (30 FPS constraint)
    "rmssd": (FPS_NOISE_FLOOR, 200.0),  # 35 ms hard floor (30 FPS constraint)
    "pnn50": (0.0,   100.0),   # percentage — must stay in [0, 100]
}

# ─── Timestamp Configuration ──────────────────────────────────────────────────
# Simulated 5-second HRV windows recorded at wall-clock time
WINDOW_SECONDS = 5
START_TIME     = pd.Timestamp("2024-01-01 08:00:00")


def sample_feature(label: int, feature: str, n: int) -> np.ndarray:
    """Draw n samples from the specified class/feature distribution, then clip."""
    mean, std = DISTRIBUTIONS[label][feature]
    samples   = rng.normal(loc=mean, scale=std, size=n)
    lo, hi    = CLIP_BOUNDS[feature]
    return np.clip(samples, lo, hi)


def build_class_dataframe(label: int, n: int) -> pd.DataFrame:
    """Generate n rows for a single class label."""
    return pd.DataFrame({
        "bpm"  : sample_feature(label, "bpm",   n),
        "sdnn" : sample_feature(label, "sdnn",  n),
        "rmssd": sample_feature(label, "rmssd", n),
        "pnn50": sample_feature(label, "pnn50", n),
        "label": label,
    })


def generate_timestamps(n: int) -> pd.Series:
    """
    Create n evenly-spaced timestamps.
    Each row represents one 5-second HRV analysis window.
    """
    offsets = pd.to_timedelta(
        np.arange(n) * WINDOW_SECONDS, unit="s"
    )
    return START_TIME + offsets


def main() -> None:
    print("=" * 60)
    print("  rPPG Stress Detection — Synthetic Dataset Generator")
    print("=" * 60)

    # 1. Generate per-class DataFrames
    print(f"\n[1/5]  Sampling Class 0 (Low Stress)   — {N_PER_CLASS:,} rows …")
    df_class0 = build_class_dataframe(label=0, n=N_PER_CLASS)

    print(f"[2/5]  Sampling Class 1 (High Stress)  — {N_PER_CLASS:,} rows …")
    df_class1 = build_class_dataframe(label=1, n=N_PER_CLASS)

    # 2. Concatenate and shuffle
    print("[3/5]  Concatenating and shuffling rows …")
    df = (
        pd.concat([df_class0, df_class1], ignore_index=True)
          .sample(frac=1, random_state=SEED)
          .reset_index(drop=True)
    )

    # 3. Attach timestamps (post-shuffle so they are monotonically increasing
    #    in the final row order — as a continuous recording would be)
    df.insert(0, "timestamp", generate_timestamps(len(df)))

    # 4. Round physiological metrics
    print("[4/5]  Rounding physiological metrics to 2 decimal places …")
    for col in ["bpm", "sdnn", "rmssd", "pnn50"]:
        df[col] = df[col].round(2)

    # 5. Save to CSV
    print(f"[5/5]  Saving dataset → {OUTPUT_PATH}")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    # ─── Validation Report ────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print("  VALIDATION REPORT")
    print("─" * 60)
    print(f"  Total rows        : {len(df):,}")
    print(f"  Class distribution:\n{df['label'].value_counts().to_string()}")
    print(f"\n  30 FPS Noise Floor Constraint (≥ {FPS_NOISE_FLOOR} ms)")
    print(f"    SDNN  min  : {df['sdnn'].min():.2f} ms  ✓" if df['sdnn'].min()  >= FPS_NOISE_FLOOR else "    SDNN  min  : VIOLATION ✗")
    print(f"    RMSSD min  : {df['rmssd'].min():.2f} ms  ✓" if df['rmssd'].min() >= FPS_NOISE_FLOOR else "    RMSSD min  : VIOLATION ✗")
    print(f"\n  Per-class feature statistics:")
    print(
        df.groupby("label")[["bpm", "sdnn", "rmssd", "pnn50"]]
          .agg(["mean", "std", "min", "max"])
          .round(2)
          .to_string()
    )
    print("\n  Dataset saved successfully.")
    print("─" * 60 + "\n")


if __name__ == "__main__":
    main()