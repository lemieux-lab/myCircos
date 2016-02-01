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
  "lauching circos"
  cmd_circos = '> process.txt; circos -conf %s -silent > %s; rm process.txt' % (path, ERROR) #using dummy method
  o,e = subprocess_cmd(cmd_circos)
  process['%s_circos' % (unique)] = o,e
  #add report to logs
  logs(unique, user)
  if user != "Guest":
    #looking for error
    with open(ERROR, 'r') as e:
      lines = e.readlines()
      if (lines) and ('*** CIRCOS ERROR ***' in lines[1]):
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
  TASK = '%s/%s/%s' % (USER, user, unique)
  ERROR = '%s/error.txt' % (TASK)
  CIR_CONF = '%s/circos.conf' % (TASK)
  #parse
  cmd_table = 'cat %s | parse-table -conf %s > %s/parsed.txt' % (to_parse, parse_table, TASK)
  subprocess_cmd(cmd_table)
  #make-conf
  cmd_conf = 'cat %s/parsed.txt | make-conf -dir %s' % (TASK, TASK, TASK)
  subprocess_cmd(cmd_conf)
  #circos
  specific(unique)
  circos(CIR_CONF, unique, user, 'tab', id, host)

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
