# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 16:33:11 2020

@author: Rafi
"""

from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors

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
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    username = request.form['username']
    password = request.form['password']
    
    cursor = conn.cursor()
    query = 'SELECT * FROM person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
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
    password = request.form['password']
    vpassword = request.form['vpassword']
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
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, password, firstName, lastName, email))
        conn.commit()
        cursor.close()
        session['username']=username
        return render_template('home.html',user=username)
    
@app.route('/home')
def home():
    try:
        username=session['username']
    except:
        return redirect('/')
    #cursor = conn.cursor();
    #query = 'SELECT filename FROM follow NATURAL JOIN photo WHERE followerUsername = %s ORDER BY postingDate DESC'
    #cursor.execute(query, (username))
    #data = cursor.fetchall()
    #cursor.close()
    return render_template('home.html',user=username)#,feed=data)

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
    filepath = request.form['filepath']
    #How to use BLOB datatype
    caption = request.form['caption']
    shareWith = request.form['shareWith']
    cursor=conn.cursor()
    if shareWith == "allFollowers":
        ins = 'INSERT INTO photo VALUES(NULL,%s, CURRENT_TIMESTAMP, %s, 1, %s)'
        cursor.execute(ins,(username,filepath,caption))
        conn.commit()
    else:
        ins = 'INSERT INTO photo VALUES(NULL, %s, CURRENT_TIMESTAMP, %s, 0, %s)'
        cursor.execute(ins,(username,filepath,caption))
        conn.commit()
        query = 'SELECT LAST_INSERT_ID()'
        pID = cursor.execute(query)
        #return render_template('debug.html',pID=pID,shareWith=shareWith)
        groupName = cursor.execute('SELECT %s.groupName',(shareWith))
        creatorUsername = cursor.execute('SELECT %s.creatorUsername',(shareWith))
        return render_template('debug.html',gn=groupName,cu=creatorUsername)
        ins = 'INSERT INTO share VALUE(%s,%s,%s)'
        cursor.execute(ins,(pID,groupName,creatorUsername))
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
        return render_template("friendGroups.html",user=username)
    
@app.route('/follows')
def follows():
    try:
        username=session['username']
    except:
        return redirect('/')
    cursor = conn.cursor()
    query = 'SELECT followeeUsername FROM follow WHERE followeeUsername = %s AND followStatus = 0'
    cursor.execute(query,(username))
    newFollowers = cursor.fetchall()
    cursor.close()
    return render_template("follows.html",newFollowers)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

app.secret_key = '4pp 53cr37 k3y'
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)