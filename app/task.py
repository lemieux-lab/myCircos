####################################################
####						####
####		      Task			####
####						####
####################################################
#functions used when a new task is generated

import os, os.path
import datetime, time, random, shutil, stat
from random import randint
from util import *
from .models import User, Circos


USER = 'app/circos/usr'
CONF = 'app/circos'

#every time when clicking 'generate'
def maintenance():
  print 'starting maintenance'
  user = authenticate()
  #generating a unique ID for the present task/circos
  unique = unique_ID()
  #get rid of 'error folders'
  user_folder = '%s/%s' % (USER, user)
  folders = os.listdir(user_folder)
  for folder in folders:
    task_data = os.listdir('%s/%s/%s' % (USER, user, folder))
    if 'circos_%s.png' % (folder) not in task_data:
      shutil.rmtree('%s/%s/%s' % (USER, user, folder), onerror=force_delete) 

      #removing id from bd if it's there   ## not used for now
      u = db.session.query(User).filter_by(email=user).first()
      c = db.session.query(Circos).filter_by(user_id=u.id, svg=folder).first()
      if c : 
        db.session.delete(c)
        db.session.commit()
  
  #generate task's repository ---> info.txt, specific.conf, circos_<unique>.svg
  directory = '%s/%s/%s' % (USER, user, unique)
  if not os.path.exists(directory):
    os.makedirs(directory)
  else:
    maintenance()
  print 'maintenance finished'
  return unique

def force_delete(func, path, excinfo):
  os.chmod(path, stat.S_IWRITE)
  func(path)

#creating unique id for circos (how we can trace back the image in the future)
def unique_ID():
  now = datetime.datetime.now()
  today = datetime.date.today()
  r = randint(1000, 5000) 
  unique = '%s_%s_%s' % (now.microsecond, today.toordinal(), r)
  return unique
