from bson import ObjectId
from pymongo import MongoClient, DESCENDING
import boto3

from jwt.exceptions import ExpiredSignatureError
import hashlib
from flask import Flask, render_template, jsonify, request ,url_for, redirect, make_response
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
    token_receive = request.cookies.get('token')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"email": payload["email"]})
        if user_info is not None:
            nickname = user_info.get("nickname", "Guest")
        else:
            nickname = "Guest"
        return render_template('index.html', nickname=nickname)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/login')
def login():
    return render_template('login.html') 

@app.route('/register')
def register():
    return render_template('register.html') 

@app.route('/api/register', methods=['POST'])
def api_register():
    email = request.form['email']
    password = request.form['password']
    nickname = request.form['nickname']
    print(request.files)
    file = request.files['file']

    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    if file:
        #TODO:S3 서버 장애시 대응
        filename = f'profile{email}'
        file_url = getFileUrl(file,filename)

    db.user.insert_one({
        'email': email, 
        'password': password_hash, 
        'nickname': nickname, 
        'profile': file_url
    })

    return jsonify({'result': 'success'})

@app.route('/api/login', methods=['POST'])
def api_login():
    email_receive = request.form['email_give']
    password_receive = request.form['password_give']

    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    userDoc = db.user.find_one({'email': email_receive})
    if(not userDoc):
        return jsonify({'result': 'fail', 'msg': '아이디가 없습니다'})
    isLogin = password_hash == userDoc['password']
    if userDoc is not None and isLogin:
        # JWT 토큰에는, payload와 시크릿키가 필요합니다.
        # 시크릿키가 있어야 토큰을 디코딩(=풀기) 해서 payload 값을 볼 수 있습니다.
        # 아래에선 email와 exp를 담았습니다. 즉, JWT 토큰을 풀면 유저email 값을 알 수 있습니다.
        # exp에는 만료시간을 넣어줍니다(5초). 만료시간이 지나면, 시크릿키로 토큰을 풀 때 만료되었다고 에러가 납니다.
        payload = {
            'email': email_receive,
            'nickname':userDoc['nickname'],
            'profile':userDoc['profile'],
            'exp': datetime.utcnow() + timedelta(days=1)
                    }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        user = {
            'email':email_receive,
            'nickname':userDoc['nickname'],
            'profile':userDoc['profile'],
        }
        # token을 줍니다.
        response = {'result': 'success', 'token': token}
        response.update(user)
        return jsonify(response)
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/api/vote', methods=['POST'])
def vote():
    try:
        req= request.get_json()
        state = req['state']
        email = req['email']
        message = req['message']
        user = getUserByEmail(email)
        print(user)
        timestamp = datetime.utcnow()
        print("Vote", state)
        vote = {
            'state':state,
            'email':email,
            'nickname':user['nickname'],
            'profile':user['profile'],
            'message':message,
            'timestamp':timestamp,
        }
        result = db.vote.update_one({'email':email},{'$set': vote})
        if result.modified_count == 1:   #메모가 하나만 수정됐는지 확인
            return jsonify({'result': 'success'})
        elif result.modified_count == 0: #메모가 같은 값이면 0. 수정되지 않았는지 확인
            db.vote.insert_one(vote)
            return jsonify({'result' : 'no_change'})
        else:                               #메모 수정이 1개 이상이면 서버 오류
            return jsonify({'result': 'fail'})
    except Exception as e:
        print("실패", e)
        return jsonify({'result':'fail'})

@app.route('/api/votes', methods=['GET'])
def votes():
    data = {
        'hot':[],
        'good':[],
        'cold':[],
        'most':'none'
    }
    try:
        lastSet = db.set.find_one(sort=[('timestamp', DESCENDING)])
        lastTime = lastSet['timestamp']
        recent_votes = list(db.vote.find({'timestamp': {'$gte': lastTime}}))
        hot = [doc if 'img_url' in doc else {**doc, 'img_url': base_profile_url} for doc in recent_votes if doc['state'] == 'hot']
        good = [doc if 'img_url' in doc else {**doc, 'img_url': base_profile_url} for doc in recent_votes if doc['state'] == 'good']
        cold = [doc if 'img_url' in doc else {**doc, 'img_url': base_profile_url} for doc in recent_votes if doc['state'] == 'cold']
        states = {'hot':len(hot),'good':len(good),'cold':len(cold)}
        max_state = max(states, key=lambda k: states[k])
        print('hot',len(hot),"cold",len(cold),'good',len(good),max_state)
        if(len(hot)==len(cold)): 
            max_state = 'good'
            print(max_state)
        if(len(hot)==len(good) and len(cold)==len(good)): 
            max_state = 'good'
            if(len(hot)==0):
                max_state='none'
    except Exception as e:
        print("실패",e)
        return jsonify({'result':'fail'}), 400
    data = {
        'hot': hot,
        'good': good,
        'cold': cold,
        'most': max_state
    }
    result = {'result':'success'}
    result.update(data)
    return jsonify(result)

@app.route('/api/stateImages', methods=['GET'])
def state_images():
    image = {'img_url':base_state_url}
    try:
        state = request.args.get('state','none')
        print("state",state)
        pipeline = [
            {"$match": {"state": state}},
            {"$sample": {"size": 1}}
        ]
        image = list(db.image.aggregate(pipeline))
        print(image)
        image = image[0]
        print("image URL",image['img_url'])
    except Exception as e:
        print("실패",e)
        result = {'result':'fail'}
        result.update(image)
        return jsonify({'result':'fail','img_url':image['img_url']})
    result = {'result':'success'}
    result.update(image)
    return jsonify(result)

def getFileUrl(file,filename):
    try:
        # S3에 파일 업로드
        s3_client.upload_fileobj(file, 'krafton-yourname', filename)
    except Exception as e:
        print('이미지 서버 이상',e)
        return jsonify({'result':'fail','message':'이미지 서버가 좋지 않습니다.'}), 400
    # S3 파일 URL 생성
    file_url = f"{bucket_url}/{filename}"
    return file_url

@app.route('/api/uploadImage', methods=['POST'])
def upload_image():
    email = request.form['email']
    user = getUserByEmail(email)
    nickname = user['nickname']
    state = request.form['state']
    file = request.files['file']
    category = request.form.get('category','state')
    print(category)
    timestamp = get_js_timestamp()
    if file:
        #TODO:S3 서버 장애시 대응
        filename = category+'/'+state+str(timestamp)
        file_url = getFileUrl(file,filename)

        doc = {
            'email':email,
            'nickname':nickname,
            'state':state,
            'img_url': file_url
        }
        db.image.insert_one(doc)   
    else:
        return jsonify({'result': 'fail', 'message': '파일 업로드를 안했습니다.'}), 400
    return jsonify({'result': 'success'}), 200

@app.route('/api/set', methods=['POST'])
def set_temperature():
    req= request.get_json()
    email=req['email']
    temperature = req['temperature']
    timestamp = datetime.utcnow()
    user = {
        'email':email,
        'temperature':temperature,
        'nickname':'이름없음',
        'profile':base_profile_url,
        'timestamp':timestamp
    }
    print(email)
    try:
        userDoc = getUserByEmail(email)
        print(userDoc)
        user.update({
            'nickname':userDoc['nickname'],
            'profile':userDoc['profile'],
        })
    except Exception as e:
        print("실패", e)
        return jsonify({'result':'fail'})
    db.set.insert_one(user)
    print("세트 완료")
    result = {'result':'success'}
    return jsonify(result)

def get_js_timestamp():

    now = datetime.utcnow()
    unix_timestamp = now.timestamp()
    js_timestamp = int(unix_timestamp * 1000)
    return js_timestamp

def getUserByEmail(email):
    user = {
        'nickname':'이름없음',
        'profile': base_profile_url
    }
    try:
        userDoc = db.user.find_one({'email':email})
        nickname = userDoc['nickname']
        profile = userDoc['profile']
        user = {
            'nickname':nickname,
            'profile':profile
        }
    except Exception as e:
        print("해당 email 없음",e)
    return user

if __name__ == '__main__':
    app.run(port=5000,debug=True)