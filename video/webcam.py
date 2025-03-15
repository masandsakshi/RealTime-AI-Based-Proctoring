import cv2
import mediapipe as mp
import numpy as np
import time

# Initialize MediaPipe Face Mesh with iris (refined) landmarks enabled.
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=5,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
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

# Suspicious gaze tracking variables
sus_gaze_active = False  # Flag to track if suspicious gaze is active
sus_gaze_start_time = None  # Timestamp when the suspicious gaze started
sus_gaze_warned = False  # Flag to track if warning has been printed
SUS_GAZE_THRESHOLD = 1.5  # Time in seconds before printing warning

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not access the camera.")
    exit()

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
        if num_faces > 1:
            cv2.putText(frame, "Multiple faces detected!", (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        for face_landmarks in results.multi_face_landmarks:
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1)
            )

            right_iris_center_norm = get_iris_center(face_landmarks, list(range(468, 473)))
            left_iris_center_norm = get_iris_center(face_landmarks, list(range(473, 478)))

            right_iris_center = (int(right_iris_center_norm[0] * w), int(right_iris_center_norm[1] * h))
            left_iris_center = (int(left_iris_center_norm[0] * w), int(left_iris_center_norm[1] * h))

            cv2.circle(frame, right_iris_center, 3, (0, 0, 255), -1)
            cv2.circle(frame, left_iris_center, 3, (0, 0, 255), -1)

            right_eye_bbox = get_eye_bbox(face_landmarks, [33, 133], w, h)
            left_eye_bbox = get_eye_bbox(face_landmarks, [362, 263], w, h)

            cv2.rectangle(frame, (right_eye_bbox[0], right_eye_bbox[1]),
                          (right_eye_bbox[2], right_eye_bbox[3]), (255, 255, 0), 1)
            cv2.rectangle(frame, (left_eye_bbox[0], left_eye_bbox[1]),
                          (left_eye_bbox[2], left_eye_bbox[3]), (255, 255, 0), 1)

            right_gaze = estimate_gaze(right_iris_center, right_eye_bbox)
            left_gaze = estimate_gaze(left_iris_center, left_eye_bbox)

            if right_gaze != "Looking Center" or left_gaze != "Looking Center":
                if not sus_gaze_active:
                    sus_gaze_active = True
                    sus_gaze_start_time = current_time
                    sus_gaze_warned = False  # Reset warning flag for new event
            else:
                sus_gaze_active = False
                sus_gaze_warned = False  # Reset warning if gaze returns to normal

            gaze_text = f"Gaze: {left_gaze} | {right_gaze}"
            cv2.putText(frame, gaze_text, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    else:
        cv2.putText(frame, "No face detected", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        sus_gaze_active = False  # Reset if no face is detected
        sus_gaze_warned = False  # Reset warning if face disappears

    # Check if suspicious gaze has been active for the required time and only print once
    if sus_gaze_active and not sus_gaze_warned and (current_time - sus_gaze_start_time >= SUS_GAZE_THRESHOLD):
        print("⚠️ Suspicious gaze detected!")
        sus_gaze_warned = True  # Prevent repeated warnings

    cv2.imshow("MediaPipe Gaze & Multi-Face Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
