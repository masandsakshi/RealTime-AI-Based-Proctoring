import time
import numpy as np
import sounddevice as sd
import requests
import threading
from queue import Queue
import json


def start_audio_monitoring(url="http://localhost:8080/publish"):
    event_queue = Queue()

    def audio_monitoring_loop():
        # Audio configuration
        FS = 16000
        CHANNELS = 1
        CHUNK_DURATION = 0.03
        CHUNK_SIZE = int(FS * CHUNK_DURATION)
        LOUD_THRESHOLD = 900

        try:
            stream = sd.InputStream(
                samplerate=FS,
                channels=CHANNELS,
                dtype=np.int16,
                blocksize=CHUNK_SIZE,
                latency="low",
            )

            with stream:
                while True:
                    try:
                        audio_chunk, overflowed = stream.read(CHUNK_SIZE)
                        if overflowed:
                            continue

                        amplitude = np.abs(audio_chunk).mean()

                        if amplitude > LOUD_THRESHOLD:
                            timestamp = time.time()
                            # Use the standard format directly
                            event_queue.put(
                                {
                                    "Type": "sus_aud",
                                    "Value": [
                                        f"LOUD noise detected!",
                                        f"{timestamp:.3f}",
                                    ],
                                }
                            )
                            print(
                                f"Detected loud noise: {amplitude:.2f} at {timestamp:.3f}"
                            )

                        time.sleep(0.01)

                    except Exception as e:
                        time.sleep(0.1)

        except Exception as e:
            pass

    def event_sender():
        while True:
            try:
                if not event_queue.empty():
                    event = event_queue.get()
                    try:
                        # Wrap the event in a data array as expected by main.go
                        payload = {"data": [event]}
                        json_payload = json.dumps(payload)
                        print(f"Sending audio event: {json_payload}")

                        response = requests.post(
                            url,
                            data=json_payload,
                            headers={"Content-Type": "application/json"},
                            timeout=1,
                        )
                        print(f"Audio event sent, status: {response.status_code}")
                    except requests.exceptions.RequestException as e:
                        print(f"Failed to send audio event: {e}")
                time.sleep(0.1)
            except Exception as e:
                print(f"Error in event_sender: {e}")
                time.sleep(0.1)

    # Start threads
    threading.Thread(target=audio_monitoring_loop, daemon=True).start()
    threading.Thread(target=event_sender, daemon=True).start()
