from flask import Flask, jsonify, request
import json
import requests

app = Flask(__name__)


c = 0

# endpoint to test connection
@app.route('/ping', methods=['GET'])
def ping():
    global c
    c += 1
    print(c)
    return jsonify({"message": "Pinged Distributor API!"})


@app.route('/event',methods=['POST'])
def event():
    event = request.json.get("event")
    etyp = event["type"]
    eVal = event["value"]
    print(etyp,eVal)

    return jsonify({"message":"event recorded"}), 200





# Send to another service







@app.route('/trigger', methods=['POST'])
def trigger_server():
    target_url = request.json.get("url")
    print(target_url)
    if not target_url:
        return jsonify({"error": "No URL provided"}), 400
    try:
        response = requests.get(target_url, json={"triggered": True})
        return jsonify({"status": "Triggered", "response": response.json()}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
