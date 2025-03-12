from flask import Flask, jsonify, request
import json
import requests

app = Flask(__name__)

def init_log_file():
    with open('./activity.log','w'):
        pass

def log(typ,data):
    with open('./activity.log','a') as f:
        f.writelines([f'{typ} | {data}\n'])

init_log_file()
for i in range(20):
    log('key_down',['a',120325,10])




# Plis Implement Data collection and storing logic here






@app.route('/', methods=['POST'])
def records():
    data_point = request.json.get("event")


if __name__ == '__main__':
    app.run(debug=True, port=5000)