from flask import Flask, jsonify, request
import json
import requests

app = Flask(__name__)

def init_log_file():
    with open('./activity.log','w'):
        pass

def log(typ,data):
    with open('./activity.log','a') as f:
        tmp =''
        for i in data:
            tmp +=( i +" ")
        f.writelines([f'{typ} {tmp}\n'])

init_log_file()





# Plis Implement Data collection and storing logic here






@app.route('/log', methods=['POST'])
def records():
    data_point = request.get_json()
    log(data_point['Type'],data_point['Value'])
    print('logged in file : )')
    return 'ok', 200


if __name__ == '__main__':
    app.run(debug=True, port=6000)