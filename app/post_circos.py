####################################################
####						####
####		      POST-CIRCOS		####
####						####
####################################################
#functions used after generating a Circos and before displaying it

import os, os.path
import datetime, time, shutil, tarfile, zipfile, stat
import smtplib
from flask import request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from util import *

USER = 'app/circos/usr'

#make a zip file 
def zip_circos(unique):
  print 'making zip file'
  user = authenticate()
 
  zip_file = zipfile.ZipFile('%s/%s/%s/circos_%s.zip' % (USER, user, unique, unique), "w")
  task_folder = '%s/%s/%s' % (USER, user, unique)
  files = os.listdir(task_folder)
  for f in files:
    if '.conf' in f or 'gene_density' in f or 'karyotype' in f:
      zip_file.write('%s/%s/%s/%s' % (USER, user, unique, f), f)
      os.remove('%s/%s/%s/%s' % (USER, user, unique, f)) 
  zip_file.close() 

#adding to logs.txt
def logs(unique):
  print 'adding report to logs.txt'
  user = authenticate()
  with open("%s/%s/%s/error.txt" % (USER, user, unique)) as f:
      with open("logs.txt", "a") as f1:
        f1.write('%s\t\t' % (datetime.date.today()))
        f1.write('%s\t' % (unique))
        for line in f:
            f1.write('%s .*. ' % (line)) 
        f1.write('\n')

#sending notification to the user
def send_email(unique):
  print 'sending email'
  no_reply = 'circos@binfo09.iric.ca'
  user = authenticate()
  host = request.host_url
  print host
  
  msg = MIMEMultipart()

  msg['Subject'] = 'Your Circos'
  msg['From'] = no_reply
  msg['To'] = user

  message = 'Your Circos has been generated.\n\nYou can view it by clicking on the link: %scircos_display/%s' % (host, unique)
  msg.attach(MIMEText(message, 'plain'))

  try:
    s = smtplib.SMTP('localhost')
    s.sendmail(no_reply, [user], msg.as_string())
    s.quit()
    print 'Email successfully sent'
  except Exception, e:
    print 'Error: unable to send email to ' + user
