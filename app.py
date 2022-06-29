from flask import Flask, send_file, request, redirect, session, url_for, render_template, g
from database import get_db
import sqlite3
from sqlite3 import Error
from datetime import datetime
import json
import http.client
import hashlib
import os
import sys
from flask_recaptcha import ReCaptcha
import cred
# the line below is required in production.
sys.path.insert(0, '/home/fairacresltd/sms')

'''
TODO: 
25JUN2022: 
add comments to the file - this is getting loosy-goosy. Also made a lot of changes to git updating.
git key is now different - check ~/.ssh/id_abcdef
'''

app = Flask(__name__)

app.secret_key = os.urandom(24)
app.config['RECAPTCHA_SITE_KEY'] = cred.recaptcha_site_key
app.config['RECAPTCHA_SECRET_KEY'] = cred.recaptcha_secret_key


recaptcha = ReCaptcha(app)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def hashpass(pwd):
    return hashlib.md5(pwd.encode()).hexdigest()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if recaptcha.verify():
            conn = get_db()
            cur = conn.cursor()
            sql = 'select id, username, email, admin from users where email = ? and password = ?'
            email = request.form['txtEmail']
            pwd = hashpass(request.form['txtPass'])
            cur.execute(sql, [email, pwd])
            result = cur.fetchone()
            if result == None:
                return render_template('login.html', msg='Invalid User')
            session['uid'] = result['id']
            session['user'] = result['username']
            session['email'] = result['email']
            session['admin'] = result['admin']
            return redirect(url_for('home'))
        else:
            return render_template('login.html', msg='Please click verification checkbox')


    return render_template('login.html', msg='')


@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user')
    if 'email' in session:
        session.pop('email')
    if 'admin' in session:
        session.pop('admin')
    if 'uid' in session:
        session.pop('uid')


    return redirect(url_for('login'))


def sendMessage(users, msg):
    if 'user' not in session:
        return render_template('login.html', msg='')


    userlist = ''
    sep = ''
    conn = get_db()
    cur = conn.cursor()
    sql = 'select phone from recipients where name = ?'
    for item in users:
        cur.execute(sql,[item])
        result = cur.fetchone()
        userlist += sep + result['phone']
        sep = ','


    jsondata = {
        "SenderId": "FAIR_ACRES",
        "Is_Unicode": False,
        "Is_Flash": False,
        "SchedTime": "",
        "GroupId": "",
        "ServiceId": "",
        "CoRelator": "",
        "LinkId": "",
        "MobileNumbers": userlist,
        "Message": msg,
        "ApiKey": cred.uwazii_api_key,
        "ClientId": cred.uwazii_client_id
    }


    jsondata = json.dumps(jsondata)


    headers = {
        "content-type": "application/json",
        "cache-control": "no-cache"
    }


    httpconn = http.client.HTTPSConnection("api.uwaziimobile.com")
    httpconn.request("POST", "/api/v2/SendSMS", body=jsondata, headers=headers)
    res = httpconn.getresponse()
    data = res.read()
    httpconn.close()
    dataresult = data.decode("utf-8")


    # log in message.db
    now = datetime.now()
    dnow = now.strftime('%Y-%m-%d')
    tnow = now.strftime('%H:%M:%S')
    conn = get_db()
    cur = conn.cursor()
    sql = 'insert into message (mdate, mtime, who, message, result) values (?, ?, ?, ?, ?)'
    cur.execute(sql,[dnow, tnow, userlist, msg, dataresult])
    conn.commit()


    return "Message Sent to: "+userlist


@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        # return render_template('login.html', msg='')
        return redirect(url_for('login'), code=307)


    user = session['user']
    admin = session['admin']


    msg = ""
    if request.method == 'POST':
        msg = "Form Posted"
        userlist = request.form.getlist('outList')
        message = request.form['txtMessage']
        # if the message is longer than 160 chars, we can chop it up here and send it in
        # pieces at 160 length each.
        msg = sendMessage(userlist, message)


    conn = get_db()
    sql = 'select id, name, phone, firstname, lastname, email from recipients'
    cur = conn.cursor()
    cur.execute(sql)
    results = cur.fetchall()
    sql = 'select id, firstname, lastname, email, phone, house, homeowner from contacts'
    cur.execute(sql)
    contacts = cur.fetchall()
    return render_template('index.html', users=results, msg=msg, contacts=contacts)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if 'user' not in session:
        return redirect(url_for('login'))


    user = session['user']
    admin = session['admin']


    conn = get_db()
    cur = conn.cursor()


    if request.method == 'POST':
        lastname = request.form['txtLast']
        firstname = request.form['txtFirst']
        phone = request.form['txtPhone']
        email = request.form['txtEmail']


        sql = 'select * from contacts where email = ?'
        cur.execute(sql, [email])
        result = cur.fetchone()
        if result is None:
            sql = 'insert into contacts (firstname, lastname, phone, email) values (?, ?, ?, ?)'
            cur.execute(sql, [firstname, lastname, phone, email])
            conn.commit()


    sql = 'select id, firstname, lastname, phone, email, house from contacts'
    cur.execute(sql)
    contacts = cur.fetchall()
    return render_template('contact.html', contacts=contacts)


@app.route('/edit/<econt>', methods=['GET', 'POST'])
def edit(econt):
    if 'user' not in session:
        return redirect(url_for('contact'))


    if request.method == 'POST':
        lastname = request.form['txtLast']
        firstname = request.form['txtFirst']
        phone = request.form['txtPhone']
        house = request.form['txtHouse']
        howner = request.form['txtOwner']
        if howner == 'Y':
            homeowner = 1
        else:
            homeowner = 0
        sql = 'update contacts set lastname = ?, firstname = ?, house = ?, homeowner = ?, phone = ? where email = ?'
        conn = get_db()
        cur = conn.cursor()
        cur.execute(sql, [lastname, firstname, house, homeowner, phone, econt])
        conn.commit()
        return redirect(url_for('contact'))


    user = session['user']
    admin = session['admin']


    conn = get_db()
    cur = conn.cursor()
    sql = 'select id, firstname, lastname, email, phone, house, homeowner from contacts where email=?'
    cur.execute(sql, [econt])
    contact = cur.fetchone()
    return render_template('edit.html', contact=contact)


@app.route('/delete/<econt>', methods=['GET', 'POST'])
def delcontact(econt):
    if 'user' not in session:
        return redirect(url_for('login'))


    if request.method == 'POST':
        sql = 'delete from contacts where email = ?'
        conn = get_db()
        cur = conn.cursor()
        cur.execute(sql, [econt])
        conn.commit()
        return redirect(url_for('contact'))


    user = session['user']
    admin = session['admin']


    conn = get_db()
    cur = conn.cursor()
    sql = 'select id, firstname, lastname, email, phone, house, homeowner from contacts where email=?'
    cur.execute(sql, [econt])
    contact = cur.fetchone()
    return render_template('delete.html', contact=contact)


@app.route('/staff', methods=['GET', 'POST'])
def staff():
    if 'user' not in session:
        return redirect(url_for('login'))


    user = session['user']
    admin = session['admin']


    if admin != 1:
        return redirect(request.referrer)


    conn = get_db()
    cur = conn.cursor()
    msg = ''


    if request.method == 'POST':
        lastname = request.form['txtLast']
        firstname = request.form['txtFirst']
        username = request.form['txtUser']
        email = request.form['txtEmail']
        admin = 0


        sql = 'select username from users where username = ?'
        cur.execute(sql,[username])
        result = cur.fetchone()
        if result is None:
            sql = 'insert into users (username, firstname, lastname, email, password, admin) '
            sql += 'values (?, ?, ?, ?, ?, ?)'
            cur.execute(sql, [username, firstname, lastname, email, hashpass(username), admin])
            conn.commit()
            return redirect(url_for('staff'))
        else:
            msg = 'User not added. User {} exists'.format(username)


    sql = 'select id, username, firstname, lastname, email, admin from users'
    cur.execute(sql)
    result = cur.fetchall()
    return render_template('staff.html', contacts=result, msg=msg)


@app.route('/edituser/<uid>', methods=['GET', 'POST'])
def edituser(uid):
    if 'user' not in session:
        return redirect(url_for('login'))


    if 'admin' not in session:
        return redirect(request.referrer)


    if request.method == 'POST':
        firstname = request.form['txtFirst']
        lastname = request.form['txtLast']
        email = request.form['txtEmail']
        admin = request.form['txtAdmin']
        password = request.form['txtPassword']
        if len(password) == 0:
            sql = 'update users set firstname = ?, lastname = ?, email = ?, admin = ? where id = ?'
            params = [firstname, lastname, email, admin, uid]
        else:
            sql = 'update users set firstname = ?, lastname = ?, email = ?, admin = ?, password = ? where id = ?'
            params = [firstname, lastname, email, admin, hashpass(password), uid]


        db = get_db()
        cur = db.cursor()
        cur.execute(sql, params)
        db.commit()
        return redirect(url_for('staff'))


    db = get_db()
    cur = db.cursor()
    sql = 'select id, username, firstname, lastname, email, admin from users where id = ?'
    cur.execute(sql, [uid])
    result = cur.fetchone()
    return render_template('edituser.html', contact=result)


@app.route('/deluser/<uid>')
def deluser(uid):
    if 'user' not in session:
        return redirect(url_for('login'))
    if 'admin' not in session:
        return redirect(request.referrer)


    # don't delete logged in user.
    if int(uid) != int(session['uid']):
        sql = 'delete from users where id = ?'
        db = get_db()
        cur = db.cursor()
        cur.execute(sql,[uid])
        db.commit()


    return redirect(url_for('staff'))


@app.route('/showlogs')
def showlogs():
    if 'user' not in session:
        return redirect(url_for('login'))


    user = session['user']
    admin = int(session['admin'])


    if admin != 1:
        return redirect(url_for('home'))


    conn = get_db()
    cur = conn.cursor()
    sql = 'select id, mdate, mtime, who, message, result from message order by id desc limit 20'
    cur.execute(sql)
    data = cur.fetchall()


    return render_template('showlogs.html', messages=data)


if __name__ == '__main__':
    app.run(debug=True)
