from bson import ObjectId
from pymongo import MongoClient, DESCENDING
import boto3

import jwt
import hashlib
from flask import Flask, render_template, jsonify, request
from flask.json.provider import JSONProvider

from datetime import datetime
import json
import sys

app = Flask(__name__)
#client = MongoClient('mongodb://test:test@localhost',27017)
client = MongoClient('localhost', 27017)
ACCESS_KEY='AKIAUVLHFO3JAY6XVO2F'
S3SECRET_KEY='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'
SECRET_KEY = 'SPARTA'


s3_client = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=S3SECRET_KEY)

db=client.yourname

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):  # datetime 객체를 확인하고 ISO 형식의 문자열로 변환합니다.
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)

app.json = CustomJSONProvider(app)

@app.route('/')
def main():
    return render_template('index.html') 

@app.route('/login')
def login():
    return render_template('login.html') 

@app.route('/register')
def register():
    return render_template('register.html') 

@app.route('/api/register', methods=['POST'])
def api_register():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    nickname_receive = request.form['nickname_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    db.user.insert_one({'email': id_receive, 'password': pw_receive, 'nickname': nickname_receive})

    return jsonify({'result': 'success'})

@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    result = db.user.find_one({'email': id_receive, 'password': pw_hash})

@app.route('/api/vote', methods=['POST'])
def vote():
    state = request.form.get('state')
    email = request.form.get('email')
    message = request.form.get('message','')
    timestamp = datetime.utcnow()
    
    vote = {'state':state,'email':email,'message':message,'timestamp':timestamp}
    db.vote.insert_one(vote)
    return jsonify({'result':'success'})

@app.route('/api/votes', methods=['GET'])
def votes():
    print("요청")
    lastSet = db.set.find_one(sort=[('timestamp', DESCENDING)])
    print("lastSet",lastSet)
    lastTime = lastSet['timestamp']
    recent_votes = list(db.vote.find({'timestamp': {'$gte': lastTime}}))
    hot = [doc for doc in recent_votes if doc['state'] == 'hot']
    good = [doc for doc in recent_votes if doc['state'] == 'good']
    cold = [doc for doc in recent_votes if doc['state'] == 'cold']
    states = {'hot':len(hot),'good':len(good),'cold':len(cold)}
    max_state = max(states, key=lambda k: states[k])

    response_data = {
        'hot': hot,
        'good': good,
        'cold': cold,
        'most': max_state
    }
    result = {'result':'success'}
    result.update(response_data)
    print(result)
    return jsonify(result)

@app.route('/api/stateImages/', methods=['GET'])
def state_images():
    state = request.args.get('state','none')
    images = db.set.find({'state': state})
    image_urls = [doc.url for doc in images]
    result = {'result':'success'}
    return jsonify(result.update(image_urls))

@app.route('/api/uploadImage', methods=['POST'])
def upload_image():
    email=request.form['email']
    state=request.form['state']
    file = request.files['file']
    if file:
        # S3에 파일 업로드
        s3_client.upload_fileobj(file, 'krafton_yourname', file.filename)
        # S3 파일 URL 생성
        file_url = f"https://krafton_yourname.s3.amazonaws.com/{file.filename}"

        doc = {'email':email,'state':state,'image_url': file_url}
        db.image.insert_one(doc)
        
        return jsonify({'result': 'success'}), 200
    else:
        return jsonify({'result': 'fail', 'error': 'No file uploaded'}), 400

@app.route('/api/set', methods=['POST'])
def set_temperature():
    email=request.form['email']
    temperature = request.form['temperature']
    timestamp = datetime.utcnow()
    set = {'email':email,'temperature':temperature,'timestamp':timestamp}
    db.set.insert_one(set)
    result = {'result':'success'}
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)