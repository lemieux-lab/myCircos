####################################################
####						####
####		    VIEWS SESSION		####
####						####
####################################################

import os, os.path
from flask import render_template, redirect, url_for, request, session 
from flask.ext.login import login_user, logout_user, current_user, login_required
from passlib.hash import md5_crypt
from app import app, db, lm, models
from util import *
from views import *
from .models import User, Circos

USER = 'app/circos/usr'

#given user id, will return the assossiated object
@lm.user_loader
def user_loader(user_id):
  return User.query.get(user_id)


#display page
@app.route('/login', endpoint='login')
def login():
  return render_template('log.html', title='Login')


#display page
@app.route('/register', endpoint='register')
def register():
  return render_template('register.html', title='Registration')


#action: loging in
@app.route('/logged', methods=['GET', 'POST'], endpoint='logged')
def logged():
  email = request.form['email']
  password = request.form['password']
  #looking if good credentials
  username = User.query.filter_by(email=email).first()
  if username:
    hash = username.password
    print username 
    print hash
    print md5_crypt.verify(password, hash)
    if md5_crypt.verify(password, hash):
      registered_user = User.query.filter_by(email=email, password=hash).first()
    else:
     return redirect(url_for('error', template='home', error='Password is invalid. Please try again or register.'))
    login_user(registered_user)
    session['logged_in'] = True
    return redirect(url_for('data'))
  return redirect(url_for('error', template='home', error='Email address is invalid. Please try again or register.'))
  

#action: registering
@app.route('/registered', methods=['GET', 'POST'], endpoint='registered')
def registered():
  email = request.form['email']
  password = request.form['password']
  confirm = request.form['confirm']
  if password == confirm:
    #looking if another user already has these credentials
    if User.query.filter_by(email=email).first() is not None:
      print 'email already used'
      return redirect(url_for('error', template='register', error='This email was already used. Please try again with another email address'))
    else:
      #hashing the password
      hash = md5_crypt.encrypt(password)
      #adding new credentials to db
      user = User(email=email, password=hash)
      db.session.add(user)
      db.session.commit()

    #login new user automatically
    registered_user = User.query.filter_by(email=email, password=hash).first()
    login_user(registered_user)
    session['logged_in'] = True

    #user directory
    user = authenticate()
    print user
    directory = '%s/%s' % (USER, user)
    if not os.path.exists(directory):
      os.makedirs(directory)
    return redirect(url_for('data'))
  return redirect(url_for('error', template='register', error='Passwords do not match. Please try again'))


#action
@app.route('/logout', endpoint='logout')
def logout():
  logout_user()
  return redirect(url_for('home'))
