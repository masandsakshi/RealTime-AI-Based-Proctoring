import time
import numpy as np
import sounddevice as sd
import webrtcvad
import requests
import json
import threading
from queue import Queue


def start_audio_monitoring(url="http://localhost:8080/publish"):
    # Create event queue for thread-safe communication
    event_queue = Queue()

    def audio_monitoring_loop():
        # Audio configuration
        FS = 16000  # Sampling rate must be 16000, 32000, or 48000 for WebRTC VAD
        CHANNELS = 1
        CHUNK_DURATION = 0.03  # 30ms chunks for WebRTC VAD
        CHUNK_SIZE = int(FS * CHUNK_DURATION)

        # Initialize VAD
        vad = webrtcvad.Vad(3)  # Aggressiveness level 3 (most aggressive)

        try:
            # Configure audio stream
            stream = sd.InputStream(
                samplerate=FS,
                channels=CHANNELS,
                dtype=np.int16,
                blocksize=CHUNK_SIZE,
                latency="low",
            )

            with stream:
                print("Audio monitoring started")
                while True:
                    try:
                        # Read audio chunk
                        audio_chunk, overflowed = stream.read(CHUNK_SIZE)
                        if overflowed:
                            print("Audio buffer overflow")
                            continue

                        # Convert to the format needed by WebRTC VAD
                        audio_chunk = audio_chunk.reshape(-1)  # Flatten array
                        audio_bytes = audio_chunk.tobytes()

                        # Check for speech
                        try:
                            is_speech = vad.is_speech(audio_bytes, FS)
                            if is_speech:
                                timestamp = time.time()
                                event_queue.put(
                                    {
                                        "Type": "sus_aud",
                                        "Value": [
                                            "Speech detected",
                                            f"{timestamp:.3f}",
                                        ],
                                    }
                                )
                        except Exception as e:
                            print(f"VAD error: {e}")
                            continue

                        # Check amplitude
                        amplitude = np.abs(audio_chunk).mean()
                        if amplitude > 1000:  # Adjust threshold as needed
                            timestamp = time.time()
                            event_queue.put(
                                {
                                    "Type": "sus_aud",
                                    "Value": [
                                        "Loud noise detected",
                                        f"{timestamp:.3f}",
                                    ],
                                }
                            )

                        time.sleep(0.01)  # Small delay to prevent CPU overuse

                    except Exception as e:
                        print(f"Error processing audio chunk: {e}")
                        time.sleep(0.1)  # Add delay on error

        except Exception as e:
            print(f"Error initializing audio stream: {e}")
            return

    def event_sender():
        while True:
            try:
                # Get event from queue
                if not event_queue.empty():
                    event = event_queue.get()
                    try:
                        response = requests.post(
                            url,
                            json={"data": [event]},
                            headers={"Content-Type": "application/json"},
                            timeout=1,
                        )
                        if response.status_code != 200:
                            print(f"Error sending event: {response.status_code}")
                    except requests.exceptions.RequestException as e:
                        print(f"Network error: {e}")
                time.sleep(0.1)  # Prevent tight loop
            except Exception as e:
                print(f"Event sender error: {e}")
                time.sleep(0.1)

    # Start monitoring thread
    audio_thread = threading.Thread(target=audio_monitoring_loop, daemon=True)
    audio_thread.start()

    # Start event sender thread
    sender_thread = threading.Thread(target=event_sender, daemon=True)
    sender_thread.start()
