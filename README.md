# 📌 Real-Time AI Proctoring System - README

This is an AI-powered proctoring system that monitors keystroke behavior, screen focus, audio, and video activity to detect suspicious behavior during online exams. The system continuously logs activities, computes a risk score out of 100%, and issues warnings or termination alerts based on detected anomalies.

# 📌 Features
🔹 1. Keystroke Behavior Analysis
a. Detects irregular typing patterns using LSTM-based anomaly detection.
b. Logs keystroke speed, hold time, and flight time for risk assessment.
c. Flags unusual typing behavior that may indicate unauthorized assistance.

🔹 2. Screen Focus Monitoring
a. Detects when the user switches tabs or minimizes the window.
b. Logs focus intervals (how long the user was out of focus).
c. Issues warnings if focus loss exceeds a set threshold.

🔹 3. Audio Surveillance (Voice Monitoring & Recording)
a. Records and processes exam room audio.
b. Detects loud noises, conversations, or multiple voices.
c. Flags suspicious background activity during the exam.

🔹 4. Video Monitoring (Face & Gaze Tracking)
a. Detects face presence and movement.
b. Logs gaze direction and multiple face detections.
c. Flags absence from the camera or the presence of multiple faces.

🔹 5. Risk Score Computation & Real-Time Alerts
a. Continuously computes a risk score out of 100% based on violations.
b. Uses time decay weighting (older violations have less impact).
c. Issues warnings or automatic exam termination when risk crosses thresholds.

🔹 6. Batch Processing & Continuous Log Monitoring
a. Monitors activity.log in real-time and processes new data every 5 seconds.
b. Ensures efficient log reading without reprocessing old data.
c. Updates risk scores dynamically as new events occur.

# 📌 Installation & Setup
🔹 1. Install Dependencies
Make sure Python and the required libraries are installed:

pip install tensorflow numpy pandas scikit-learn opencv-python pyaudio

🔹 2. Navigate to the Respective Directories

Move into the correct project directories before running each component.

# 📌 Execution Order

Run the following scripts in this order:

python ai_reciever.py     # Start AI processing

go run main.go            # Start event logging system (Go backend)

python log_reciever.py    # Start log monitoring system

python texteditor.py      # Start frontend (text editor interface)

python flagger.py         # Start logging & risk analysis

🔹 Run texteditor.py last to launch the exam interface.

# 📌 Risk Score & Warnings

Risk Score (%)	Action
0 - 25%	✅ Safe (No action needed)

25 - 45%	🔸 Low Risk (Mild Warning)

45 - 75%	⚠️ Medium Risk (Strong Warning)

75 - 100%	❌ High Risk (Exam Termination)

# 📌 Log File Format (activity.log)

The system reads and processes logs in real-time. The log format includes:

Event       Type	                      Description              	

# Example Log:

ai_check  Keystroke anomaly detected	ai_check Anomaly Detected Score: 12.56

focus	Screen out of focus	focus 20.35 (User out of focus for 20.35 sec)

focus true	User regained focus	focus true 1742105169.737

sus_aud	Loud noise detected	sus_aud LOUD noise detected! 1742105173.246

sus_vid	User left camera view	sus_vid Where you go???? 1742105180.059
