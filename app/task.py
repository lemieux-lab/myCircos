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
  #generate task's repository ---> info.txt, specific.conf, circos_<unique>.svg
  directory = '%s/%s/%s' % (USER, user, unique)
  if not os.path.exists(directory):
    os.makedirs(directory)
    #tmp
    tmp_data = '%s/%s/%s/data' % (USER, user, unique)
    tmp_image = '%s/%s/%s/image' % (USER, user, unique)
    os.makedirs(tmp_data)
    os.makedirs(tmp_image)
    shutil.copy('%s/standard.conf' % (CONF), '%s/%s/%s' % (USER, user, unique))
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
