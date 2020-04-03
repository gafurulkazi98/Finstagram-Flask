# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 16:33:11 2020

@author: Rafi
"""

from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
SALT = '7h1515my54l7d0n7judg3m30k'

app = Flask(__name__)

conn = pymysql.connect(host='localhost',
                       port = 3308,
                       user='root',
                       password='',
                       db='Finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

@app.route('/')
def login():
    try:
        username = session['username']
        return redirect(url_for('home'))
    except:
        return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    username = request.form['username']
    password = request.form['password'] + SALT
    hashword = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    cursor = conn.cursor()
    query = 'SELECT * FROM person WHERE username = %s and password = %s'
    cursor.execute(query, (username, hashword))
    data = cursor.fetchone()
    cursor.close()
    if(data):
        session['username'] = username
        return redirect(url_for('home'))
    else:
        return render_template('login.html', error='Invalid login or username')

@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    username = request.form['username']
    password = request.form['password'] + SALT
    vpassword = request.form['vpassword'] + SALT
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    email = request.form['email']
    
    cursor = conn.cursor()
    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchone()
    if(data):
        return render_template('register.html', error = "This username is taken")
    else:
        if password!=vpassword:
            return render_template('register.html', error = "Passwords do not match")
        hashword = hashlib.sha256(password.encode('utf-8')).hexdigest()
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, hashword, firstName, lastName, email))
        conn.commit()
        cursor.close()
        session['username']=username
        return redirect(url_for('home'))
    
@app.route('/home')
def home():
    try:
        username=session['username']
    except:
        return redirect('/')
    cursor = conn.cursor();
    query = 'SELECT pID,filepath FROM follow JOIN photo ON followeeUsername = posterUsername WHERE followerUsername = %s UNION SELECT pID,filepath FROM photo NATURAL JOIN share NATURAL JOIN friendGroup NATURAL JOIN groupmember WHERE memberUsername = %s'
    cursor.execute(query, (username,username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html',user=username,feed=data)

@app.route('/newPost')
def newPost():
    try:
        username=session['username']
    except:
        return redirect('/')
    cursor=conn.cursor()
    query = 'SELECT groupName,creatorUsername FROM groupMember WHERE memberUsername = %s'
    cursor.execute(query,(username))
    data=cursor.fetchall()
    cursor.close()
    return render_template('newPost.html',user=username,friendGroups=data)

@app.route('/submitPost', methods=['GET','POST'])
def submitPost():
    try:
        username=session['username']
    except:
        return redirect('/')
    filepath = request.files['filepath']
    photoData = filepath.read()
    #return render_template("debug.html",filepath=filepath,photoData=photoData)
    caption = request.form['caption']
    shareWith = request.form['shareWith']
    
    cursor=conn.cursor()
    
    ins = 'INSERT INTO photo VALUES(NULL,%s, CURRENT_TIMESTAMP, %s, %s, %s)'
    cursor.execute(ins,(username,photoData,shareWith == "allFollowers",caption))
    conn.commit()
    
    if not shareWith == "allFollowers":
        query = 'SELECT LAST_INSERT_ID();'
        cursor.execute(query)
        data = cursor.fetchone()
        pID = data['LAST_INSERT_ID()']
        shareWith_vals=shareWith.split(',')
        groupName = shareWith_vals[0]
        creatorUsername = shareWith_vals[1]
        ins = 'INSERT INTO share VALUE(%s,%s,%s)'
        cursor.execute(ins,(pID,groupName,creatorUsername))
        conn.commit()
    cursor.close()
    return render_template('home.html',user=username)

@app.route('/friendGroups')
def friendGroup():
    try:
        username=session['username']
    except:
        return redirect('/')
    cursor = conn.cursor()
    query = 'SELECT * FROM groupMember NATURAL JOIN friendGroup WHERE memberUsername = %s'
    cursor.execute(query,(username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('friendGroups.html',user=username,friendGroups=data)

@app.route('/newFriendGroup')
def newFriendGroup():
    try:
        username=session['username']
    except:
        return redirect('/')
    return render_template('newFriendGroup.html',user=username)

@app.route('/authFriendGroup', methods = ['GET', 'POST'])
def authFriendGroup():
    try:
        username=session['username']
    except:
        return redirect('/')
    newGroupName = request.form['newGroupName']
    description = request.form['description']
    cursor = conn.cursor()
    query = 'SELECT groupName,creatorUsername FROM friendGroup WHERE groupName = %s AND creatorUsername = %s'
    cursor.execute(query,(newGroupName,username))
    data = cursor.fetchone()
    error = None
    if(data):
        cursor.close()
        error = 'You already own a friend group with this name'
        return render_template("newFriendGroup.html",user=username, error=error)
    else:
        ins = 'INSERT INTO friendGroup VALUES(%s, %s, %s)'
        cursor.execute(ins, (newGroupName,username,description))
        conn.commit()
        ins = 'INSERT INTO groupMember VALUES(%s, %s, %s)'
        cursor.execute(ins, (newGroupName,username,username))
        conn.commit()
        cursor.close()
        return redirect("friendGroups")
    
@app.route('/follows')
def follows():
    try:
        username=session['username']
    except:
        return redirect('/')
    cursor = conn.cursor()  
    query = 'SELECT followerUsername,first_name,last_name FROM follow JOIN person ON followerUsername = username WHERE followeeUsername = %s AND followStatus = 0'
    #Ask if it's possible to join this table with PERSON so that I can get the names of the followers
    cursor.execute(query,(username))
    pFollows = cursor.fetchall()
    cursor.close()
    return render_template("follows.html",user=username,pendingFollows=pFollows)

@app.route('/newFollowee', methods = ['GET','POST'])
def newFollowee():
    try:
        username=session['username']
    except:
        return redirect('/')
    cursor = conn.cursor()
    followeeUsername = request.form['newFollowee']
    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query,(followeeUsername))
    data = cursor.fetchone()
    if followeeUsername == username:
        error = "Invalid username"
        cursor.close()
        return render_template("follows.html",user=username,error=error)
    if(data):
        ins = 'INSERT INTO follow VALUES(%s,%s,0)'
        cursor.execute(ins,(username,followeeUsername))
        conn.commit()
        cursor.close()
        return render_template("follows.html",user=username,notification=1)
    else:
        error = "Username not found"
        cursor.close()
        return render_template("follows.html",user=username,error=error)

@app.route('/setFollows', methods = ['GET', 'POST'])
def setFollows():
    try:
        username=session['username']
    except:
        return redirect('/')
    cursor = conn.cursor()
    #query = 'SELECT followerUsername FROM follow JOIN person ON followeeUsername = username WHERE followeeUsername = %s AND followStatus = 0'
    #cursor.execute(query,(username))
    #followList = cursor.fetchall()
    #return render_template("debug.html",followList=followList)
    #for f in followList:
    action_vals = request.form['action']
    action_split = action_vals.split(',')
    followerUsername = action_split[0]
    action = int(action_split[1])
    if(action):
        stmt = 'UPDATE follow SET followStatus = 1 WHERE followerUsername = %s AND followeeUsername = %s'
    else:
        stmt = 'DELETE FROM follow WHERE followerUsername = %s AND followeeUsername = %s'
    cursor.execute(stmt,(followerUsername,username))
    conn.commit()
    return redirect("follows")
    
@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

app.secret_key = '4pp 53cr37 k3y'
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)