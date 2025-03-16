import numpy as np
import requests  # ✅ Import requests for logging
from flask import Flask, request, jsonify
import time
from tensorflow.keras.models import load_model
from collections import deque

app = Flask(__name__)

# Load the trained LSTM model
print("Loading LSTM model...")
model = load_model("lstm_autoencoder.keras")
print("Model loaded successfully.")

# **Global Hyperparameters**
k = 0.2  # Sensitivity factor
window_size = 500  # Past keystrokes for thresholding
fine_tune_epochs = 3  # Online fine-tuning epochs
batch_size = 50  # LSTM expects input in batches of 50

# **Threshold Stabilization Settings**
stabilization_window = 3  # Number of consecutive threshold updates to check for stability
stabilization_tolerance = 0.01  # Max variation allowed for stability detection
threshold_history = deque(maxlen=stabilization_window)
calibration_done = False  # Flag to indicate if calibration is complete
fixed_threshold = None  # Stores final threshold after stabilization

# Buffers for keystroke logging and processing
keystroke_buffer = deque(maxlen=300)  
model_buffer = deque(maxlen=batch_size)

# Buffers for error tracking and adaptive thresholding
error_history = deque(maxlen=window_size)
user_data = deque(maxlen=window_size)

# **Logging Endpoint**
LOGGING_URL = "http://localhost:6000/log"  # ✅ Endpoint to send anomaly logs

print("Initializing Flask app...")

@app.route("/key_press", methods=["POST"])
def records():
    """
    Receives keystroke events, processes them, and detects anomalies when batch is full.
    """
    global calibration_done, fixed_threshold

    try:
        data = request.get_json()
        print(f"Received data: {data}")

        if not data:
            return jsonify({"error": "No data received"}), 400

        keystroke_buffer.append(data)
        print(f"Keystroke buffer size: {len(keystroke_buffer)}")

        if len(keystroke_buffer) >= 2:
            processed_features = process_keystroke(data)

            if processed_features:
                model_buffer.append(processed_features)
                print(f"Model buffer size: {len(model_buffer)}")

        if len(model_buffer) == batch_size:
            print("Processing batch...")
            batch_features = np.array(model_buffer)

            is_anomaly, error, threshold = detect_anomaly(batch_features)

            print(f"Anomalies: {is_anomaly}, Errors: {error}, Threshold: {threshold}")

            model_buffer.clear()

            return jsonify({
                "anomalies": int(is_anomaly),
                "errors": float(error),
                "threshold": float(threshold)
            }), 200

        return jsonify({"message": "Waiting for 50 keystrokes"}), 202

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

def process_keystroke(event):
    """
    Processes an individual keystroke event into a feature vector.
    """
    if len(keystroke_buffer) < 2:
        return None  # Not enough data to compute features

    prev_event = keystroke_buffer[-2]
    prev_key, prev_action, prev_timestamp = prev_event['Value']
    prev_timestamp = float(prev_timestamp)

    key, action, timestamp = event['Value']
    timestamp = float(timestamp)

    # ✅ Handle multi-character keys properly
    key1 = ord(prev_key[0]) if len(prev_key) == 1 else 0
    key2 = ord(key[0]) if len(key) == 1 else 0

    features = [
        key1, key2, 
        round((timestamp - prev_timestamp) if prev_key == key and prev_action == "KD" and action == "KU" else 0, 3),  
        round((timestamp - prev_timestamp) if prev_action == "KD" and action == "KD" else 0, 3),  
        round((timestamp - prev_timestamp) if prev_action == "KU" and action == "KD" else 0, 3)  
    ]

    print(f"Processed keystroke: {features}")  # ✅ Debugging statement
    return features

def compute_threshold(reconstruction_errors):
    """
    Computes an adaptive threshold but stops recalibrating once it stabilizes.
    """
    global calibration_done, fixed_threshold

    if len(reconstruction_errors) < 10:
        return np.mean(reconstruction_errors) + k * np.std(reconstruction_errors) + 0.1  

    threshold = np.mean(reconstruction_errors[-window_size:]) + k * np.std(reconstruction_errors)
    
    # Store the new threshold in history
    threshold_history.append(threshold)

    # ✅ Check if the threshold has stabilized
    if len(threshold_history) == stabilization_window:
        max_threshold = max(threshold_history)
        min_threshold = min(threshold_history)

        if abs(max_threshold - min_threshold) <= stabilization_tolerance:
            calibration_done = True
            fixed_threshold = threshold
            print(f"⚠️ Threshold stabilized at: {fixed_threshold}, stopping calibration.")

    if calibration_done:
        return fixed_threshold  # ✅ Use fixed threshold after stabilization

    print(f"Updated threshold: {threshold}")  # ✅ Debugging statement
    return threshold

def detect_anomaly(batch_features):
    """
    Detect anomalies using the LSTM model with adaptive thresholding.
    """
    global model

    print("Detecting anomalies...")
    if len(batch_features) < batch_size:
        print("Not enough data to process.")
        return False, 0.5, 0.5

    batch_features = np.array(batch_features, dtype=np.float32).reshape((1, batch_size, 5))
    print("Feeding data into model for prediction...")

    reconstructed = model.predict(batch_features)
    error = np.mean(np.abs(reconstructed - batch_features))

    if not calibration_done:
        error_history.append(error)

    threshold = compute_threshold(list(error_history))
    is_anomaly = error > threshold

    print(f"Error: {error}, Threshold: {threshold}, Anomaly: {is_anomaly}")  # ✅ Debugging statement

    # ✅ Send anomaly logs to external logging server
    if is_anomaly:
        log_anomaly(error, threshold)

    return is_anomaly, error, threshold

def log_anomaly(error, threshold):
    """
    Sends anomaly detection logs to an external server.
    """
    try:
        payload = {
            "Type":"ai_check",
            "Value": ["Anomaly Detected", f"Score: {float(error - threshold)}"]  # ✅ Convert np.float32 to Python float
        }
        print(f"Sending anomaly log: {payload}")  # ✅ Debugging statement
        requests.post(LOGGING_URL, json=payload, timeout=2)
    except requests.exceptions.RequestException as e:
        print(f"Failed to send log: {e}")  # ✅ Debugging statement

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True)  # ✅ Debug mode enabled
