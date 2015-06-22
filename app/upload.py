####################################################
####						####
####		      UPLOAD			####
####						####
####################################################
#functions used when uploading user files

import os, os.path
from werkzeug import secure_filename
import tarfile, zipfile
from util import *

ALLOWED_EXTENSIONS = set(['txt', 'tar', 'zip'])
USER = 'app/circos/usr'

#check if extension is valid
def allowed_file(filename):
  return '.' in filename and \
      filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

#secure upload user files
def file_upload(file, unique):
  user = authenticate()
  filename = secure_filename(file.filename)
  file.save(os.path.join('%s/%s/%s/data' % (USER, user, unique), filename))

#unpacking .tar
def un_tar(data, unique):
  print 'unpacking tar folder'
  user = authenticate()
  t = tarfile.open(data, 'r')
  t.extractall('%s/%s/%s/data' % (USER, user, unique))

#unpacking .zip
def un_zip(data, unique):
  print 'unpacking zip folder'
  user = authenticate()
  z = zipfile.ZipFile(data, "r") 
  z.extractall('%s/%s/%s/data' % (USER, user, unique))
