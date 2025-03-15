# audio_analyzer.py
import time
import numpy as np
import sounddevice as sd
import webrtcvad
import requests as req
import json
import threading


def start_audio_monitoring(
    url="http://localhost:8080/publish",
    amplitude_threshold=0.1,
    suspicious_duration_threshold=5,
):
    """
    Starts a background thread that continuously monitors audio.

    - If speech is detected, it sends a payload indicating suspicious conversation.
    - If loud noise persists for longer than the threshold, it sends a payload indicating suspicious activity.
    """

    def audio_monitoring_loop():
        FS = 16000  # Sampling rate (Hz); optimal for webrtcvad
        CHUNK_DURATION = 1.0  # Duration (in seconds) per audio chunk
        CHUNK_SAMPLES = int(FS * CHUNK_DURATION)
        vad = webrtcvad.Vad(1)  # Aggressiveness mode: 0 (least) to 3 (most)
        suspicious_duration = 0

        while True:
            try:
                # Capture one chunk of audio (16-bit PCM)
                chunk = sd.rec(CHUNK_SAMPLES, samplerate=FS, channels=1, dtype="int16")
                sd.wait()

                # Convert chunk to float for amplitude analysis (range: -1 to 1)
                float_chunk = chunk.flatten().astype(np.float32) / 32768.0

                # Increase the suspicious counter if above threshold; otherwise, decay it
                if np.max(np.abs(float_chunk)) > amplitude_threshold:
                    suspicious_duration += CHUNK_DURATION
                else:
                    suspicious_duration = max(suspicious_duration - CHUNK_DURATION, 0)

                # Check for speech using webrtcvad (expects raw PCM bytes)
                is_speech = vad.is_speech(chunk.tobytes(), sample_rate=FS)
                if is_speech:
                    print("Speech detected in audio chunk.")
                    payload = {
                        "Type": "sus_aud",
                        "Value": ["Suspicious activity (conversation)"],
                    }
                    try:
                        response = req.post(
                            url,
                            data=json.dumps(payload),
                            headers={"Content-Type": "application/json"},
                        )
                        print("Audio payload sent (speech), response:", response.text)
                    except Exception as e:
                        print("Error sending audio payload (speech):", e)
                    # Reset suspicious duration after sending payload
                    suspicious_duration = 0

                # Check if loud noise persisted over threshold duration
                if suspicious_duration >= suspicious_duration_threshold:
                    print("Loud noise detected over threshold duration.")
                    payload = {
                        "Type": "sus_aud",
                        "Value": ["Suspicious activity (loud noise)"],
                    }
                    try:
                        response = req.post(
                            url,
                            data=json.dumps(payload),
                            headers={"Content-Type": "application/json"},
                        )
                        print(
                            "Audio payload sent (loud noise), response:", response.text
                        )
                    except Exception as e:
                        print("Error sending audio payload (loud noise):", e)
                    suspicious_duration = 0

            except Exception as ex:
                print("Error in audio monitoring:", ex)
            # Small pause between iterations; adjust if needed
            time.sleep(0.1)

    # Launch the monitoring loop in a separate daemon thread.
    audio_thread = threading.Thread(target=audio_monitoring_loop, daemon=True)
    audio_thread.start()
