from bson import ObjectId
from pymongo import MongoClient, DESCENDING
import boto3

from jwt.exceptions import ExpiredSignatureError
import hashlib
from flask import Flask, render_template, jsonify, request,url_for, redirect
from flask.json.provider import JSONProvider

from datetime import datetime, timedelta
import json
import sys

import jwt
import hashlib

app = Flask(__name__)
client = MongoClient('mongodb://test:test@3.35.3.55',27017)
# client = MongoClient('localhost', 27017)
ACCESS_KEY='AKIAUVLHFO3JAY6XVO2F'
S3SECRET_KEY='xGd36QoMpQqi+6WNxtQ48PM1uv6q8OhAkLcIuUNm'
SECRET_KEY = 'SPARTA'

bucket_name = 'krafton-yourname'
bucket_url= f'https://{bucket_name}.s3.amazonaws.com'
base_profile_url = f'{bucket_url}/baseprofile.png'
base_state_url = f'{bucket_url}/basestate.png'

s3_client = boto3.client(
    's3', 
    aws_access_key_id=ACCESS_KEY, 
    aws_secret_access_key=S3SECRET_KEY
)

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
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"email": payload["id"]})
        return render_template('index.html', nickname=user_info["nickname"])
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/login')
def login():
    return render_template('login.html') 

if __name__ == '__main__':
    app.run(port=5001,debug=True)