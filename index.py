from logging import debug
import os
from os import stat
from flask import Flask,request,redirect
from flask.globals import session
from flask.json import jsonify
from flask.wrappers import Response
from flask_cors import CORS,cross_origin
import datetime
from pytz import timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, DateTime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash,check_password_hash
from flask_marshmallow import Marshmallow
import smtplib
from random import randint
from flask_socketio import SocketIO, disconnect, emit,send


app = Flask(__name__)

CORS(app)
ENV='dev'
if ENV=='dev':
    app.debug=True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost/crudpython'
else:
    app.debug=False
    app.config['SQLALCHEMY_DATABASE_URI'] = ''

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db=SQLAlchemy(app)
ma=Marshmallow(app)
socketio=SocketIO(app,cors_allowed_origins="*")

class Data(db.Model):
    __tablename__='data'
    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    nim=db.Column(db.String(255))
    nama=db.Column(db.String(255))
    email=db.Column(db.String(255))
    foto=db.Column(db.String(255))
    password=db.Column(db.String(255))
    role=db.Column(db.String(255))
    verify_token=db.Column(db.String(255))
    created_at=db.Column(db.DateTime, default=datetime.datetime.now(timezone('UTC')).astimezone(timezone('Asia/Jakarta')))
    Updated_at=db.Column(db.DateTime, default=datetime.datetime.now(timezone('UTC')).astimezone(timezone('Asia/Jakarta')))

    def __init__(self,nim,nama,email,foto,password,role,verify_token):
        self.nim=nim
        self.nama=nama
        self.email=email
        self.foto=foto
        self.password=password
        self.role=role
        self.verify_token=verify_token

class DataSchema(ma.Schema):
    class Meta:
        fields=('id','nim','nama','email','foto','password','role','verify_token')

data_schema=DataSchema()
datas_schema=DataSchema(many=True)

def random_str(n):
    ranges=10**(n-1)
    rangee=(10**n)-1
    return randint(ranges,rangee)

def SendEmail(emailto,token):
    server=smtplib.SMTP_SSL('smtp.googlemail.com',465)
    server.login('gunawanindustri2020@gmail.com','fcgdxryhauoxlgag')
    subject='Verification Your Email For Data UKSW'
    # body=open('verify.php').read()
    body=f'kode verification kamu adalah {token}'
    msg=f'Subject: {subject}\n{body}'
    return server.sendmail('gunawanindustri2020@gmail.com',emailto,msg)

@app.route('/Sendemail', methods=['GET'])
@cross_origin(origin='*')
def verification_token():
    email=request.args['email']
    data=Data.query.filter(Data.email==email).one()
    token=random_str(6)
    data.verify_token=token
    SendEmail(email,token)
    db.session.commit()
    return 'sended'

@app.route('/VerifyPost', methods=['POST'])
@cross_origin(origin='*')
def check_token():
    t1=request.form['t1']
    t2=request.form['t2']
    t3=request.form['t3']
    t4=request.form['t4']
    t5=request.form['t5']
    t6=request.form['t6']
    token=f'{t1}{t2}{t3}{t4}{t5}{t6}'
    email=request.form['email']
    data=Data.query.filter(Data.email==email).one()
    if data.verify_token==token:
        data.verify_token='konfirmasi'
        db.session.commit()
        return jsonify(response='sukses'),200
    else:
        return jsonify(response='salah'),200

@app.route('/LoginPost', methods=['POST'])
@cross_origin(origin='*')

def LoginPost():
    newemail=request.form['email']
    newpassword=request.form['password']
    data=Data.query.filter(Data.email==newemail).one()
    if data!='':
        if check_password_hash(data.password,newpassword):
            return data_schema.jsonify(data),200
        else:
            return jsonify(response='Akun atau Password Salah'),200

@app.route('/Post', methods=['POST'])
@cross_origin(origin='*')

def PostData():
    newnim=request.form['nim']
    newnama=request.form['nama']
    newemail=request.form['email']
    newfoto=request.files['foto']
    newpassword=generate_password_hash('mahasiswa')
    newrole='mahasiswa'
    newtoken='kosong'

    app.config['UPLOAD_FILES']='D:\koding\python\crud\latihan\public\img'
    filename_edit=newfoto.filename
    filename=secure_filename(filename_edit.replace(' ',''))
    newfoto.save(os.path.join(app.config['UPLOAD_FILES'],filename))

    data=Data(
        nim=newnim,
        nama=newnama,
        email=newemail,
        foto=filename_edit.replace(' ',''),
        password=newpassword,
        role=newrole,
        verify_token=newtoken
        )
    db.session.add(data)
    db.session.commit()
    return data_schema.jsonify(data)

@app.route('/Load', methods=['GET'])
@cross_origin(origin='*')
def LoadData():
    dataall=Data.query.filter(Data.role=='mahasiswa').order_by(desc(Data.id)).all()
    result=datas_schema.dump(dataall)
    return jsonify(result)

@app.route('/Edit', methods=['GET'])
@cross_origin(origin='*')
def EditData():
    newid=request.args['id']
    dataedit=Data.query.get(newid)
    return data_schema.jsonify(dataedit)

@app.route('/Update', methods=['POST'])
@cross_origin(origin='*')
def UpdateData():
    newfoto=request.files['editfoto'].filename.replace(' ','')
    newid=request.form['editid']
    dataedit=Data.query.get(newid)
    dataedit.nim=request.form['editnim']
    dataedit.nama=request.form['editnama']
    dataedit.email=request.form['editemail']
    dataedit.foto=newfoto

    app.config['UPLOAD_FILES']='D:\koding\python\crud\latihan\public\img'
    filename=secure_filename(newfoto)
    request.files['editfoto'].save(os.path.join(app.config['UPLOAD_FILES'],filename))
    db.session.commit()
    return data_schema.jsonify(dataedit)

@app.route('/Delete', methods=['GET'])
@cross_origin(origin='*')
def DeleteData():
    newid=request.args['id']
    datadelete=Data.query.get(newid)
    db.session.delete(datadelete)
    db.session.commit()
    return data_schema.jsonify(datadelete)

@app.route('/Search', methods=['GET'])
@cross_origin(origin='*')
def Search():
    newsearch=request.args['search']
    search = "%{}%".format(newsearch)
    data = Data.query.filter(Data.nama.like(search)).filter(Data.role=='mahasiswa').order_by(desc(Data.id)).all()
    result=datas_schema.dump(data)
    return jsonify(result)

@socketio.on('message')
def connect(data):
    send(data,broadcast=True)
    return 'oke'

if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    socketio.run(app,debug=True)