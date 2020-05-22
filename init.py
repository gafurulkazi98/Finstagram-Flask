# -*- coding: utf-8 -*-
"""
Finstagram Code by Gafurul (Rafi) Islam Kazi - gik211
"""

from flask import Flask, flash, render_template, request, session, url_for, redirect, send_from_directory
import pymysql.cursors
import hashlib
import os
SALT = '7h1515my54l7d0n7judg3m30k'

app = Flask(__name__)
UPLOAD_FOLDER = 'templates/photos'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

conn = pymysql.connect(host='localhost',
                       port = 3308,
                       user='root',
                       password='',
                       db='Finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

def readFile(filepath):
    with open(filepath,"r") as f:
        return f.read()

@app.route('/debug1')
def debug1():
    return render_template('debug.html')

@app.route('/debug2', methods=['GET','POST'])
def debug2():
    comment=request.form['comment']
    emoji=request.form['emoji']
    print(comment,emoji)
    return render_template('debug.html', comment=comment,emoji=emoji)


@app.route('/')
def login():
    try:
        username = session['username']
        return redirect(url_for('home'))
    except:
        error_arg = request.args.get('error')
        errorStr = None
        if error_arg == "1":
            errorStr = 'Invalid login or username'
        return render_template('login.html',error=errorStr)

@app.route('/register')
def register():
    error_arg = request.args.get('error')
    errorStr = None
    if error_arg == "1":
        errorStr = "Invalid login or username"
    elif error_arg == "2":
        errorStr = "Passwords do not match"
    return render_template('register.html',error=errorStr)

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
        return redirect('/?error=1')

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
        return redirect('/register?error=1')
    else:
        if password!=vpassword:
            return redirect('/register?error=2')
        hashword = hashlib.sha256(password.encode('utf-8')).hexdigest()
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, hashword, firstName, lastName, email))
        conn.commit()
        cursor.close()
        session['username']=username
        return redirect(url_for('home'))
    
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)
    
@app.route('/home')
def home():
    try:
        username=session['username']
    except:
        return redirect('/')
    cursor = conn.cursor()
    query = 'SELECT DISTINCT pID,postingDate,posterUsername FROM follow JOIN photo ON followeeUsername = posterUsername WHERE followerUsername = %s AND followStatus = 1 UNION SELECT pID,postingDate,posterUsername FROM photo WHERE (pID) IN (SELECT pID FROM share WHERE (groupName,creatorUsername) IN (SELECT groupName,creatorUsername FROM groupmember WHERE memberUsername = %s)) UNION SELECT pID,postingDate,posterUsername FROM photo WHERE posterUsername = %s ORDER BY postingDate DESC'
    cursor.execute(query, (username,username,username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html',user=username,feed=data)

@app.route('/viewPhoto/<pID>', methods=['GET','POST'])
def viewPhoto(pID):
    try:
        username=session['username']
    except:
        return redirect('/')
    error = request.args.get('error')
    cursor = conn.cursor()
    query = 'SELECT pID,caption,posterUsername,postingDate,first_name,last_name FROM photo JOIN person ON posterUsername=username WHERE pID = %s'
    cursor.execute(query,(pID))
    photoData = cursor.fetchone()
    
    query = 'SELECT reactorUsername,reactionTime,comment,emoji FROM reaction WHERE pID = %s ORDER BY reactionTime DESC'
    cursor.execute(query,(pID))
    reactionData = cursor.fetchall()
    
    query = 'SELECT username,first_name,last_name FROM person WHERE (username) IN (SELECT taggedUsername FROM tag WHERE tagStatus = 1 AND pID = %s)'
    cursor.execute(query,(pID))
    tagData = cursor.fetchall()
    
    return render_template('viewPhoto.html',user=username,pData=photoData,rData=reactionData,tData=tagData,error=error)

@app.route('/submitTag',methods=['GET','POST'])
def submitTag():
    try:
        username=session['username']
    except:
        return redirect('/')
    pID = request.args.get('pID')
    newTag = request.form['newTag']
    cursor = conn.cursor()
    query = "SELECT username FROM person AS p WHERE username = %s AND (username) NOT IN (SELECT taggedUsername FROM tag WHERE pID = %s)"
    cursor.execute(query,(newTag,pID))
    username_valid = cursor.fetchone()
    query = "SELECT pID FROM photo WHERE pID = %s AND (pID) IN (SELECT DISTINCT pID FROM follow JOIN photo ON followeeUsername = posterUsername WHERE followerUsername = %s AND followStatus = 1 UNION SELECT pID FROM photo WHERE (pID) IN (SELECT pID FROM share WHERE (groupName,creatorUsername) IN (SELECT groupName,creatorUsername FROM groupmember WHERE memberUsername = %s)) UNION SELECT pID FROM photo WHERE posterUsername = %s)"
    cursor.execute(query,(pID,newTag,newTag,newTag))
    visible = cursor.fetchone()
    if username_valid and visible:
        if newTag == username:
            ins = 'INSERT INTO tag VALUES (%s,%s,1)'
        else:
            ins = 'INSERT INTO tag VALUES (%s,%s,0)'
        cursor.execute(ins,(pID,newTag))
        conn.commit()
        cursor.close()
        return redirect('viewPhoto?pID='+pID)
    else:
        cursor.close()
        return redirect('viewPhoto?pID='+pID+'&error=1')
    
@app.route('/submitReaction',methods=['GET','POST'])
def submitReaction():
    try:
        username=session['username']
    except:
        return redirect('/')
    pID = request.args.get('pID')
    emoji = request.form['emoji']
    comment = request.form['comment']
    cursor = conn.cursor()
    query = "SELECT reactorUsername FROM reaction WHERE reactorUsername = %s AND pID = %s"
    cursor.execute(query,(username,pID))
    comment_exists = cursor.fetchone()
    if comment_exists:
        upd = 'UPDATE reaction SET comment = %s, emoji = %s, reactionTime = CURRENT_TIMESTAMP WHERE reactorUsername = %s AND pID = %s'
        cursor.execute(upd,(comment,emoji,username,pID))
    else:
        ins = 'INSERT INTO reaction VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s)'
        cursor.execute(ins,(pID,username,comment,emoji))
    conn.commit()
    cursor.close()
    return redirect('viewPhoto?pID='+pID)
    
# @app.route('/viewPerson/', methods=['GET','POST'])
# def viewPerson():
#     try:
#         username=session['username']
#     except:
#         return redirect('/')
#     viewedUser = request.args.get('username')
#     cursor = conn.cursor()
#     query = 'SELECT username,first_name,last_name,email FROM person WHERE username = %s'
#     cursor.execute(query,viewedUser)
#     userPageData = cursor.fetchone()
#     return render_template('viewPerson.html',uData=userPageData,viewingSelf=viewedUser==username)

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
    file = request.files['file']
    ext = file.filename.rsplit('.', 1)[1].lower()
    #photo = b64encode(photoData).decode("utf-8")
    #return render_template("debug.html",photo=photo)
    caption = request.form['caption']
    shareWith = request.form['shareWith']
    
    cursor=conn.cursor()
    
    ins = 'INSERT INTO photo VALUES(NULL,%s, CURRENT_TIMESTAMP, %s, %s)'
    cursor.execute(ins,(username,shareWith == "allFollowers",caption))
    conn.commit()
    query = 'SELECT LAST_INSERT_ID();'
    cursor.execute(query)
    data = cursor.fetchone()
    pID = data['LAST_INSERT_ID()']
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(pID)+".jpg"))
    
    if not shareWith == "allFollowers":
        shareWith_vals=shareWith.split(',')
        groupName = shareWith_vals[0]
        creatorUsername = shareWith_vals[1]
        ins = 'INSERT INTO share VALUE(%s,%s,%s)'
        cursor.execute(ins,(pID,groupName,creatorUsername))
        conn.commit()
    cursor.close()
    return redirect('/home')

@app.route('/friendGroups')
def friendGroup():
    try:
        username=session['username']
    except:
        return redirect('/')
    error = request.args.get('error')
    cursor = conn.cursor()
    query = 'SELECT * FROM friendGroup WHERE (groupName,creatorUsername) IN (SELECT groupName,creatorUsername FROM groupMember WHERE memberUsername = %s)'
    cursor.execute(query,(username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('friendGroups.html',user=username,friendGroups=data,error=error)

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
        return redirect("/friendGroups?error=1")
    else:
        ins = 'INSERT INTO friendGroup VALUES(%s, %s, %s)'
        cursor.execute(ins, (newGroupName,username,description))
        conn.commit()
        ins = 'INSERT INTO groupMember VALUES(%s, %s, %s)'
        cursor.execute(ins, (newGroupName,username,username))
        conn.commit()
        cursor.close()
        return redirect("/friendGroups")
    
@app.route('/follows')
def follows():
    try:
        username=session['username']
    except:
        return redirect('/')
    error = request.args.get('error')
    notif = request.args.get('notification')
    cursor = conn.cursor()  
    query = 'SELECT followerUsername,first_name,last_name FROM follow JOIN person ON followerUsername = username WHERE followeeUsername = %s AND followStatus = 0'
    cursor.execute(query,(username))
    pFollows = cursor.fetchall()
    query = 'SELECT followerUsername,first_name,last_name FROM follow JOIN person ON followerUsername = username WHERE followeeUsername = %s AND followStatus = 1'
    cursor.execute(query,(username))
    aFollows = cursor.fetchall()
    cursor.close()
    return render_template("follows.html",user=username,pendingFollows=pFollows,acceptedFollows=aFollows,error=error,notification=notif)

@app.route('/newFollowee', methods = ['GET','POST'])
def newFollowee():
    try:
        username=session['username']
    except:
        return redirect('/')
    cursor = conn.cursor()
    followeeUsername = request.form['newFollowee']
    query = 'SELECT username FROM person AS p WHERE username = %s AND (username) NOT IN (SELECT followeeUsername FROM follow WHERE followerUsername = %s)'
    cursor.execute(query,(followeeUsername,username))
    data = cursor.fetchone()
    if followeeUsername == username:
        cursor.close()
        return redirect("/follows?error=1")
    if(data):
        ins = 'INSERT INTO follow VALUES(%s,%s,0)'
        cursor.execute(ins,(username,followeeUsername))
        conn.commit()
        cursor.close()
        return redirect("/follows?notification=1")
    else:
        cursor.close()
        return redirect("/follows?error=1")

@app.route('/setFollows', methods = ['GET', 'POST'])
def setFollows():
    try:
        username=session['username']
    except:
        return redirect('/')
    cursor = conn.cursor()
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
    cursor.close()
    return redirect("follows")

@app.route('/tags')
def tags():
    try:
        username=session['username']
    except:
        return redirect('/')
    cursor = conn.cursor()
    query = 'SELECT pID,posterUsername,postingDate FROM photo WHERE (pID) IN (SELECT pID FROM tag WHERE taggedUsername = %s and tagStatus = 0)'
    cursor.execute(query,(username))
    tagList = cursor.fetchall()
    #for tag in tagList:
   #     tag['filepath'] = b64encode(tag['filepath']).decode("utf-8")
    return render_template('tags.html',tagList = tagList)
    
@app.route('/setTags', methods = ['GET','POST'])
def setTags():
    try:
        username=session['username']
    except:
        return redirect('/')
    cursor = conn.cursor()
    action_vals = request.form['action']
    action_split = action_vals.split(',')
    pID = action_split[0]
    action = int(action_split[1])
    if action:
        stmt = 'UPDATE tag SET tagStatus = 1 WHERE taggedUsername = %s AND pID = %s'
    else:
        stmt = 'DELETE FROM tag WHERE taggedUsername = %s AND pID = %s'
    cursor.execute(stmt,(username,pID))
    conn.commit()
    cursor.close()
    return redirect('tags')
    
@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

app.secret_key = '4pp 53cr37 k3y'
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
