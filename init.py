# -*- coding: utf-8 -*-
"""
Finstagram Code by Gafurul (Rafi) Islam Kazi - gik211
"""

#cd Documents\GitHub\Finstagram
#set FLASK_ENV=development

from flask import Flask, render_template, request, session, url_for, redirect, send_from_directory
import pymysql.cursors
import hashlib
import os
SALT = '7h1515my54l7d0n7judg3m30k'

app = Flask(__name__)
UPLOAD_FOLDER = 'photos'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

conn = pymysql.connect(host='localhost',
                       port = 3308,
                       user='root',
                       password='',
                       db='Finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#These routes are meant for debugging purposes only
@app.route('/debug1')
def debug1():
    return render_template('debug.html')

@app.route('/debug2', methods=['GET','POST'])
def debug2():
    comment=request.form['comment']
    emoji=request.form['emoji']
    print(comment,emoji)
    return render_template('debug.html', comment=comment,emoji=emoji)

#Login page route
@app.route('/')
def login():
    #Check for existing session
    try:
        username = session['username']
        return redirect(url_for('home'))
    except:
        error = request.args.get('error')
        return render_template('login.html',error=error)

#Account registration page route
@app.route('/register')
def register():
    #Check for existing session
    try:
        username = session['username']
        return redirect(url_for('home'))
    except:
        error = request.args.get('error')
        return render_template('register.html',error=error)

#Login authentication route: Rejects login if no username exists with given password
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #Retrieval of argument from form
    username = request.form['username']
    
    #All passwords are salted and hashed
    password = request.form['password'] + SALT
    hashword = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    #Query for username and password pairing
    cursor = conn.cursor()
    query = 'SELECT * FROM person WHERE username = %s and password = %s'
    cursor.execute(query, (username, hashword))
    data = cursor.fetchone()
    cursor.close()
    
    #If username and password exist, commence session
    if(data):
        session['username'] = username
        return redirect(url_for('home'))
    else:
        return redirect('/?error=1')

#Registration authentication route: Rejects registration if verification check failed, username already exists, or invalid character used in username
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #Read from form
    username = request.form['username']
    password = request.form['password'] + SALT
    vpassword = request.form['vpassword'] + SALT
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    email = request.form['email']
    
    #Password verification
    if password!=vpassword:
        return redirect('/register?error=2')
    
    #Username character check
    for char in username:
        if char<'0' or (char>'9' and char<'A') or (char>'Z' and char<'a') or char>'z':
            return redirect('/register?error=3')
    
    #Query for username
    cursor = conn.cursor()
    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchone()
    
    #Check if username exists
    if(data):
        return redirect('/register?error=1')
    
    #Insertion of new person into database
    hashword = hashlib.sha256(password.encode('utf-8')).hexdigest()
    ins = 'INSERT INTO person VALUES(%s, %s, %s, %s, %s)'
    cursor.execute(ins, (username, hashword, firstName, lastName, email))
    conn.commit()
    cursor.close()
    
    #Commence session
    session['username']=username
    return redirect(url_for('home'))
    
#File route
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)
    
#Home page route
@app.route('/home')
def home():
    #Check for existing session
    try:
        username=session['username']
    except:
        return redirect('/')
    
    #Query to retrieve posts visible to this user
    cursor = conn.cursor()
    #The section after the second UNION is to be removed when user pages are implemented
    query = 'SELECT photo.pID, posterUsername, postingDate, rc, tc FROM follow JOIN photo ON followeeUsername = posterUsername LEFT JOIN (SELECT pID, COUNT(reactorUsername) AS rc FROM reaction GROUP BY pID) AS r ON r.pID = photo.pID LEFT JOIN (SELECT pID, SUM(tagStatus) AS tc FROM tag GROUP BY pID) AS t ON t.pID = photo.pID WHERE followerUsername = %s AND followStatus = 1 UNION SELECT photo.pID, posterUsername, postingDate, rc, tc FROM photo  LEFT JOIN (SELECT pID, COUNT(reactorUsername) AS rc FROM reaction GROUP BY pID) AS r ON r.pID = photo.pID LEFT JOIN (SELECT pID, SUM(tagStatus) AS tc FROM tag GROUP BY pID) AS t ON t.pID = photo.pID WHERE (photo.pID) IN (SELECT pID FROM share WHERE (groupName,creatorUsername) IN (SELECT groupName,creatorUsername FROM groupmember WHERE memberUsername = %s)) UNION SELECT photo.pID AS pID, posterUsername, postingDate, rc, tc FROM photo LEFT JOIN (SELECT pID, COUNT(reactorUsername) AS rc FROM reaction GROUP BY pID) AS r ON r.pID = photo.pID LEFT JOIN (SELECT pID, SUM(tagStatus) AS tc FROM tag GROUP BY pID) AS t ON t.pID = photo.pID WHERE posterUsername=%s ORDER BY postingDate DESC'
    cursor.execute(query, (username,username,username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html',user=username,feed=data)
    
#Post search page route
@app.route('/searchPosts', methods=['GET','POST'])
def searchPosts():
    #Check for existing session
    try:
        username=session['username']
    except:
        redirect('/')
    #Retrieval of URL arguments
    #Note: Following conventions seen on other websites regarding search functions, arguments are retrieved from URL instead of a form
    searchMode = request.args.get('searchMode')
    searchTerm = request.args.get('searchTerm')
    
    #Query for posts that fit criteria
    cursor = conn.cursor()
    if searchMode == "poster": #Look for posts posted by a certain user
        query = 'SELECT pID FROM photo WHERE posterUsername = %s AND (pID) IN (SELECT DISTINCT pID FROM follow JOIN photo ON followeeUsername = posterUsername WHERE followerUsername = %s AND followStatus = 1 UNION SELECT pID FROM photo WHERE (pID) IN (SELECT pID FROM share WHERE (groupName,creatorUsername) IN (SELECT groupName,creatorUsername FROM groupmember WHERE memberUsername = %s)) UNION SELECT pID FROM photo WHERE posterUsername = %s)'
    elif searchMode == "tag": #Look for posts where a certain user is tagged
        query = 'SELECT pID FROM tag WHERE taggedUsername = %s AND (pID) IN (SELECT DISTINCT pID FROM follow JOIN photo ON followeeUsername = posterUsername WHERE followerUsername = %s AND followStatus = 1 UNION SELECT pID FROM photo WHERE (pID) IN (SELECT pID FROM share WHERE (groupName,creatorUsername) IN (SELECT groupName,creatorUsername FROM groupmember WHERE memberUsername = %s)) UNION SELECT pID FROM photo WHERE posterUsername = %s)'
    cursor.execute(query,(searchTerm,username,username,username))
    results = cursor.fetchall()
    cursor.close()
    return render_template("searchPosts.html",results=results,searchTerm=searchTerm,searchMode=searchMode)

#View photo route
@app.route('/viewPhoto/<pID>', methods=['GET','POST'])
def viewPhoto(pID):
    #Check for existing session
    try:
        username = session['username']
    except:
        return redirect('/')
    
    error = request.args.get('error')
    cursor = conn.cursor()
    
    #Query to check if post is visible to user
    query = 'SELECT pID FROM follow JOIN photo ON followeeUsername = posterUsername WHERE followerUsername = %s AND followStatus = 1 AND pID = %s UNION SELECT pID FROM photo WHERE pID = %s AND (pID) IN (SELECT pID FROM share WHERE (groupName,creatorUsername) IN (SELECT groupName,creatorUsername FROM groupmember WHERE memberUsername = %s)) UNION SELECT pID FROM photo WHERE posterUsername = %s AND pID = %s'
    cursor.execute(query,(username,pID,pID,username,username,pID))
    visible = cursor.fetchone()
    if visible==None:
        return render_template('cannotViewPhoto.html',user=username)
    
    #Query to retrieve Photo information
    query = 'SELECT pID,caption,posterUsername,postingDate,first_name,last_name FROM photo JOIN person ON posterUsername=username WHERE pID = %s'
    cursor.execute(query,(pID))
    photoData = cursor.fetchone()
    
    #Query to retrieve relevant Reaction information
    query = 'SELECT reactorUsername,reactionTime,comment,emoji FROM reaction WHERE pID = %s ORDER BY reactionTime DESC'
    cursor.execute(query,(pID))
    reactionData = cursor.fetchall()
    reactionCount = len(reactionData)
    if reactionCount == 0:
        noReactions = True
    else:
        noReactions = False
    
    #Query to retrieve relevant Tag information
    query = 'SELECT username, first_name, last_name FROM person WHERE (username) IN (SELECT taggedUsername FROM tag WHERE (tagStatus = 1 AND pID = %s) OR (tagStatus = 0 AND pID = %s AND taggedUsername = %s))'
    cursor.execute(query,(pID,pID,username))
    tagData = cursor.fetchall()
    tagCount = len(tagData)
    
    cursor.close()
    return render_template('viewPhoto.html',user=username,pData=photoData,rData=reactionData,rCount=reactionCount,noReactions=noReactions,tData=tagData,tCount=tagCount,error=error)

#Tag submission system
@app.route('/submitTag',methods=['GET','POST'])
def submitTag():
    #Check for exsiting session
    try:
        username=session['username']
    except:
        return redirect('/')
    
    #Retrieval of arguments from URL & form
    pID = request.args.get('pID')
    newTag = request.form['newTag']
    
    #Removal of @ if necessary (an @ is not needed when tagging users)
    if newTag[0]=="@":
        newTag = newTag[1:]
        
    #Query to find username
    cursor = conn.cursor()
    query = "SELECT username FROM person AS p WHERE username = %s AND (username) NOT IN (SELECT taggedUsername FROM tag WHERE pID = %s)"
    cursor.execute(query,(newTag,pID))
    username_valid = cursor.fetchone()
    
    #Query to see if tag is visible to tagged user
    query = "SELECT pID FROM photo WHERE pID = %s AND (pID) IN (SELECT DISTINCT pID FROM follow JOIN photo ON followeeUsername = posterUsername WHERE followerUsername = %s AND followStatus = 1 UNION SELECT pID FROM photo WHERE (pID) IN (SELECT pID FROM share WHERE (groupName,creatorUsername) IN (SELECT groupName,creatorUsername FROM groupmember WHERE memberUsername = %s)) UNION SELECT pID FROM photo WHERE posterUsername = %s)"
    cursor.execute(query,(pID,newTag,newTag,newTag))
    visible = cursor.fetchone()
    
    #Insertion of tag into database
    if username_valid and visible:
        #If tagging self
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
    
#Reaction submission route
@app.route('/submitReaction',methods=['GET','POST'])
def submitReaction():
    #Check for existing session
    try:
        username=session['username']
    except:
        return redirect('/')
    
    #Retrieval of arguments
    pID = request.args.get('pID')
    emoji = request.form['emoji']
    comment = request.form['comment']
    
    #Query to find existing comment by user
    cursor = conn.cursor()
    query = "SELECT reactorUsername FROM reaction WHERE reactorUsername = %s AND pID = %s"
    cursor.execute(query,(username,pID))
    comment_exists = cursor.fetchone()
    
    #Updates reaction if comment exists, otherwise inserts new reaction
    if comment_exists:
        upd = 'UPDATE reaction SET comment = %s, emoji = %s, reactionTime = CURRENT_TIMESTAMP WHERE reactorUsername = %s AND pID = %s'
        cursor.execute(upd,(comment,emoji,username,pID))
    else:
        ins = 'INSERT INTO reaction VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s)'
        cursor.execute(ins,(pID,username,comment,emoji))
    conn.commit()
    cursor.close()
    return redirect('viewPhoto?pID='+pID)

#New post page route
@app.route('/newPost')
def newPost():
    #Check for existing session
    try:
        username=session['username']
    except:
        return redirect('/')
    
    #Query for friend group information
    cursor=conn.cursor()
    query = 'SELECT groupName,creatorUsername FROM groupMember WHERE memberUsername = %s'
    cursor.execute(query,(username))
    data=cursor.fetchall()
    cursor.close()
    return render_template('newPost.html',friendGroups=data)

#Photo submission route
@app.route('/submitPost', methods=['GET','POST'])
def submitPost():
    #Check for existing session
    try:
        username=session['username']
    except:
        return redirect('/')
    
    #Retrieval of arguments from form
    file = request.files['file']
    caption = request.form['caption']
    shareWith = request.form['shareWith']
    
    cursor=conn.cursor()
    
    #Insertion of Photo into database
    ins = 'INSERT INTO photo VALUES(NULL,%s, CURRENT_TIMESTAMP, %s, %s)'
    cursor.execute(ins,(username,shareWith == "allFollowers",caption))
    conn.commit()
    query = 'SELECT LAST_INSERT_ID();'
    cursor.execute(query)
    data = cursor.fetchone()
    pID = data['LAST_INSERT_ID()']
    
    #Copies file into server's upload folder
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(pID)+".jpg"))
    
    #Insertion of Share into database
    if not shareWith == "allFollowers":
        shareWith_vals=shareWith.split(',')
        groupName = shareWith_vals[0]
        creatorUsername = shareWith_vals[1]
        ins = 'INSERT INTO share VALUE(%s,%s,%s)'
        cursor.execute(ins,(pID,groupName,creatorUsername))
        conn.commit()
    cursor.close()
    return redirect('/home')

#Friend groups hub page route
@app.route('/friendGroups')
def friendGroups():
    #Check for exisiting session
    try:
        username=session['username']
    except:
        return redirect('/')
    error = request.args.get('error')
    
    #Query for friend groups
    cursor = conn.cursor()
    query = 'SELECT * FROM friendGroup NATURAL JOIN (SELECT COUNT(memberUsername) AS c, groupName, creatorUsername FROM groupmember GROUP BY groupName,creatorUsername) AS memberCount WHERE (groupName,creatorUsername) IN (SELECT groupName,creatorUsername FROM groupMember WHERE memberUsername = %s)'
    cursor.execute(query,(username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('friendGroups.html',friendGroups=data,error=error)

#Friend group individial page route
@app.route('/viewFriendGroup')
def viewFriendGroup():
    #Check for existing session
    try:
        username=session['username']
    except:
        return redirect('/')
    
    #Retrieval of arguments from URL
    groupName = request.args.get('gn')
    creatorUsername = request.args.get('cu')
    
    cursor = conn.cursor()
    
    #Query for checking if user exists as member of group
    query = 'SELECT * FROM groupmember WHERE groupName= %s AND creatorUsername = %s AND memberUsername = %s'
    cursor.execute(query,(groupName,creatorUsername,username))
    visible = cursor.fetchone()
    if visible == None:
        return render_template('cannotViewFriendGroup.html',user=username)
    
    #Query for friend group information
    query = 'SELECT description FROM friendGroup WHERE groupName = %s AND creatorUsername = %s'
    cursor.execute(query,(groupName,creatorUsername))
    description = cursor.fetchone()
    
    #Query for friend group creator information
    query = 'SELECT first_name, last_name FROM person WHERE username = %s'
    cursor.execute(query,(creatorUsername))
    creatorInfo = cursor.fetchone()
    
    #Query for friend group members information
    query = 'SELECT username, first_name, last_name FROM person WHERE username IN (SELECT memberUsername FROM groupmember WHERE groupName = %s AND creatorUsername = %s)'
    cursor.execute(query,(groupName,creatorUsername))
    members = cursor.fetchall()
    memberCount = len(members)
    
    #Query for friend group posts
    query = 'SELECT pID FROM share WHERE groupName = %s AND creatorUsername = %s'
    cursor.execute(query,(groupName,creatorUsername))
    posts = cursor.fetchall()
    pCount = len(posts)
    
    #Query for follower information
    query = 'SELECT DISTINCT followerUsername FROM follow WHERE followeeUsername = %s AND followStatus = 1 AND (followerUsername) NOT IN (SELECT memberUsername FROM groupmember WHERE groupName = %s AND creatorUsername = %s)'
    cursor.execute(query,(username,groupName,creatorUsername))
    followers = cursor.fetchall()
    
    cursor.close()
    
    return render_template('viewFriendGroup.html',description=description,creatorInfo=creatorInfo,groupName=groupName,creatorUsername=creatorUsername,members=members,memberCount=memberCount,posts=posts,pCount=pCount,followers=followers,user=username)

#New friend group authentication: Inserts new friend group into database if user does not own a friend group of the same name
@app.route('/authFriendGroup', methods = ['GET', 'POST'])
def authFriendGroup():
    #Check for existing session
    try:
        username=session['username']
    except:
        return redirect('/')
    
    #Retrival of arguments from form
    newGroupName = request.form['newGroupName']
    description = request.form['description']
    
    #Query for group name for current user
    cursor = conn.cursor()
    query = 'SELECT groupName,creatorUsername FROM friendGroup WHERE groupName = %s AND creatorUsername = %s'
    cursor.execute(query,(newGroupName,username))
    data = cursor.fetchone()
    
    #If no group name exists for current user, friend group is inserted into database & new member (the creator) is inserted into database
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
    
#Friend addition route
@app.route('/addFriend', methods=['GET','POST'])
def addFriend():
    #Check for an existing session
    try:
        username=session['username']
    except:
        return redirect('/')
    
    #Retrival of arguments from form and URL
    memberUsername = request.form['newFriend']
    creatorUsername = request.args.get('cu')
    groupName = request.args.get('gn')
    
    #Check if username given is a valid follower
    cursor = conn.cursor()
    query = 'SELECT DISTINCT followerUsername FROM follow WHERE followerUsername = %s followeeUsername = %s AND followStatus = 1 AND (followerUsername) NOT IN (SELECT memberUsername FROM groupmember WHERE groupName = %s AND creatorUsername = %s)'
    cursor.execute(query,(memberUsername,username,groupName,creatorUsername))
    followerValid = cursor.fetchone()
    print(followerValid)
    
    #Inserts new group member into database
    ins = 'INSERT INTO groupmember VALUES(%s,%s,%s)'
    cursor.execute(ins,(groupName,creatorUsername,memberUsername))
    conn.commit()
    cursor.close()
    return redirect('/viewFriendGroup?gn='+groupName+'&cu='+creatorUsername)

#Friend removal route
@app.route('/removeFriend', methods=['GET','POST'])
def removeFriend():
    #Check for existing session
    try:
        username=session['username']
    except:
        return redirect('/')
    
    #Retrival of arguments
    creatorUsername = request.args.get('cu')
    groupName = request.args.get('gn')
    memberUsername = request.args.get('mu') #Note to self: find way to not need member username in URL
    
    cursor = conn.cursor()
    
    #Deletion of tags of group member in group's posts
    delete = 'DELETE FROM tags WHERE taggedUsername = %s AND pID IN (SELECT pID IN share WHERE groupName = %s AND creatorUsername = %s)'
    cursor.execute(delete,(memberUsername,groupName,creatorUsername))
    cursor.commit()
    
    #Deletion of group member
    delete = 'DELETE FROM groupMember WHERE groupName = %s AND creatorUsername = %s AND memberUsername = %s'
    cursor.execute(delete,(groupName,creatorUsername,memberUsername))
    conn.commit()
    cursor.close()
    return redirect('/viewFriendGroup?gn='+groupName+'&cu='+creatorUsername)
    
#Follows page route
@app.route('/follows')
def follows():
    #Check for existing session
    try:
        username=session['username']
    except:
        return redirect('/')
    error = request.args.get('error')
    notif = request.args.get('notification')
    
    #Query for pending followers
    cursor = conn.cursor()  
    query = 'SELECT followerUsername,first_name,last_name FROM follow JOIN person ON followerUsername = username WHERE followeeUsername = %s AND followStatus = 0'
    cursor.execute(query,(username))
    pFollows = cursor.fetchall()
    
    #Query for people who follow user
    query = 'SELECT followerUsername,first_name,last_name FROM follow JOIN person ON followerUsername = username WHERE followeeUsername = %s AND followStatus = 1'
    cursor.execute(query,(username))
    followers = cursor.fetchall()
    
    #Query for people who user follows
    query = 'SELECT followeeUsername,first_name,last_name FROM follow JOIN person ON followeeUsername = username WHERE followerUsername = %s AND followStatus = 1'
    cursor.execute(query,(username))
    followees = cursor.fetchall()
    cursor.close()
    
    return render_template("follows.html",pendingFollows=pFollows,followers=followers,followees=followees,error=error,notification=notif)

#Creation of new follower request: Inserts an inactive follow into the database if username is valid
@app.route('/newFollowee', methods = ['GET','POST'])
def newFollowee():
    #Check for existing session
    try:
        username=session['username']
    except:
        return redirect('/')
    
    #Retrieval of argument from form
    followeeUsername = request.form['newFollowee']
    
    #Query for valid followee username
    cursor = conn.cursor()
    query = 'SELECT username FROM person AS p WHERE username = %s AND (username) NOT IN (SELECT followeeUsername FROM follow WHERE followerUsername = %s) AND username!=%s'
    cursor.execute(query,(followeeUsername,username,username))
    data = cursor.fetchone()
    
    #If followee exists and is valid, new follow request is inserted into database
    if(data):
        ins = 'INSERT INTO follow VALUES(%s,%s,0)'
        cursor.execute(ins,(username,followeeUsername))
        conn.commit()
        cursor.close()
        return redirect("/follows?notification=1")
    else:
        cursor.close()
        return redirect("/follows?error=1")

#Accept or Decline follower requests route: Activates or deletes a follow request in database depending on given action
@app.route('/setFollows', methods = ['GET', 'POST'])
def setFollows():
    #Check for existing session
    try:
        username=session['username']
    except:
        return redirect('/')
    
    #Retrieval of arguments from form
    action_vals = request.form['action']
    action_split = action_vals.split(',')
    followerUsername = action_split[0]
    action = int(action_split[1])
    
    #Query to update or delete follow request in database
    cursor = conn.cursor()
    if(action):
        stmt = 'UPDATE follow SET followStatus = 1 WHERE followerUsername = %s AND followeeUsername = %s'
    else:
        stmt = 'DELETE FROM follow WHERE followerUsername = %s AND followeeUsername = %s'
    cursor.execute(stmt,(followerUsername,username))
    conn.commit()
    cursor.close()
    return redirect("follows")

#Unfollow route
@app.route('/unfollow')
def unfollow():
    #Check for existing session
    try:
        username=session['username']
    except:
        return redirect('/')
    
    #Retrieve arguments from URL
    followeeUsername = request.args.get('fu')
    
    cursor = conn.cursor()
    
    #Query to delete user's tags from posts make by followee
    stmt = 'DELETE FROM tag WHERE taggedUsername = %s AND pID IN (SELECT pID FROM photo WHERE posterUsername = %s)'
    cursor.execute(stmt,(username,followeeUsername))
    conn.commit()
    
    #Query to delete follow from database
    stmt = 'DELETE FROM follow WHERE followerUsername = %s AND followeeUsername = %s'
    cursor.execute(stmt,(username,followeeUsername))
    conn.commit()
    cursor.close()
    return redirect("follows")
    
#Tags page route
@app.route('/tags')
def tags():
    #Check for existing session
    try:
        username=session['username']
    except:
        return redirect('/')
    
    #Query for Tag information
    cursor = conn.cursor()
    query = 'SELECT pID,posterUsername,postingDate FROM photo WHERE (pID) IN (SELECT pID FROM tag WHERE taggedUsername = %s and tagStatus = 0)'
    cursor.execute(query,(username))
    tagList = cursor.fetchall()
    return render_template('tags.html',tagList = tagList)
    
#Accept or Delete Tag route: Accepts or Deletes a tag request on a post in database depending on given action
@app.route('/setTags', methods = ['GET','POST'])
def setTags():
    #Check for existing session
    try:
        username=session['username']
    except:
        return redirect('/')
    
    #Retrieval of arguments
    source_page = request.args.get('source')
    action_vals = request.form['action']
    action_split = action_vals.split(',')
    pID = action_split[0]
    action = int(action_split[1])
    
    cursor = conn.cursor()
    
    #Query to update or delete tag in database
    if action:
        stmt = 'UPDATE tag SET tagStatus = 1 WHERE taggedUsername = %s AND pID = %s'
    else:
        stmt = 'DELETE FROM tag WHERE taggedUsername = %s AND pID = %s'
    cursor.execute(stmt,(username,pID))
    conn.commit()
    cursor.close()
    if source_page == 'tags':
        return redirect('tags')
    else:
        return redirect('viewPhoto/'+source_page)

#Logout route
@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

app.secret_key = '4pp 53cr37 k3y'
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
