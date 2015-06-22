####################################################
####						####
####		      DISPLAY			####
####						####
####################################################
#functions used when displaying a Circos

import os, os.path
import time
from util import *

USER = 'app/circos/usr'

#get parameters values from info.txt
def info(unique):
  user = authenticate()
  info = '%s/%s/%s/info.txt' % (USER, user, unique)
  with open(info, 'r') as i:
    lines_info = i.readlines()
    return lines_info

#get parameters values from legend.txt
def legend(unique):
  user = authenticate()
  legend = '%s/%s/%s/legend.txt' % (USER, user, unique)
  with open(legend, 'r') as i:
    lines_legend = i.readlines()
    return lines_legend

#look svg size changes
def file_ready(svg_file):
  print 'looking if svg is ready'
  prev = 0
  x = True
  while (x):
    time.sleep(3)
    current = os.path.getsize(svg_file)
    if prev == current:
      break
    else:
      prev = current
  print 'ready'
  return 'updated'


