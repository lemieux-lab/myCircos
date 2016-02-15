import os
from app import app, db, lm, models
from create import create_celery
from util import *
from circos import *
from post_circos import *
from .models import User, Circos

process = {}

CONF = 'app/circos'
USER = 'app/circos/usr'

celery_app = create_celery(app)

@celery_app.task()
def circos(path, unique, user, type, id, host):
  print "accessing Circos-celery"
  TASK = '%s/%s/%s' % (USER, user, unique)
  ERROR = '%s/error.txt' % (TASK)
  #circos
  cmd_circos = '> process.txt; circos -conf %s -silent > %s; rm process.txt' % (path, ERROR) #using dummy method
  o,e = subprocess_cmd(cmd_circos)
  process['%s_circos' % (unique)] = o,e
  print o
  print e
  #add report to logs
  logs(unique, user)
  if os.stat(ERROR).st_size == 0:
    if user != "Guest":
      #looking for error
      if os.stat(ERROR).st_size != 0:
        send_email(unique, type, 'failure', user, host)
        files = os.listdir(TASK)
        for f in files:
	  os.remove('%s/%s' % (TASK, f))
      else:
        #zip + clean
        if 'data' in type:
        #os.remove(ERROR)
        #create circos.zip
	  zip_circos(unique, user)
        else:
          #cleaning task folder
	  files = os.listdir(TASK)
	  for f in files:
	    if ('.svg' not in f) and ('.png' not in f) and ('info.txt' not in f) and ('parse-table.conf' not in f):
	      os.remove('%s/%s' % (TASK, f))
        #save circos into db
        c = Circos(svg=unique, user_id=id)
        db.session.add(c)
        db.session.commit()
        #send notification/email to user
        send_email(unique, type, 'success', user, host)
  print "PROCESS DONE"

@celery_app.task()
def tabular_circos(to_parse, parse_table, TASK, unique, user, id, host):
  print "CELERY TASK"
  TASK = '%s/%s/%s' % (USER, user, unique)
  ERROR = '%s/error.txt' % (TASK)
  CIR_CONF = '%s/circos.conf' % (TASK)
  #parse
  print "PARSING FILES"
  cmd_table = '(cat %s | parse-table -conf %s > %s/parsed.txt) &>> %s' % (to_parse, parse_table, TASK, ERROR)
  subprocess_cmd(cmd_table)
  if os.stat(ERROR).st_size == 0:
    #make-conf
    print "MAKE FILES"
    cmd_conf = 'cat %s/parsed.txt | make-conf -dir %s' % (TASK, TASK)
    subprocess_cmd(cmd_conf)
    if os.stat(ERROR).st_size == 0:
      #circos
      print "CALLING CIRCOS"
      specific_g(unique, user)
      if os.stat(ERROR).st_size == 0:
        circos(CIR_CONF, unique, user, 'tab', id, host)
      else:
	logs(unique, user)
    else:
      logs(unique, user)
  else:
    logs(unique, user)

@celery_app.task()
def test(word): 
  print 'testing tasks', word

@celery_app.task()
def test_return(*args): 
  return args

@celery_app.task()
def add(a, b):
  r = a + b
  print r
