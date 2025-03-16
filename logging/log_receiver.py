from flask import Flask, jsonify, request
import json

app = Flask(__name__)


def init_log_file():
    with open("./activity.log", "w"):
        pass


def log(typ, data):
    with open("./activity.log", "a") as f:
        tmp = ""
        for i in data:
            tmp += str(i) + " "
        print(f"Logging event: {typ} {tmp}")  # Debug print
        f.writelines([f"{typ} {tmp}\n"])


init_log_file()


@app.route("/log", methods=["POST"])
def records():
    try:
        data_point = request.get_json()
        print(f"Received data: {data_point}")  # Debug print

        # Handle both wrapped and unwrapped payloads
        if "data" in data_point:
            # Wrapped payload (from audio/video)
            for event in data_point["data"]:
                log(event["Type"], event["Value"])
        else:
            # Direct payload (from focus events)
            log(data_point["Type"], data_point["Value"])

        print("Logged to file")
        return "ok", 200
    except Exception as e:
        print(f"Error processing event: {e}")
        return str(e), 500


if __name__ == "__main__":
    app.run(debug=True, port=6000)
