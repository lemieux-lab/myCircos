####################################################
####						####
####		    VIEWS SESSION		####
####						####
####################################################

import os, os.path
from flask import render_template, redirect, url_for, request, session 
from flask.ext.login import login_user, logout_user, current_user, login_required
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
  registered_user = User.query.filter_by(email=email, password=password).first()
  
  if registered_user is None:
    return redirect(url_for('error', template='home', error='Email address or Password is invalid. Please try again or register.'))
  login_user(registered_user)
  session['logged_in'] = True
  return redirect(url_for('data'))
  

#action: registering
@app.route('/registered', methods=['GET', 'POST'], endpoint='registered')
def registered():
  email = request.form['email']
  password = request.form['password']
  confirm = request.form['confirm']
  if password == confirm:
    #looking if another user already has these credentials
    if User.query.filter_by(email=email).first() is not None or User.query.filter_by(password=password).first() is not None:
      return redirect(url_for('error', template='register', error='Someone already has these credentials. Please use another email and/or password'))
    else:
      user = User(email=email, password=password)
      db.session.add(user)
      db.session.commit()

    #login new user automatically
    registered_user = User.query.filter_by(email=email, password=password).first()
    login_user(registered_user)
    session['logged_in'] = True

    #user directory
    user = authenticate()
    print user
    directory = '%s/%s' % (USER, user)
    if not os.path.exists(directory):
      os.makedirs(directory)
    return redirect(url_for('data'))
  return redirect(url_for('error', template='register', error='Passwords do not match. Please fill in the registration form.'))


#action
@app.route('/logout', endpoint='logout')
def logout():
  logout_user()
  return redirect(url_for('home'))
