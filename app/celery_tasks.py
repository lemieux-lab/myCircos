from app import app
from create import create_celery
from util import *

process = {}

CONF = 'app/circos'
USER = 'app/circos/usr'

celery_app = create_celery(app)

@celery_app.task(ignore_result=False)
def circos(path, unique, user):
  #user = authenticate()
  print user
  cmd_circos = '> process.txt; circos -conf %s -silent > %s/%s/%s/error.txt; rm process.txt' % (path, USER, user, unique) #using dummy method
  o,e = subprocess_cmd(cmd_circos)
  process['%s_circos' % (unique)] = o,e
  print 'circos launched'
  #return rc

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
