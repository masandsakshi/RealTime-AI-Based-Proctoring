import time
import numpy as np
import sounddevice as sd
import requests
import threading
from queue import Queue


def start_audio_monitoring(url="http://localhost:8080/publish"):
    event_queue = Queue()

    def audio_monitoring_loop():
        # Audio configuration
        FS = 16000
        CHANNELS = 1
        CHUNK_DURATION = 0.03
        CHUNK_SIZE = int(FS * CHUNK_DURATION)
        LOUD_THRESHOLD = 900  # Threshold for loud noise detection

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
                            event_queue.put(
                                {
                                    "Type": "sus_aud",
                                    "Value": [
                                        "LOUD noise detected!",
                                        f"{timestamp:.3f}",
                                    ],
                                    "Level": "critical",
                                }
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
                        response = requests.post(
                            url,
                            json={"data": [event]},
                            headers={"Content-Type": "application/json"},
                            timeout=1,
                        )
                    except requests.exceptions.RequestException:
                        pass
                time.sleep(0.1)
            except Exception:
                time.sleep(0.1)

    # Start threads
    threading.Thread(target=audio_monitoring_loop, daemon=True).start()
    threading.Thread(target=event_sender, daemon=True).start()
