#!flask/bin/python

import sys
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app import app 

print "looking if circos is running properly"
cmd = 'circos'
o,e = subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()

error_string_en = 'ommand not found'
error_string_fr = 'ommande introuvable'
if error_string_en in o or error_string_en in e or error_string_fr in o or error_string_fr in e:  
  print 'Command not found', 
  print str(o)
  print str(e)

  no_reply = 'mycircos@iric.ca'
  user = 'mycircos@iric.ca'
  msg = MIMEMultipart()

  msg['Subject'] = 'ERROR'
  msg['From'] = no_reply
  msg['To'] = 'Admin'

  message = 'An error occured while lauching myCircos and the app is currently not running. \n %s \n %s' % (str(o), str(e))
  msg.attach(MIMEText(message, 'plain'))

  try:
    s = smtplib.SMTP('localhost')
    s.sendmail(no_reply, [user], msg.as_string())
    s.quit()
    print 'Email successfully sent'
  except Exception, e:
    print 'Error: unable to send email to ' + user
    print e

  sys.exit(0)

app.run(debug = True, host='0.0.0.0', port=8099)
