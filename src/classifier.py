import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

def train_stress_classifier():
    # 1. Setup Absolute Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Using the biologically corrected dataset!
    data_path = os.path.join(script_dir, '..', 'data', 'processed', 'corrected_stress_dataset.csv')
    models_dir = os.path.join(script_dir, '..', 'models')
    
    # Ensure the models directory exists
    os.makedirs(models_dir, exist_ok=True)
    
    # 2. Load the Cleaned Dataset
    print(f"Loading dataset from: {data_path}")
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        # Fixed the typo in the error message
        print("Error: Could not find 'corrected_stress_dataset.csv'. Ensure it is in the data/processed folder.")
        return
        
    # 3. Prepare Features (X) and Target Labels (y)
    # Sticking to the 3 core metrics extracted by your face_detection.py script
    X = df[['bpm', 'sdnn', 'rmssd']]
    y = df['label']
    
    # 4. Train-Test Split (80% for training, 20% for testing)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # 5. Feature Scaling (Standardization)
    print("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 6. Initialize and Train the Random Forest Model
    print("Training Random Forest Classifier...")
    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    clf.fit(X_train_scaled, y_train)
    
    # 7. Evaluate the Model
    y_pred = clf.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    
    print("\n" + "="*30)
    print("--- MODEL EVALUATION ---")
    print("="*30)
    print(f"Accuracy on Test Data: {accuracy * 100:.2f}%\n")
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Low Stress (0)', 'High Stress (1)']))
    
    # 8. Export the Model and the Scaler
    model_path = os.path.join(models_dir, 'stress_classifier.pkl')
    scaler_path = os.path.join(models_dir, 'scaler.pkl')
    
    joblib.dump(clf, model_path)
    joblib.dump(scaler, scaler_path)
    
    print("="*30)
    print(f"Success! Model successfully exported to: {model_path}")
    print(f"Scaler successfully exported to: {scaler_path}")

if __name__ == "__main__":
    train_stress_classifier()