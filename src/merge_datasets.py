import pandas as pd
import os

def combine_and_clean_datasets():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    processed_dir = os.path.join(script_dir, '..', 'data', 'processed')
    
    # 1. Load the three files (Change these filenames if yours are different)
    try:
        df1 = pd.read_csv(os.path.join(processed_dir, 'dataset_chatgpt.csv'))
        df2 = pd.read_csv(os.path.join(processed_dir, 'dataset_gemini.csv'))
        df3 = pd.read_csv(os.path.join(processed_dir, 'dataset_claude.csv'))
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        print("Make sure you saved all 3 CSVs in the data/processed folder with the correct names!")
        return

    print(f"Loaded {len(df1)} rows from ChatGPT")
    print(f"Loaded {len(df2)} rows from Gemini")
    print(f"Loaded {len(df3)} rows from Claude")

    # 2. Combine them into one massive DataFrame
    combined_df = pd.concat([df1, df2, df3], ignore_index=True)
    print(f"\nTotal rows before cleaning: {len(combined_df)}")

    # 3. SAFETY CHECK 1: Drop Duplicates (The Random Seed Trap)
    # We ignore the 'timestamp' column when looking for duplicates, 
    # checking if the exact biological numbers were repeated.
    combined_df = combined_df.drop_duplicates(subset=['bpm', 'sdnn', 'rmssd', 'pnn50', 'label'])
    print(f"Total unique rows after dropping duplicates: {len(combined_df)}")

    # 4. SAFETY CHECK 2: Enforce the 30 FPS Hardware Rule
    # Just in case one of the AIs forgot our prompt instructions!
    combined_df['sdnn'] = combined_df['sdnn'].clip(lower=35.0)
    combined_df['rmssd'] = combined_df['rmssd'].clip(lower=35.0)

    # 5. Shuffle the final master dataset perfectly
    combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)

    # 6. Save the ultimate dataset
    final_path = os.path.join(processed_dir, 'corrected_stress_dataset.csv')
    combined_df.to_csv(final_path, index=False)
    
    print("\n" + "="*40)
    print(f"SUCCESS: Master dataset saved to {final_path}")
    print("="*40)

if __name__ == "__main__":
    combine_and_clean_datasets()