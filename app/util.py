####################################################
####						####
####		      UTIL			####
####						####
####################################################
#functions most often used

import subprocess
from subprocess import Popen, PIPE
from flask.ext.login import current_user

#to execute command at the command line level
def subprocess_cmd(cmd):
  p = subprocess.Popen(cmd, shell=True, stdout = None, stderr=subprocess.STDOUT)
  return p

#user 
def authenticate():
  if current_user.is_authenticated():
    return current_user.email

#display image
def image(img):
  path = 'image/%s' % img
  return send_file(path, mimetype='image/png')

