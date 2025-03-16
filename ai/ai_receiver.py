# # import numpy as np
# # from flask import Flask, request, jsonify
# # import time
# # from tensorflow.keras.models import load_model
# # from collections import deque

# # app = Flask(__name__)

# # # Load the trained LSTM model
# # print("Loading LSTM model...")
# # model = load_model("lstm_autoencoder.keras")
# # print("Model loaded successfully.")

# # # Buffers for keystroke logging and model processing
# # keystroke_buffer = deque(maxlen=100)  # Stores incoming keystroke events for processing
# # model_buffer = deque(maxlen=50)  # Stores processed keystroke features for the model

# # batch_size = 50  # LSTM expects input in batches of 50

# # # Keycode mapping for multi-character keys
# # keycode_map = {
# #     'Backspace': 8, 'Tab': 9, 'Enter': 13, 'Shift': 16, 'Ctrl': 17, 'Alt': 18,
# #     'Caps Lock': 20, 'Esc': 27, 'Space': 32, 'Page Up': 33, 'Page Down': 34,
# #     'End': 35, 'Home': 36, 'Left arrow': 37, 'Up arrow': 38, 'Right arrow': 39,
# #     'Down arrow': 40, 'Insert': 45, 'Delete': 46, 'Num Lock': 144, 'Scroll Lock': 145
# # }

# # print("Initializing Flask app...")

# # @app.route("/key_press", methods=["POST"])
# # def records():
# #     """
# #     Receives keystroke events, processes them, and detects anomalies when batch is full.
# #     """
# #     try:
# #         data = request.get_json()
# #         print(f"Received data: {data}")
        
# #         if not data:
# #             return jsonify({"error": "No data received"}), 400

# #         # Push new keystroke event to the buffer
# #         keystroke_buffer.append(data)
# #         print(f"Keystroke buffer size: {len(keystroke_buffer)}")

# #         # Process the keystroke into a feature vector
# #         processed_features = process_keystroke(data)
        
# #         if processed_features:
# #             model_buffer.append(processed_features)
# #             print(f"Model buffer size: {len(model_buffer)}")

# #         # Process when model buffer reaches 50 samples
# #         if len(model_buffer) == batch_size:
# #             print("Processing batch...")
# #             batch_features = np.array(model_buffer)

# #             is_anomaly, error, threshold = detect_anomaly(batch_features)
# #             print(f"Anomalies: {is_anomaly}, Errors: {error}, Threshold: {threshold}")

# #             # ✅ Fix: Clear model_buffer after processing
# #             model_buffer.clear()

# #             return jsonify({
# #                 "anomalies": is_anomaly,
# #                 "errors": error,
# #                 "threshold": threshold
# #             }), 200

# #         return jsonify({"message": "Waiting for 50 keystrokes"}), 202

# #     except Exception as e:
# #         print(f"Error: {e}")
# #         return jsonify({"error": str(e)}), 500

# # def process_keystroke(event):
# #     """
# #     Processes an individual keystroke event into a feature vector.
# #     """
# #     if len(keystroke_buffer) < 2:
# #         return None  # Not enough data to compute features

# #     prev_event = keystroke_buffer[-2]
# #     prev_key, prev_action, prev_timestamp = prev_event['Value']
# #     prev_timestamp = float(prev_timestamp)

# #     key, action, timestamp = event['Value']
# #     timestamp = float(timestamp)

# #     # ✅ Fix: Handle multi-character keys
# #     key1 = keycode_map.get(prev_key, ord(prev_key[0]) if prev_key else 0)
# #     key2 = keycode_map.get(key, ord(key[0]) if key else 0)

# #     features = [
# #         key1, key2, 
# #         round((timestamp - prev_timestamp) if prev_key == key and prev_action == "KD" and action == "KU" else 0, 3),  # DU.key1.key1
# #         round((timestamp - prev_timestamp) if prev_action == "KD" and action == "KD" else 0, 3),  # DD.key1.key2
# #         round((timestamp - prev_timestamp) if prev_action == "KU" and action == "KD" else 0, 3)  # DU.key1.key2
# #     ]

# #     return features

# # def detect_anomaly(batch_features):
# #     """
# #     Detect anomalies using the LSTM model.
# #     """
# #     print("Detecting anomalies...")

# #     if len(batch_features) < batch_size:
# #         print("Not enough data to process.")
# #         return [], [], 0.5

# #     batch_features = np.array(batch_features, dtype=np.float32).reshape((1, batch_size, 5))
# #     print("Feeding data into model for prediction...")

# #     reconstructed = model.predict(batch_features)
# #     error = np.mean(np.abs(reconstructed - batch_features), axis=1)
# #     is_anomaly = error > 0.5

# #     print(f"Anomaly detection complete. Errors: {error}")
# #     return is_anomaly.tolist(), error.tolist(), 0.5

# # if __name__ == "__main__":
# #     print("Starting Flask server...")
# #     app.run(debug=True)
# import numpy as np
# from flask import Flask, request, jsonify
# import time
# from tensorflow.keras.models import load_model
# from collections import deque

# app = Flask(__name__)

# # Load the trained LSTM model
# print("Loading LSTM model...")
# model = load_model("lstm_autoencoder.keras")
# print("Model loaded successfully.")

# # Buffers for keystroke logging and model processing
# keystroke_buffer = deque(maxlen=300)  # Stores incoming keystroke events for processing
# model_buffer = deque(maxlen=50)  # Stores processed keystroke features for the model

# batch_size = 50  # LSTM expects input in batches of 50

# # Buffers for error tracking and adaptive thresholding
# error_history = deque(maxlen=500)
# user_data = deque(maxlen=500)

# keycode_map = {
#     'Backspace': 8, 'Tab': 9, 'Enter': 13, 'Shift': 16, 'Ctrl': 17, 'Alt': 18, 'Pause/Break': 19, 'Caps Lock': 20, 'Esc': 27,
#     'Space': 32, 'Page Up': 33, 'Page Down': 34, 'End': 35, 'Home': 36, 'Left arrow': 37, 'Up arrow': 38, 'Right arrow': 39, 'Down arrow': 40,
#     'Print Screen': 44, 'Insert': 45, 'Delete': 46, 
#     '0': 48, '1': 49, '2': 50, '3': 51, '4': 52, '5': 53, '6': 54, '7': 55, '8': 56, '9': 57,
#     'A': 65, 'B': 66, 'C': 67, 'D': 68, 'E': 69, 'F': 70, 'G': 71, 'H': 72, 'I': 73, 'J': 74, 'K': 75, 'L': 76, 'M': 77, 
#     'N': 78, 'O': 79, 'P': 80, 'Q': 81, 'R': 82, 'S': 83, 'T': 84, 'U': 85, 'V': 86, 'W': 87, 'X': 88, 'Y': 89, 'Z': 90,
#     'a': 97, 'b': 98, 'c': 99, 'd': 100, 'e': 101, 'f': 102, 'g': 103, 'h': 104, 'i': 105, 'j': 106, 'k': 107, 'l': 108, 'm': 109, 'n': 110,
#     'o': 111, 'p': 112, 'q': 113, 'r': 114, 's': 115, 't': 116, 'u': 117, 'v': 118, 'w': 119, 'x': 120, 'y': 121, 'z': 122, 
#     'Left Win': 91, 'Right Win': 92, 'Menu': 93,
    
#     # Numeric keypad
#     'Numpad 0': 96, 'Numpad 1': 97, 'Numpad 2': 98, 'Numpad 3': 99, 'Numpad 4': 100, 'Numpad 5': 101, 
#     'Numpad 6': 102, 'Numpad 7': 103, 'Numpad 8': 104, 'Numpad 9': 105, 'Numpad *': 106, 'Numpad +': 107, 
#     'Numpad -': 109, 'Numpad .': 110, 'Numpad /': 111,

#     # Function keys
#     'F1': 112, 'F2': 113, 'F3': 114, 'F4': 115, 'F5': 116, 'F6': 117, 'F7': 118, 'F8': 119, 'F9': 120, 
#     'F10': 121, 'F11': 122, 'F12': 123,

#     # Locks and shifts
#     'Num Lock': 144, 'Scroll Lock': 145, 
#     'Left Shift': 160, 'Right Shift': 161, 'Left Ctrl': 162, 'Right Ctrl': 163, 
#     'Left Alt': 164, 'Right Alt': 165,

#     # Symbols and punctuation
#     '`': 192, '-': 189, '=': 187, '[': 219, ']': 221, '\\': 220, ';': 186, '\'': 222, 
#     ',': 188, '.': 190, '/': 191,

#     # Multimedia keys (varies by keyboard)
#     'Volume Mute': 173, 'Volume Down': 174, 'Volume Up': 175, 
#     'Media Next': 176, 'Media Previous': 177, 'Media Stop': 178, 'Media Play/Pause': 179
# }

# print("Initializing Flask app...")

# @app.route("/key_press", methods=["POST"])
# def records():
#     """
#     Receives keystroke events, processes them, and detects anomalies when batch is full.
#     """
#     try:
#         data = request.get_json()
#         print(f"Received data: {data}")
        
#         if not data:
#             return jsonify({"error": "No data received"}), 400

#         # Push new keystroke event to the buffer
#         keystroke_buffer.append(data)
#         print(f"Keystroke buffer size: {len(keystroke_buffer)}")

#         # Process the keystroke into a feature vector
#         processed_features = process_keystroke(data)
        
#         if processed_features:
#             model_buffer.append(processed_features)
#             print(f"Model buffer size: {len(model_buffer)}")

#         # Process when model buffer reaches 50 samples
#         if len(model_buffer) == batch_size:
#             print("Processing batch...")
#             batch_features = np.array(model_buffer)

#             is_anomaly, error, threshold = detect_anomaly(batch_features)
#             print(f"Anomalies: {is_anomaly}, Errors: {error}, Threshold: {threshold}")

#             # ✅ Clear model_buffer after processing
#             model_buffer.clear()

#             return jsonify({
#                 "anomalies": is_anomaly,
#                 "errors": error,
#                 "threshold": threshold
#             }), 200

#         return jsonify({"message": "Waiting for 50 keystrokes"}), 202

#     except Exception as e:
#         print(f"Error: {e}")
#         return jsonify({"error": str(e)}), 500

# def process_keystroke(event):
#     """
#     Processes an individual keystroke event into a feature vector.
#     """
#     if len(keystroke_buffer) < 2:
#         return None  # Not enough data to compute features

#     prev_event = keystroke_buffer[-2]
#     prev_key, prev_action, prev_timestamp = prev_event['Value']
#     prev_timestamp = float(prev_timestamp)

#     key, action, timestamp = event['Value']
#     timestamp = float(timestamp)

#     # ✅ Handle multi-character keys
#     key1 = keycode_map.get(prev_key, ord(prev_key[0]) if prev_key else 0)
#     key2 = keycode_map.get(key, ord(key[0]) if key else 0)

#     features = [
#         key1, key2, 
#         round((timestamp - prev_timestamp) if prev_key == key and prev_action == "KD" and action == "KU" else 0, 3),  # DU.key1.key1
#         round((timestamp - prev_timestamp) if prev_action == "KD" and action == "KD" else 0, 3),  # DD.key1.key2
#         round((timestamp - prev_timestamp) if prev_action == "KU" and action == "KD" else 0, 3)  # DU.key1.key2
#     ]

#     return features

# def compute_threshold(reconstruction_errors, k=1):
#     """
#     Computes an adaptive threshold based on past reconstruction errors.
#     """
#     if len(reconstruction_errors) < 10:  # Ensure at least 10 errors exist before computing
#         return np.mean(reconstruction_errors) + k * np.std(reconstruction_errors) + 0.1  # Small buffer
#     else:
#         recent_errors = reconstruction_errors[-500:]
#         return np.mean(recent_errors) + k * np.std(recent_errors)

# def detect_anomaly(batch_features):
#     """
#     Detect anomalies using the LSTM model with adaptive thresholding.
#     """
#     global model

#     print("Detecting anomalies...")
#     if len(batch_features) < batch_size:
#         print("Not enough data to process.")
#         return [], [], 0.5

#     batch_features = np.array(batch_features, dtype=np.float32).reshape((1, batch_size, 5))
#     print("Feeding data into model for prediction...")

#     reconstructed = model.predict(batch_features)
#     error = np.mean(np.abs(reconstructed - batch_features))
#     error_history.append(error)

#     # Compute adaptive threshold
#     threshold = compute_threshold(list(error_history))

#     # Flag anomaly if error exceeds threshold
#     is_anomaly = error > threshold
#     user_data.append(batch_features)

#     if is_anomaly:
#         print(f"⚠️ Anomaly Detected! Error: {error}, Threshold: {threshold}")

#     # Fine-tune the model on user's recent keystrokes after collecting enough data
#     if len(user_data) == 500:
#         print("Fine-tuning model on user's recent keystrokes...")
#         X_train = np.array(list(user_data)).reshape(-1, batch_size, 5)
#         model.fit(X_train, X_train, epochs=3, batch_size=32, verbose=0)
#         model.save("keystroke_autoencoder.keras")  # Save updated model

#     return is_anomaly, error, threshold

# if __name__ == "__main__":
#     print("Starting Flask server...")
#     app.run(debug=True)
# import numpy as np
# from flask import Flask, request, jsonify
# import time
# from tensorflow.keras.models import load_model
# from collections import deque

# app = Flask(__name__)

# # Load the trained LSTM model
# print("Loading LSTM model...")
# model = load_model("lstm_autoencoder_2.keras")
# print("Model loaded successfully.")

# # **Global Hyperparameters**
# k = 0.1  # Sensitivity factor (higher = fewer anomalies, lower = more anomalies)
# window_size = 500  # Number of past keystrokes to consider for thresholding & fine-tuning
# fine_tune_epochs = 3  # Number of epochs for online fine-tuning
# batch_size = 50  # LSTM expects input in batches of 50

# # Buffers for keystroke logging and model processing
# keystroke_buffer = deque(maxlen=300)  # Stores incoming keystroke events for processing
# model_buffer = deque(maxlen=batch_size)  # Stores processed keystroke features for the model

# # Buffers for error tracking and adaptive thresholding
# error_history = deque(maxlen=window_size)
# user_data = deque(maxlen=window_size)

# # Keycode mapping for multi-character keys
# keycode_map = {
#     'Backspace': 8, 'Tab': 9, 'Enter': 13, 'Shift': 16, 'Ctrl': 17, 'Alt': 18, 'Pause/Break': 19, 'Caps Lock': 20, 'Esc': 27,
#     'Space': 32, 'Page Up': 33, 'Page Down': 34, 'End': 35, 'Home': 36, 'Left arrow': 37, 'Up arrow': 38, 'Right arrow': 39, 'Down arrow': 40,
#     'Print Screen': 44, 'Insert': 45, 'Delete': 46, 
#     '0': 48, '1': 49, '2': 50, '3': 51, '4': 52, '5': 53, '6': 54, '7': 55, '8': 56, '9': 57,
#     'A': 65, 'B': 66, 'C': 67, 'D': 68, 'E': 69, 'F': 70, 'G': 71, 'H': 72, 'I': 73, 'J': 74, 'K': 75, 'L': 76, 'M': 77, 
#     'N': 78, 'O': 79, 'P': 80, 'Q': 81, 'R': 82, 'S': 83, 'T': 84, 'U': 85, 'V': 86, 'W': 87, 'X': 88, 'Y': 89, 'Z': 90,
#     'a': 97, 'b': 98, 'c': 99, 'd': 100, 'e': 101, 'f': 102, 'g': 103, 'h': 104, 'i': 105, 'j': 106, 'k': 107, 'l': 108, 'm': 109, 'n': 110,
#     'o': 111, 'p': 112, 'q': 113, 'r': 114, 's': 115, 't': 116, 'u': 117, 'v': 118, 'w': 119, 'x': 120, 'y': 121, 'z': 122, 
#     'Left Win': 91, 'Right Win': 92, 'Menu': 93,
    
#     # Numeric keypad
#     'Numpad 0': 96, 'Numpad 1': 97, 'Numpad 2': 98, 'Numpad 3': 99, 'Numpad 4': 100, 'Numpad 5': 101, 
#     'Numpad 6': 102, 'Numpad 7': 103, 'Numpad 8': 104, 'Numpad 9': 105, 'Numpad *': 106, 'Numpad +': 107, 
#     'Numpad -': 109, 'Numpad .': 110, 'Numpad /': 111,

#     # Function keys
#     'F1': 112, 'F2': 113, 'F3': 114, 'F4': 115, 'F5': 116, 'F6': 117, 'F7': 118, 'F8': 119, 'F9': 120, 
#     'F10': 121, 'F11': 122, 'F12': 123,

#     # Locks and shifts
#     'Num Lock': 144, 'Scroll Lock': 145, 
#     'Left Shift': 160, 'Right Shift': 161, 'Left Ctrl': 162, 'Right Ctrl': 163, 
#     'Left Alt': 164, 'Right Alt': 165,

#     # Symbols and punctuation
#     '`': 192, '-': 189, '=': 187, '[': 219, ']': 221, '\\': 220, ';': 186, '\'': 222, 
#     ',': 188, '.': 190, '/': 191,

#     # Multimedia keys (varies by keyboard)
#     'Volume Mute': 173, 'Volume Down': 174, 'Volume Up': 175, 
#     'Media Next': 176, 'Media Previous': 177, 'Media Stop': 178, 'Media Play/Pause': 179
# }

# print("Initializing Flask app...")

# @app.route("/key_press", methods=["POST"])
# def records():
#     """
#     Receives keystroke events, processes them, and detects anomalies when batch is full.
#     """
#     try:
#         data = request.get_json()
#         print(f"Received data: {data}")
        
#         if not data:
#             return jsonify({"error": "No data received"}), 400

#         # Push new keystroke event to the buffer
#         keystroke_buffer.append(data)
#         print(f"Keystroke buffer size: {len(keystroke_buffer)}")

#         # Process the keystroke into a feature vector
#         processed_features = process_keystroke(data)
        
#         if processed_features:
#             model_buffer.append(processed_features)
#             print(f"Model buffer size: {len(model_buffer)}")

#         # Process when model buffer reaches 50 samples
#         if len(model_buffer) == batch_size:
#             print("Processing batch...")
#             batch_features = np.array(model_buffer)

#             is_anomaly, error, threshold = detect_anomaly(batch_features)
#             print(f"Anomalies: {is_anomaly}, Errors: {error}, Threshold: {threshold}")

#             # ✅ Clear model_buffer after processing
#             model_buffer.clear()

#             return jsonify({
#                 "anomalies": is_anomaly,
#                 "errors": error,
#                 "threshold": threshold
#             }), 200

#         return jsonify({"message": "Waiting for 50 keystrokes"}), 202

#     except Exception as e:
#         print(f"Error: {e}")
#         return jsonify({"error": str(e)}), 500

# def process_keystroke(event):
#     """
#     Processes an individual keystroke event into a feature vector.
#     """
#     if len(keystroke_buffer) < 2:
#         return None  # Not enough data to compute features

#     prev_event = keystroke_buffer[-2]
#     prev_key, prev_action, prev_timestamp = prev_event['Value']
#     prev_timestamp = float(prev_timestamp)

#     key, action, timestamp = event['Value']
#     timestamp = float(timestamp)

#     # ✅ Handle multi-character keys
#     key1 = keycode_map.get(prev_key, ord(prev_key[0]) if prev_key else 0)
#     key2 = keycode_map.get(key, ord(key[0]) if key else 0)

#     features = [
#         key1, key2, 
#         round((timestamp - prev_timestamp) if prev_key == key and prev_action == "KD" and action == "KU" else 0, 3),  # DU.key1.key1
#         round((timestamp - prev_timestamp) if prev_action == "KD" and action == "KD" else 0, 3),  # DD.key1.key2
#         round((timestamp - prev_timestamp) if prev_action == "KU" and action == "KD" else 0, 3)  # DU.key1.key2
#     ]

#     return features

# def compute_threshold(reconstruction_errors, k):
#     """
#     Computes an adaptive threshold based on past reconstruction errors.
#     """
#     if len(reconstruction_errors) < 10:  
#         return np.mean(reconstruction_errors) + k * np.std(reconstruction_errors) + 0.1  
#     else:
#         recent_errors = reconstruction_errors[-window_size:]  # ✅ Uses global `window_size`
#         return np.mean(recent_errors) + k * np.std(recent_errors)

# def detect_anomaly(batch_features):
#     """
#     Detect anomalies using the LSTM model with adaptive thresholding.
#     """
#     global model

#     print("Detecting anomalies...")
#     if len(batch_features) < batch_size:
#         print("Not enough data to process.")
#         return [], [], 0.5

#     batch_features = np.array(batch_features, dtype=np.float32).reshape((1, batch_size, 5))
#     print("Feeding data into model for prediction...")

#     reconstructed = model.predict(batch_features)
#     error = np.mean(np.abs(reconstructed - batch_features))
#     error_history.append(error)

#     # ✅ Use the global `k` value
#     threshold = compute_threshold(list(error_history), k)

#     is_anomaly = error > threshold
#     user_data.append(batch_features)

#     if is_anomaly:
#         print(f"⚠️ Anomaly Detected! Error: {error}, Threshold: {threshold}")

#     # ✅ Fine-tune the model on user's recent keystrokes every `window_size` entries
#     if len(user_data) == window_size:
#         print("Fine-tuning model on user's recent keystrokes...")
#         X_train = np.array(list(user_data)).reshape(-1, batch_size, 5)
#         model.fit(X_train, X_train, epochs=fine_tune_epochs, batch_size=32, verbose=0)  # ✅ Uses global `fine_tune_epochs`
#         model.save("keystroke_autoencoder.keras")  

#     return is_anomaly, error, threshold

# if __name__ == "__main__":
#     print("Starting Flask server...")
#     app.run(debug=True)

# import numpy as np
# from flask import Flask, request, jsonify
# import time
# from tensorflow.keras.models import load_model
# from collections import deque

# app = Flask(__name__)

# # Load the trained LSTM model
# print("Loading LSTM model...")
# model = load_model("lstm_autoencoder.keras")
# print("Model loaded successfully.")

# # **Global Hyperparameters**
# k = 0.1  # Sensitivity factor (higher = fewer anomalies, lower = more anomalies)
# window_size = 500  # Number of past keystrokes to consider for thresholding & fine-tuning
# fine_tune_epochs = 3  # Number of epochs for online fine-tuning
# batch_size = 50  # LSTM expects input in batches of 50

# # **Calibration Settings**
# calibration_limit = 250  # Number of keystrokes before threshold stops updating
# calibration_done = False  # Flag to indicate if calibration is complete
# fixed_threshold = None  # Store final threshold after calibration

# # Buffers for keystroke logging and model processing
# keystroke_buffer = deque(maxlen=300)  # Stores incoming keystroke events for processing
# model_buffer = deque(maxlen=batch_size)  # Stores processed keystroke features for the model

# # Buffers for error tracking and adaptive thresholding
# error_history = deque(maxlen=window_size)
# user_data = deque(maxlen=window_size)

# print("Initializing Flask app...")

# @app.route("/key_press", methods=["POST"])
# def records():
#     """
#     Receives keystroke events, processes them, and detects anomalies when batch is full.
#     """
#     try:
#         data = request.get_json()
#         print(f"Received data: {data}")

#         if not data:
#             return jsonify({"error": "No data received"}), 400

#         keystroke_buffer.append(data)
#         print(f"Keystroke buffer size: {len(keystroke_buffer)}")

#         # ✅ Fix: Check if processing is possible before calling process_keystroke
#         if len(keystroke_buffer) >= 2:
#             processed_features = process_keystroke(data)

#             if processed_features:
#                 model_buffer.append(processed_features)
#                 print(f"Model buffer size: {len(model_buffer)}")

#         if len(model_buffer) == batch_size:
#             print("Processing batch...")
#             batch_features = np.array(model_buffer)

#             is_anomaly, error, threshold = detect_anomaly(batch_features)
#             print(f"Anomalies: {is_anomaly}, Errors: {error}, Threshold: {threshold}")

#             model_buffer.clear()  # ✅ Clear model_buffer after processing

#             return jsonify({
#                 "anomalies": is_anomaly,
#                 "errors": error,
#                 "threshold": threshold
#             }), 200

#         return jsonify({"message": "Waiting for 50 keystrokes"}), 202

#     except Exception as e:
#         print(f"Error: {e}")
#         return jsonify({"error": str(e)}), 500

# def process_keystroke(event):
#     """
#     Processes an individual keystroke event into a feature vector.
#     """
#     if len(keystroke_buffer) < 2:
#         return None  # Not enough data to compute features

#     prev_event = keystroke_buffer[-2]
#     prev_key, prev_action, prev_timestamp = prev_event['Value']
#     prev_timestamp = float(prev_timestamp)

#     key, action, timestamp = event['Value']
#     timestamp = float(timestamp)

#     # Compute features based on keystroke timing
#     hold_time = round((timestamp - prev_timestamp) if prev_key == key and prev_action == "KD" and action == "KU" else 0, 3)  
#     flight_time = round((timestamp - prev_timestamp) if prev_action == "KD" and action == "KD" else 0, 3)  
#     up_down_time = round((timestamp - prev_timestamp) if prev_action == "KU" and action == "KD" else 0, 3)  

#     features = [ord(prev_key), ord(key), hold_time, flight_time, up_down_time]
    
#     return features

# def compute_threshold(reconstruction_errors, k):
#     """
#     Computes an adaptive threshold but stops recalibrating after a certain limit.
#     """
#     global calibration_done, fixed_threshold

#     if len(reconstruction_errors) >= calibration_limit and not calibration_done:
#         calibration_done = True  # ✅ Stop updating the threshold
#         fixed_threshold = np.mean(reconstruction_errors) + k * np.std(reconstruction_errors)  # ✅ Store final threshold
#         print(f"⚠️ Threshold calibration stopped at: {fixed_threshold}")

#     if calibration_done:
#         return fixed_threshold  # ✅ Use stored threshold after calibration

#     if len(reconstruction_errors) < 10:
#         return np.mean(reconstruction_errors) + k * np.std(reconstruction_errors) + 0.1  
#     else:
#         return np.mean(reconstruction_errors[-window_size:]) + k * np.std(reconstruction_errors)

# def detect_anomaly(batch_features):
#     """
#     Detect anomalies using the LSTM model with adaptive thresholding.
#     """
#     global model

#     print("Detecting anomalies...")
#     if len(batch_features) < batch_size:
#         print("Not enough data to process.")
#         return [], [], 0.5

#     batch_features = np.array(batch_features, dtype=np.float32).reshape((1, batch_size, 5))
#     print("Feeding data into model for prediction...")

#     reconstructed = model.predict(batch_features)
#     error = np.mean(np.abs(reconstructed - batch_features))

#     # ✅ Stop updating error_history after calibration limit
#     if not calibration_done:
#         error_history.append(error)

#     threshold = compute_threshold(list(error_history), k)

#     is_anomaly = error > threshold
#     user_data.append(batch_features)

#     if is_anomaly:
#         print(f"⚠️ Anomaly Detected! Error: {error}, Threshold: {threshold}")

#     return is_anomaly, error, threshold

# if __name__ == "__main__":
#     print("Starting Flask server...")
#     app.run(debug=True)

# import numpy as np
# from flask import Flask, request, jsonify
# import time
# from tensorflow.keras.models import load_model
# from collections import deque

# app = Flask(__name__)

# # Load the trained LSTM model
# print("Loading LSTM model...")
# model = load_model("lstm_autoencoder_2.keras")
# print("Model loaded successfully.")

# # **Global Hyperparameters**
# k = 0.1  # Sensitivity factor (higher = fewer anomalies, lower = more anomalies)
# window_size = 500  # Number of past keystrokes to consider for thresholding
# fine_tune_epochs = 3  # Number of epochs for online fine-tuning
# batch_size = 50  # LSTM expects input in batches of 50

# # **Calibration Settings**
# calibration_limit = 500  # Keystrokes before threshold stops updating
# calibration_done = False  # Flag to indicate if calibration is complete
# fixed_threshold = None  # Placeholder for the final threshold

# # Buffers for keystroke logging and model processing
# keystroke_buffer = deque(maxlen=300)  # Stores incoming keystroke events for processing
# model_buffer = deque(maxlen=batch_size)  # Stores processed keystroke features for the model

# # Buffers for error tracking and adaptive thresholding
# error_history = deque(maxlen=window_size)
# user_data = deque(maxlen=window_size)

# # Keycode mapping for multi-character keys
# keycode_map = {
#     'Backspace': 8, 'Tab': 9, 'Enter': 13, 'Shift': 16, 'Ctrl': 17, 'Alt': 18, 
#     'Caps_Lock': 20, 'Esc': 27, 'Space': 32, 'Page Up': 33, 'Page Down': 34,
#     'End': 35, 'Home': 36, 'Left arrow': 37, 'Up arrow': 38, 'Right arrow': 39, 'Down arrow': 40,
#     'Insert': 45, 'Delete': 46, 'Num Lock': 144, 'Scroll Lock': 145
# }

# print("Initializing Flask app...")

# @app.route("/key_press", methods=["POST"])
# def records():
#     """
#     Receives keystroke events, processes them, and detects anomalies when batch is full.
#     """
#     global calibration_done, fixed_threshold

#     try:
#         data = request.get_json()
#         print(f"Received data: {data}")

#         if not data:
#             return jsonify({"error": "No data received"}), 400

#         keystroke_buffer.append(data)
#         print(f"Keystroke buffer size: {len(keystroke_buffer)}")

#         processed_features = process_keystroke(data)
        
#         if processed_features:
#             model_buffer.append(processed_features)
#             print(f"Model buffer size: {len(model_buffer)}")

#         if len(model_buffer) == batch_size:
#             print("Processing batch...")
#             batch_features = np.array(model_buffer)

#             is_anomaly, error, threshold = detect_anomaly(batch_features)

#             print(f"Anomalies: {is_anomaly}, Errors: {error}, Threshold: {threshold}")

#             model_buffer.clear()

#             return jsonify({
#                 "anomalies": int(is_anomaly),  # ✅ Convert bool to int for JSON
#                 "errors": float(error),        # ✅ Ensure float is JSON serializable
#                 "threshold": float(threshold)
#             }), 200

#         return jsonify({"message": "Waiting for 50 keystrokes"}), 202

#     except Exception as e:
#         print(f"Error: {e}")
#         return jsonify({"error": str(e)}), 500

# def process_keystroke(event):
#     """
#     Processes an individual keystroke event into a feature vector.
#     """
#     if len(keystroke_buffer) < 2:
#         return None  # Not enough data to compute features

#     prev_event = keystroke_buffer[-2]
#     prev_key, prev_action, prev_timestamp = prev_event['Value']
#     prev_timestamp = float(prev_timestamp)

#     key, action, timestamp = event['Value']
#     timestamp = float(timestamp)

#     # ✅ Handle multi-character keys properly
#     key1 = keycode_map.get(prev_key, 0)
#     key2 = keycode_map.get(key, 0)

#     features = [
#         key1, key2, 
#         round((timestamp - prev_timestamp) if prev_key == key and prev_action == "KD" and action == "KU" else 0, 3),  
#         round((timestamp - prev_timestamp) if prev_action == "KD" and action == "KD" else 0, 3),  
#         round((timestamp - prev_timestamp) if prev_action == "KU" and action == "KD" else 0, 3)  
#     ]

#     return features

# def compute_threshold(reconstruction_errors):
#     """
#     Computes an adaptive threshold but stops recalibrating after a certain limit.
#     """
#     global calibration_done, fixed_threshold

#     if len(reconstruction_errors) >= calibration_limit and not calibration_done:
#         calibration_done = True  # ✅ Stop updating the threshold
#         fixed_threshold = np.mean(reconstruction_errors) + k * np.std(reconstruction_errors)
#         print(f"⚠️ Threshold calibration stopped. Using fixed threshold: {fixed_threshold}")

#     if calibration_done:
#         return fixed_threshold  # ✅ Use the fixed threshold after calibration

#     if len(reconstruction_errors) < 10:
#         return np.mean(reconstruction_errors) + k * np.std(reconstruction_errors) + 0.1  
#     else:
#         return np.mean(reconstruction_errors[-window_size:]) + k * np.std(reconstruction_errors)

# def detect_anomaly(batch_features):
#     """
#     Detect anomalies using the LSTM model with adaptive thresholding.
#     """
#     global model

#     print("Detecting anomalies...")
#     if len(batch_features) < batch_size:
#         print("Not enough data to process.")
#         return False, 0.5, 0.5

#     batch_features = np.array(batch_features, dtype=np.float32).reshape((1, batch_size, 5))
#     print("Feeding data into model for prediction...")

#     reconstructed = model.predict(batch_features)
#     error = np.mean(np.abs(reconstructed - batch_features))

#     # ✅ Stop updating error_history after calibration limit
#     if not calibration_done:
#         error_history.append(error)

#     threshold = compute_threshold(list(error_history))

#     is_anomaly = error > threshold
#     user_data.append(batch_features)

#     if is_anomaly:
#         print(f"⚠️ Anomaly Detected! Error: {error}, Threshold: {threshold}")

#     return is_anomaly, error, threshold

# if __name__ == "__main__":
#     print("Starting Flask server...")
#     app.run(debug=True)

# import numpy as np
# from flask import Flask, request, jsonify
# import time
# from tensorflow.keras.models import load_model
# from collections import deque

# app = Flask(__name__)

# # Load the trained LSTM model
# print("Loading LSTM model...")
# model = load_model("lstm_autoencoder.keras")
# print("Model loaded successfully.")

# # **Global Hyperparameters**
# k = 0.1  # Sensitivity factor
# window_size = 500  # Past keystrokes for thresholding
# fine_tune_epochs = 3  # Online fine-tuning epochs
# batch_size = 50  # LSTM expects input in batches of 50

# # **Threshold Stabilization Settings**
# stabilization_window = 3  # Number of consecutive threshold updates to check for stability
# stabilization_tolerance = 0.01  # Max variation allowed for stability detection
# threshold_history = deque(maxlen=stabilization_window)
# calibration_done = False  # Flag to indicate if calibration is complete
# fixed_threshold = None  # Stores final threshold after stabilization

# # Buffers for keystroke logging and processing
# keystroke_buffer = deque(maxlen=300)  
# model_buffer = deque(maxlen=batch_size)

# # Buffers for error tracking and adaptive thresholding
# error_history = deque(maxlen=window_size)
# user_data = deque(maxlen=window_size)

# # **Keycode Mapping for Multi-Character Keys**
# keycode_map = {
#     'Backspace': 8, 'Tab': 9, 'Enter': 13, 'Shift': 16, 'Ctrl': 17, 'Alt': 18, 'Pause/Break': 19, 'Caps Lock': 20, 'Esc': 27,
#     'Space': 32, 'Page Up': 33, 'Page Down': 34, 'End': 35, 'Home': 36, 'Left arrow': 37, 'Up arrow': 38, 'Right arrow': 39, 'Down arrow': 40,
#     'Print Screen': 44, 'Insert': 45, 'Delete': 46, 
#     '0': 48, '1': 49, '2': 50, '3': 51, '4': 52, '5': 53, '6': 54, '7': 55, '8': 56, '9': 57,
#     'A': 65, 'B': 66, 'C': 67, 'D': 68, 'E': 69, 'F': 70, 'G': 71, 'H': 72, 'I': 73, 'J': 74, 'K': 75, 'L': 76, 'M': 77, 
#     'N': 78, 'O': 79, 'P': 80, 'Q': 81, 'R': 82, 'S': 83, 'T': 84, 'U': 85, 'V': 86, 'W': 87, 'X': 88, 'Y': 89, 'Z': 90,
#     'a': 97, 'b': 98, 'c': 99, 'd': 100, 'e': 101, 'f': 102, 'g': 103, 'h': 104, 'i': 105, 'j': 106, 'k': 107, 'l': 108, 'm': 109, 'n': 110,
#     'o': 111, 'p': 112, 'q': 113, 'r': 114, 's': 115, 't': 116, 'u': 117, 'v': 118, 'w': 119, 'x': 120, 'y': 121, 'z': 122, 
#     'Left Win': 91, 'Right Win': 92, 'Menu': 93,
    
#     # Numeric keypad
#     'Numpad 0': 96, 'Numpad 1': 97, 'Numpad 2': 98, 'Numpad 3': 99, 'Numpad 4': 100, 'Numpad 5': 101, 
#     'Numpad 6': 102, 'Numpad 7': 103, 'Numpad 8': 104, 'Numpad 9': 105, 'Numpad *': 106, 'Numpad +': 107, 
#     'Numpad -': 109, 'Numpad .': 110, 'Numpad /': 111,

#     # Function keys
#     'F1': 112, 'F2': 113, 'F3': 114, 'F4': 115, 'F5': 116, 'F6': 117, 'F7': 118, 'F8': 119, 'F9': 120, 
#     'F10': 121, 'F11': 122, 'F12': 123,

#     # Locks and shifts
#     'Num Lock': 144, 'Scroll Lock': 145, 
#     'Left Shift': 160, 'Right Shift': 161, 'Left Ctrl': 162, 'Right Ctrl': 163, 
#     'Left Alt': 164, 'Right Alt': 165,

#     # Symbols and punctuation
#     '`': 192, '-': 189, '=': 187, '[': 219, ']': 221, '\\': 220, ';': 186, '\'': 222, 
#     ',': 188, '.': 190, '/': 191,

#     # Multimedia keys (varies by keyboard)
#     'Volume Mute': 173, 'Volume Down': 174, 'Volume Up': 175, 
#     'Media Next': 176, 'Media Previous': 177, 'Media Stop': 178, 'Media Play/Pause': 179
# }

# print("Initializing Flask app...")

# @app.route("/key_press", methods=["POST"])
# def records():
#     """
#     Receives keystroke events, processes them, and detects anomalies when batch is full.
#     """
#     global calibration_done, fixed_threshold

#     try:
#         data = request.get_json()
#         print(f"Received data: {data}")

#         if not data:
#             return jsonify({"error": "No data received"}), 400

#         keystroke_buffer.append(data)
#         print(f"Keystroke buffer size: {len(keystroke_buffer)}")

#         if len(keystroke_buffer) >= 2:
#             processed_features = process_keystroke(data)

#             if processed_features:
#                 model_buffer.append(processed_features)
#                 print(f"Model buffer size: {len(model_buffer)}")

#         if len(model_buffer) == batch_size:
#             print("Processing batch...")
#             batch_features = np.array(model_buffer)

#             is_anomaly, error, threshold = detect_anomaly(batch_features)

#             print(f"Anomalies: {is_anomaly}, Errors: {error}, Threshold: {threshold}")

#             model_buffer.clear()

#             return jsonify({
#                 "anomalies": int(is_anomaly),
#                 "errors": float(error),
#                 "threshold": float(threshold)
#             }), 200

#         return jsonify({"message": "Waiting for 50 keystrokes"}), 202

#     except Exception as e:
#         print(f"Error: {e}")
#         return jsonify({"error": str(e)}), 500

# def process_keystroke(event):
#     """
#     Processes an individual keystroke event into a feature vector.
#     """
#     if len(keystroke_buffer) < 2:
#         return None  # Not enough data to compute features

#     prev_event = keystroke_buffer[-2]
#     prev_key, prev_action, prev_timestamp = prev_event['Value']
#     prev_timestamp = float(prev_timestamp)

#     key, action, timestamp = event['Value']
#     timestamp = float(timestamp)

#     # ✅ Handle multi-character keys properly
#     key1 = keycode_map.get(prev_key, ord(prev_key[0]) if len(prev_key) == 1 else 0)
#     key2 = keycode_map.get(key, ord(key[0]) if len(key) == 1 else 0)

#     features = [
#         key1, key2, 
#         round((timestamp - prev_timestamp) if prev_key == key and prev_action == "KD" and action == "KU" else 0, 3),  
#         round((timestamp - prev_timestamp) if prev_action == "KD" and action == "KD" else 0, 3),  
#         round((timestamp - prev_timestamp) if prev_action == "KU" and action == "KD" else 0, 3)  
#     ]

#     return features

# def compute_threshold(reconstruction_errors):
#     """
#     Computes an adaptive threshold but stops recalibrating once it stabilizes.
#     """
#     global calibration_done, fixed_threshold

#     if len(reconstruction_errors) < 10:
#         return np.mean(reconstruction_errors) + k * np.std(reconstruction_errors) + 0.1  

#     threshold = np.mean(reconstruction_errors[-window_size:]) + k * np.std(reconstruction_errors)
    
#     # Store the new threshold in history
#     threshold_history.append(threshold)

#     # ✅ Check if the threshold has stabilized
#     if len(threshold_history) == stabilization_window:
#         max_threshold = max(threshold_history)
#         min_threshold = min(threshold_history)

#         if abs(max_threshold - min_threshold) <= stabilization_tolerance:
#             calibration_done = True
#             fixed_threshold = threshold
#             print(f"⚠️ Threshold stabilized at: {fixed_threshold}, stopping calibration.")

#     if calibration_done:
#         return fixed_threshold  # ✅ Use fixed threshold after stabilization

#     return threshold

# def detect_anomaly(batch_features):
#     """
#     Detect anomalies using the LSTM model with adaptive thresholding.
#     """
#     global model

#     print("Detecting anomalies...")
#     if len(batch_features) < batch_size:
#         print("Not enough data to process.")
#         return False, 0.5, 0.5

#     batch_features = np.array(batch_features, dtype=np.float32).reshape((1, batch_size, 5))
#     print("Feeding data into model for prediction...")

#     reconstructed = model.predict(batch_features)
#     error = np.mean(np.abs(reconstructed - batch_features))

#     if not calibration_done:
#         error_history.append(error)

#     threshold = compute_threshold(list(error_history))

#     is_anomaly = error > threshold
#     user_data.append(batch_features)

#     if is_anomaly:
#         print(f"⚠️ Anomaly Detected! Error: {error}, Threshold: {threshold}")

#     return is_anomaly, error, threshold

# if __name__ == "__main__":
#     print("Starting Flask server...")
#     app.run(debug=True)

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
