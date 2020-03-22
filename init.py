# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 16:33:11 2020

@author: Rafi
"""

#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3308,
                       user='root',
                       password='',
                       db='Finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define route for login
@app.route('/')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
    #stores the results in a variable
    data = cursor.fetchone()
    cursor.close()
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        return render_template('login.html', error='Invalid login or username')

#Authenticates the registration
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    vpassword = request.form['vpassword']
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    email = request.form['email']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    if(data):
        #If the previous query returns data, then username already exists
        return render_template('register.html', error = "This username is taken")
    else:
        if password!=vpassword:
            return render_template('register.html', error = "Passwords do not match")
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, password, firstName, lastName, email))
        conn.commit()
        cursor.close()
        return render_template('home.html',user=username)
    
@app.route('/home')
def home():
    try:
        username=session['username']
    except:
        return redirect('/')
    #cursor = conn.cursor();
    #query = 'SELECT filename FROM person NATURAL JOIN  WHERE username = %s ORDER BY ts DESC'
    #cursor.execute(query, (username))
    #data = cursor.fetchall()
    #cursor.close()
    return render_template('home.html',user=username)#,feed=data)

@app.route('/friendGroups')
def friendGroup():
    try:
        username=session['username']
    except:
        return redirect('/')
    cursor = conn.cursor()
    query = 'SELECT * FROM groupMember WHERE memberUsername = %s'
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
    print("ding1")
    cursor = conn.cursor()
    print("ding2")
    query = 'SELECT groupName,creatorUsername FROM friendGroup WHERE groupName = %s AND creatorUsername = %s'
    cursor.execute(query,(newGroupName,username))
    print("ding3")
    data = cursor.fetchone()
    print("ding4")
    error = None
    if(data):
        cursor.close()
        error = 'You already own a friend group with this name'
        return render_template("newFriendGroup", error=error)
    else:
        ins = 'INSERT INTO friendGroup VALUES(%s, %s, %s)'
        cursor.execute(ins, (newGroupName,username,description))
        print("ding5")
        conn.commit()
        print("ding6")
        ins = 'INSERT INTO groupMember VALUES(%s, %s, %s)'
        cursor.execute(ins, (newGroupName,username,username))
        print("ding7")
        conn.commit()
        print("ding8")
        cursor.close()
        print("ding9")
        return render_template("friendGroups.html",user=username)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

app.secret_key = '4pp 53cr37 k3y'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)