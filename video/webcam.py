# webcam.py
import cv2
import mediapipe as mp
import numpy as np
import time
import requests
import json
import threading

# Backend URL (you can override it via the start function parameter)
DEFAULT_URL = "http://localhost:8080/publish"

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=5,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)
mp_drawing = mp.solutions.drawing_utils


# Utility functions
def get_iris_center(landmarks, iris_indices):
    xs = [landmarks.landmark[i].x for i in iris_indices]
    ys = [landmarks.landmark[i].y for i in iris_indices]
    return np.mean(xs), np.mean(ys)


def get_eye_bbox(landmarks, corner_indices, image_w, image_h):
    x_vals = [landmarks.landmark[i].x for i in corner_indices]
    y_vals = [landmarks.landmark[i].y for i in corner_indices]
    x1 = int(min(x_vals) * image_w)
    x2 = int(max(x_vals) * image_w)
    y1 = int(min(y_vals) * image_h)
    y2 = int(max(y_vals) * image_h)
    return x1, y1, x2, y2


def estimate_gaze(iris_center, eye_bbox):
    if iris_center is None:
        return "Undetected"
    x_center, _ = iris_center
    x1, _, x2, _ = eye_bbox
    if x_center < x1 + (x2 - x1) * 0.35:
        return "Looking Left"
    elif x_center > x1 + (x2 - x1) * 0.65:
        return "Looking Right"
    else:
        return "Looking Center"


def send_alert(url, alert_type, message):
    """Helper function to send alert messages to backend."""
    try:
        timestamp = time.time()
        # Create event with the standardized format
        event = {"Type": "sus_vid", "Value": [message, f"{timestamp:.3f}"]}

        # Wrap the event in a data array as expected by main.go
        payload = {"data": [event]}
        json_payload = json.dumps(payload)
        print(f"Sending video alert: {json_payload}")

        response = requests.post(
            url,
            data=json_payload,
            headers={"Content-Type": "application/json"},
            timeout=1,
        )
        print(f"Video alert sent, status: {response.status_code}")
    except Exception as e:
        print(f"Failed to send alert: {e}")


def _video_monitoring_loop(url):
    ALERT_COOLDOWN = 3  # Cooldown between alerts
    SUS_GAZE_THRESHOLD = 1.5  # Suspicious gaze detection time

    last_alert_time = 0
    sus_gaze_active = False
    sus_gaze_start_time = None
    sus_gaze_warned = False

    multi_face_start_time = None
    no_face_start_time = None
    MULTI_FACE_THRESHOLD = 5  # Seconds to trigger alert for multiple faces
    NO_FACE_THRESHOLD = 5  # Seconds to trigger alert for no faces

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not access the camera.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)
        current_time = time.time()

        if results.multi_face_landmarks:
            num_faces = len(results.multi_face_landmarks)

            # MULTIPLE FACE DETECTION LOGIC
            if num_faces > 1:
                if multi_face_start_time is None:
                    multi_face_start_time = current_time  # Start timer
                elif current_time - multi_face_start_time >= MULTI_FACE_THRESHOLD:
                    if current_time - last_alert_time >= ALERT_COOLDOWN:
                        send_alert(url, "multi_face", "Ye Kaun Hai!!")
                        last_alert_time = current_time
                        multi_face_start_time = None  # Reset timer after sending alert
            else:
                multi_face_start_time = None  # Reset if faces go back to normal

            # Process each face
            for face_landmarks in results.multi_face_landmarks:
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing.DrawingSpec(
                        color=(0, 255, 0), thickness=1, circle_radius=1
                    ),
                )

                right_iris_center_norm = get_iris_center(
                    face_landmarks, list(range(468, 473))
                )
                left_iris_center_norm = get_iris_center(
                    face_landmarks, list(range(473, 478))
                )

                right_iris_center = (
                    int(right_iris_center_norm[0] * w),
                    int(right_iris_center_norm[1] * h),
                )
                left_iris_center = (
                    int(left_iris_center_norm[0] * w),
                    int(left_iris_center_norm[1] * h),
                )

                right_eye_bbox = get_eye_bbox(face_landmarks, [33, 133], w, h)
                left_eye_bbox = get_eye_bbox(face_landmarks, [362, 263], w, h)

                right_gaze = estimate_gaze(right_iris_center, right_eye_bbox)
                left_gaze = estimate_gaze(left_iris_center, left_eye_bbox)

                if right_gaze != "Looking Center" or left_gaze != "Looking Center":
                    if not sus_gaze_active:
                        sus_gaze_active = True
                        sus_gaze_start_time = current_time
                        sus_gaze_warned = False
                else:
                    sus_gaze_active = False
                    sus_gaze_warned = False

        else:
            # NO FACE DETECTION LOGIC
            if no_face_start_time is None:
                no_face_start_time = current_time  # Start timer
            elif current_time - no_face_start_time >= NO_FACE_THRESHOLD:
                if current_time - last_alert_time >= ALERT_COOLDOWN:
                    send_alert(url, "no_face", "Where you go????")
                    last_alert_time = current_time
                    no_face_start_time = None  # Reset timer after alert
        if results.multi_face_landmarks:
            no_face_start_time = None  # Reset if face reappears

        # SUSPICIOUS GAZE DETECTION
        if (
            sus_gaze_active
            and not sus_gaze_warned
            and (current_time - sus_gaze_start_time >= SUS_GAZE_THRESHOLD)
        ):
            print("⚠ Suspicious gaze detected!")
            sus_gaze_warned = True
            if current_time - last_alert_time >= ALERT_COOLDOWN:
                send_alert(url, "suspicious_gaze", "Where you look?")
                last_alert_time = current_time

        cv2.imshow("Gaze & Face Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


def start_video_monitoring(url=DEFAULT_URL):
    """Starts the video monitoring in a separate daemon thread."""
    video_thread = threading.Thread(
        target=_video_monitoring_loop, args=(url,), daemon=True
    )
    video_thread.start()
