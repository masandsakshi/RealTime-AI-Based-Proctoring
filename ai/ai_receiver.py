from flask import Flask, jsonify, request
import json
import requests

app = Flask(__name__)

# Plis Implement Data collection and queuing logic here



@app.route('/dock', methods=['POST'])
def records():
    data_point = request.json.get("event")


if __name__ == '__main__':
    app.run(debug=True, port=5000)