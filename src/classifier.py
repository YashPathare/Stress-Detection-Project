import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

def train_model():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # POINT THIS TO YOUR NEW CLEANED DATASET
    data_path = os.path.join(script_dir, '..', 'data', 'processed', 'clean_real_stress_dataset.csv')
    
    print(f"Loading REAL dataset from: {data_path}")
    try:
        # Load the CSV
        df = pd.read_csv(data_path)
        
        # FIX: If the cleaning script deleted the header, add it back manually!
        if 'bpm' not in df.columns:
            print("No header detected. Applying column names manually...")
            df = pd.read_csv(data_path, header=None, names=['timestamp', 'bpm', 'sdnn', 'rmssd', 'pnn50(%)', 'label'])
            
    except FileNotFoundError:
        print("Error: clean_real_stress_dataset.csv not found!")
        return

    # Drop any leftover NaNs from recording errors
    df = df.dropna()

    # THE 4 CLINICAL FEATURES
    X = df[['bpm', 'sdnn', 'rmssd', 'pnn50(%)']]
    y = df['label']

    print("Splitting data into 80% Training and 20% Testing...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # We increase the number of trees (n_estimators) because real-world data is noisier!
    print("Training Random Forest Classifier on Real Physiology...")
    rf_classifier = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, class_weight='balanced')
    rf_classifier.fit(X_train_scaled, y_train)

    # --- EVALUATION ---
    y_pred = rf_classifier.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    
    print("\n" + "="*30)
    print("--- MODEL EVALUATION ---")
    print("="*30)
    print(f"Accuracy on Unseen Real Data: {accuracy * 100:.2f}%\n")
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Low Stress (0)', 'High Stress (1)']))

    # --- SAVE THE MODELS ---
    models_dir = os.path.join(script_dir, '..', 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, 'stress_classifier.pkl')
    scaler_path = os.path.join(models_dir, 'scaler.pkl')
    
    joblib.dump(rf_classifier, model_path)
    joblib.dump(scaler, scaler_path)
    
    print("="*30)
    print(f"Success! Model successfully exported to: {model_path}")

if __name__ == "__main__":
    train_model()