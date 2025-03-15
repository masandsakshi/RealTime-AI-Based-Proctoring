from flask import Flask, jsonify, request
import json
import requests

app = Flask(__name__)

# Plis Implement Data collection and queuing logic here



@app.route('/key_press', methods=['POST'])
def records():
    data_point = request.get_json()
    print(data_point)

    # data_point holds an individual key_press event and it's details
    # Use however u like :)

    return 'ok', 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)