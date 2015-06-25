####################################################
####						####
####		      CIRCOS			####
####						####
####################################################
#functions used when generating a Circos

import os, os.path
import shutil
from util import *

process = {}

CONF = 'app/circos'
USER = 'app/circos/usr'


########## BOTH #################
#run circos
def circos(path, unique):
  print 'circos launched'
  user = authenticate()
  cmd_circos = '> process.txt; circos -conf %s -silent > %s/%s/%s/error.txt; rm process.txt' % (path, USER, user, unique) #using dummy method
  p = subprocess_cmd(cmd_circos)
  process['%s_circos' % (unique)] = p



########## FROM DATA ############
#list of all tracks to be displayed that we uploaded
def track_list(all_values):
  #IDs
  ids = sorted([int(val[4:]) for val in all_values if 'name' in val])
  return ids


#function generating specific.conf file 
def generate(unique, plots, links, values):
  print 'starting generate'
  user = authenticate()

  #name of .svg file: circos_unique.svg
  with open('%s/%s/%s/specific.conf' % (USER, user, unique), 'a' ) as f:
    f.write('file*=circos_%s.svg\n' % (unique))
    f.write('dir* = %s/%s/%s\n\n' % (USER, user, unique)) 
 
    #selectioning the appropriate karyotype: homo sapiens (default) or mouse 
    if values['karyotype'] == 'mm': 
      f.write('karyotype* = karyotype.mm.txt\n')

    #specific chromosome display
    if values['chr'] == '':
      f.write('chromosomes_display_default* = yes\n\n')
    else:
      f.write('chromosomes_display_default* = no \nchromosomes* = %s\n\n' % (values['chr']))

    #plots
    if plots:
     shutil.copy('%s/plots.conf' % (CONF), '%s/%s/%s' % (USER, user, unique))
     shutil.copy('%s/axis.conf' % (CONF), '%s/%s/%s' % (USER, user, unique))
     #graphical representation 
     f.write('<plots>\n')
     f.write('<<include plots.conf>>\n')
     for k,v in plots.items():
       f.write('<plot>\n')
       for sk, sv in v.items():
         f.write('%s = %s\n' % (sk, sv))
         if 'histogram' in sv or 'scatter' in sv:
           f.write('<<include axis.conf>>\n')
       f.write('</plot>\n\n')
     f.write('</plots>\n\n')

    #links 
    if links:
      f.write('<links>\n')
      for k,v in links.items():
        f.write('<link>\n')
        for sk, sv in v.items():
          f.write('%s = %s\n' % (sk, sv))
        f.write('</link>\n\n')
      f.write('</links>\n\n')
  print 'generate finished'


########## FROM CONFIG ##########
#specificy location and name of svg file
def specific(unique):
  print 'starting specific'
  user = authenticate()
  with open('%s/%s/%s/circos.conf' % (USER, user, unique), 'a' ) as f:
    #name of the generated svg image
    f.write('file** = circos_%s.svg\n' % (unique))
    #location of the generated svg image
    f.write('dir** = %s/%s/%s\n' % (USER, user, unique))
    #no png generated: only svg
    f.write('png* = yes\nsvg* = yes\n')
  print 'specific finished'
