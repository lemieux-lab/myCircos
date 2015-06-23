from __future__ import division
import os, os.path
from flask import render_template, redirect, url_for, request, send_from_directory, send_file, jsonify, make_response, session, g
import requests 
from flask.ext.login import login_user, logout_user, current_user, login_required
from werkzeug import secure_filename
from app import app, db, lm, models
import datetime, time, random, subprocess, collections, shutil, tarfile, zipfile
from random import randint
from subprocess import Popen, PIPE
from views_session import *
from util import *
from task import *
from upload import *
from circos import *
from display import *
from post_circos import *
from .models import User, Circos


####################################################
####						####
####		      VARIABLES			####
####						####
####################################################
#dictionary for running processes
process = {}

#paths
CONF = 'app/circos'
USER = 'app/circos/usr'


####################################################
####						####
####		      ERRORS			####
####						####
####################################################
@app.errorhandler(401)
def unauthorized(e):
  return render_template('401.html'), 401

@app.errorhandler(404)
def not_found(e):
  return render_template('404.html'), 404


####################################################
####						####
####		    VIEWS			####
####						####
####################################################
####################################
##				  ##
##	  ERROR HANDLING 	  ##
##				  ##
####################################
@app.route('/error/<template>/<error>', endpoint='error')
def error(template, error):
  return render_template('%s.html' % (template), title='Error', error=error)


####################################
##				  ##
##	    HOME PAGE	 	  ##
##				  ##
####################################
#first page when accessing interface, after login/registration 
@app.route('/', endpoint='home')
def home():
  return render_template('home.html', title='Home')


####################################
##				  ##
##	   IMAGE	 	  ##
##				  ##
####################################
@app.route('/image/<img>', endpoint='image')
def image(img):
  path = 'image/%s' % img
  return send_file(path, mimetype='image/png')


####################################
##				  ##
##	    DATA FORM	 	  ##
##				  ##
####################################
@app.route('/generate/data/', endpoint='data')
@login_required
def data():
  return render_template('index_data.html', title='Circos-Data')


####################################
##				  ##
##	    CONF FORM	 	  ##
##				  ##
####################################
@app.route('/generate/config', endpoint='config')
@login_required
def config():
  return render_template('index_config.html', title='Circos-Config')


####################################
##				  ##
##	  GENERATE DATA	 	  ##
##				  ##
####################################
@app.route('/index_data', methods=['GET', 'POST'], endpoint='index_data')
@login_required
def index_data():
  unique = maintenance()
  user = authenticate()
  TASK = '%s/%s/%s' % (USER, user, unique)
  KARYOTYPE = 'app/circos/karyotypes'
  INFO = '%s/%s/%s/info.txt' % (USER, user, unique)
  LEGEND = '%s/%s/%s/legend.txt' % (USER, user, unique)

  #dictionaries
  plots = collections.OrderedDict()
  links = collections.OrderedDict()
  values = {}

  if request.method == 'POST':
    all_values = request.form #list of every values (no files)
    ids = track_list(all_values)
       
    #VALUES
    values.update({'karyotype': request.values['karyotype'], 'chr': request.values['chr'], 'density': request.values['density']})
    shutil.copy('%s/karyotype.%s.txt' % (KARYOTYPE, values['karyotype']), TASK)

    #writing basic information
    with open(INFO, 'a' ) as f: 
      f.write('Type: from data files\n\nDate: %s\nID: %s\nKaryotype: %s\nDensity: %s\nDescription: %s\n\n' % (datetime.date.today(), unique, values['karyotype'], values['density'], request.values['comments']))
    
    links_file = request.files['links_file'] #get the links file by its name

    #RADIUS
    start = 0.999
    center = 0.20
    center_links = 0.60
    #n_tracks
    if values['density'] == 'no':
      t = 1
      n_track = len(ids)
    else:
      t = 2
      n_track = len(ids) + 1.0
    #track width
    if links_file:
      width = 0.08
    else: 
      width = 0.15
    #track padding
    if not n_track is 0:
      if links_file:
        pad = (start - center_links - (n_track * width)) / n_track
      else:
        pad = (start - center - (n_track * width)) / n_track
    else:
      pad = 0.0
    #links radius
    link_radius = start - ((n_track * width) + ((n_track - 1) * pad))  
    r = str(link_radius) + 'r'
    
    #LINKS
    #writing information about links
    if links_file: 
      if allowed_file(links_file.filename):
	file_upload(links_file, unique)
        links_filename = secure_filename(links_file.filename)
        if request.values['links']:
	  links_name = request.values['links'] 
	else:
	  links_name = 'no name'
	#writing info.txt
        with open(INFO, 'a' ) as f:
	  f.write('%s: %s\n\n' % (links_name, links_filename))
        #writing legend.txt
        with open(LEGEND, 'a' ) as l:
          l.write('Links: %s\n\n' % (links_name))
	#links dictionary
	links[links_name] = {'file': links_filename, 'bezier_radius': '0.1r', 'radius': r}
      else:
        return redirect(url_for('error', template='index_data', error='Links file with wrong extension. Please upload your files.'))
    
    #TRACKS
    #density track
    if values['density'] == 'yes':
      track_radius = start - width - pad
      #writing info.txt
      with open('%s/legend.txt' % (TASK), 'a' ) as l:
        l.write('Track 1: Gene Density\n')
      shutil.copy('%s/gene_density.txt' % (CONF), TASK)
      plots['density'] = {'file': 'gene_density.txt', 'type': 'histogram', 'orientation': 'in', 'r1': str(start) + 'r', 'r0': str(start - width) + 'r', 'fill_color': 'grey'}
    else:
      track_radius = start
    #label track
    labels_file = request.files['labels_file'] #get the labelss file by its name
    if labels_file: 
      if allowed_file(labels_file.filename):
	file_upload(labels_file, unique)
        labels_filename = secure_filename(labels_file.filename)
	plots['labels'] = {'file': labels_filename, 'type': 'text', 'r1': '1r + 525p', 'r0': '1r', 'label_font': 'default', 'label_size': '24p', 'show_links': 'yes', 'link_dims': '0p,0p,70p,0p,10p', 'link_thickness': '2p', 'link_color': 'red'}
      else:
	  return redirect(url_for('error', template='index_data', error='Labels file with wrong extension. Please upload your files.'))
    #for every uploaded track
    for i in ids:
      track_file_id = 'file%s' % (i) 
      track_file = request.files[track_file_id] 
      #checking that file does exist and have the right extension i.e .txt
      if track_file and allowed_file(track_file.filename): 
	file_upload(track_file, unique)
        track = 'track%s' % (i) 
        graph = 'graph%s' % (i)
        orientation = 'orientation%s' % (i) 
        track_name = 'name%s' % (i)
        track_filename = secure_filename(track_file.filename)
        #track_title 
	if request.values[track_name]:
	  track_title = request.values[track_name]
	else:
          track_title = 'no name' 
        #writing info.txt
        with open(INFO, 'a' ) as f:
	  f.write('%s: %s\n' % (track_title, track_filename))
        #writing legend.txt
        with open('%s/legend.txt' % (TASK), 'a' ) as l:
          l.write('Track %s: %s\n' % (t, track_title))
          t = t + 1
        #plots dictionary
        plots[track] = {'file': track_filename, 'type': request.form[graph], 'orientation': request.form[orientation], 'r1': str(track_radius) + 'r', 'r0': str(track_radius - width) + 'r'}
        track_radius = track_radius - width - pad
      else:
	return redirect(url_for('error', template='index_data', error='Track file(s) missing or with wrong extension. Please upload your files.'))    

    #generating the configuration files and the image
    generate(unique=unique, plots=plots, links=links, values=values)
    circos('%s/circos.conf' % (TASK), unique) 
    return redirect(url_for('circos_display', unique=unique))
  return redirect(url_for('error', template='index_data', error='An error occured while loading your file(s). Please try again'))
   

####################################
##				  ##
##	  GENERATE CONF	 	  ##
##				  ##
####################################
@app.route('/index_config', methods=['GET', 'POST'], endpoint='index_config')
@login_required
def index_config():
  unique = maintenance()
  user = authenticate()
  INFO = '%s/%s/%s/info.txt' % (USER, user, unique)
  DATA = '%s/%s/%s/data' % (USER, user, unique)
  CIR_CONF = '%s/%s/%s/data/circos.conf' % (USER, user, unique)
  
  if request.method == 'POST': 
    folder = request.files['config']
    
    if folder and allowed_file(folder.filename):
      file_upload(folder, unique)
      folder_filename = secure_filename(folder.filename)
      #path to the uploaded folder
      data = '%s/%s' % (DATA, folder_filename)

      #unpacking data
      if tarfile.is_tarfile(data):
        un_tar(data, unique)
      elif zipfile.is_zipfile(data):
        un_zip(data, unique)

      #look for circos.conf
      if os.path.exists(CIR_CONF):
	specific(unique)
	circos(CIR_CONF, unique)
	#writing info.txt
	with open(INFO, 'a' ) as f:
	  f.write('Type: from configuration files\n\nDate: %s\nID: %s\nDescription: %s\n\n' % (datetime.date.today(), unique, request.values['comments']))
        return redirect(url_for('circos_display', unique=unique))
      else:
	return redirect(url_for('error', template='index_config', error='No circos.conf found. Please define your main configuration file as circos.conf.'))	      
    return redirect(url_for('error', template='index_config', error='File(s) missing or with wrong extension. Please upload your files.'))
  return redirect(url_for('error', template='index_config', error='An error occured while uploading your files. Please upload your files.'))


####################################
##				  ##
##	     DISPLAY	 	  ##
##				  ##
####################################
@app.route('/circos_display/<unique>', endpoint='circos_display')
@login_required
def circos_display(unique):
  user = authenticate()
  LEGEND = '%s/%s/%s/legend.txt' % (USER, user, unique)
  TASK = '%s/%s/%s' % (USER, user, unique)

  #info to show in details box
  lines_info = info(unique)
  #info to show in legend box
  if os.path.exists(LEGEND):
    lines_legend = legend(unique)
  else:
    lines_legend = []
  #look if circos.zip can be downloaded
  files = os.listdir(TASK)
  return render_template('image.html', lines_info=lines_info, lines_legend=lines_legend, unique=unique, files=files)


####################################
##				  ##
##	      GET SVG	 	  ##
##				  ##
####################################
@app.route('/get_svg/<unique>', endpoint='get_svg')
@login_required
def get_svg(unique):
  user = authenticate()
  TASK = '%s/%s/%s' % (USER, user, unique)
  DATA = '%s/%s/%s/data' % (USER, user, unique)
  SVG = '%s/%s/%s/circos_%s.svg' % (USER, user, unique, unique)
  PNG = '%s/%s/%s/circos_%s.png' % (USER, user, unique,unique)
  content = '' 

  #previous circos
  if os.path.isfile(SVG) and not Circos.query.filter_by(svg=unique).first() is None:
    print 'getting previous circos'
    print Circos.query.filter_by(svg=unique).first()
    content = open(SVG).read()
    return content

  #current circos
  else:
    print 'getting current circos'
    p = process.get('%s_circos' % (unique), 'None')
    if os.path.isfile('process.txt'): #if file is there, then circos is still running
      return content

    else:
      print 'looking for error in circos'
      #look for any error
      error = '%s/error.txt' % (TASK)
      file_ready(error)
      logs(unique)
      with open(error, 'r') as f:
        for line in f:
          if '*** CIRCOS ERROR ***' in line:
            content = 'error'
            print 'an error was found'
	    return content
      print 'no error'
    
      if os.path.isfile(SVG): 
       file_ready(SVG)
       content = open(SVG).read()
       #copy files into task folder
       if os.path.exists('%s/specific.conf' % (DATA)):
         shutil.copy('%s/specific.conf' % (DATA), TASK)
       #erase tmp 
       shutil.rmtree(DATA)
       #create circos.zip
       zip_circos(unique)
       #save circos into db
       if current_user.is_authenticated():
         circos = Circos(svg='%s' % (unique), user_id=current_user.id)
         db.session.add(circos)
         db.session.commit()
       #send notification/email to user
       send_email(unique) 
       return content

####################################
##				  ##
##	      DOWNLOAD	 	  ##
##				  ##
####################################
@app.route('/download/<unique>/<file>', endpoint='download')
@login_required
def download(unique, to_download):
  user = authenticate()
  TASK = '%s/%s/%s' % (USER, user, unique)

  try:
    content = open('%s/%s' % (TASK, to_download)).read()
    response = make_response(content)
    response.headers["content-Type"] = "application/octet-stream" 
    response.headers["content-Disposition"] = "attachment; filename = %s" % (to_download)
    return response
  except Exception, e:
    print 'There was an error while downloading ' + to_download + ': ' + e
    return render_template('mycircos.html')


####################################
##				  ##
##	      DELETE	 	  ##
##				  ##
####################################
@app.route('/delete/<unique>', endpoint='delete')
@login_required
def delete(unique):
  user = authenticate()
  TASK = '%s/%s/%s' % (USER, user, unique)

  if current_user.is_authenticated():
    c = Circos.query.filter_by(svg=unique).first()
    #delete in db
    db.session.delete(c)
    db.session.commit()
    #delete task folder
    shutil.rmtree(TASK)
    return redirect(url_for('mycircos'))


####################################
##				  ##
##	    DELETE_ALL	 	  ##
##				  ##
####################################
@app.route('/delete_all', endpoint='delete_all')
@login_required
def delete_all():
  user = authenticate()
  ALL_TASK = '%s/%s' % (USER, user)

  if current_user.is_authenticated():
    circos = Circos.query.filter_by(user_id=current_user.id).all()
    for c in circos:
      db.session.delete(c)
      shutil.rmtree('%s/%s' % (ALL_TASK, c))
    db.session.commit()
  return redirect(url_for('data'))


####################################
##				  ##
##	      MYCIRCOS	 	  ##
##				  ##
####################################
@app.route('/mycircos', endpoint='mycircos')
@login_required
def mycircos():
  #get user_id
  if current_user.is_authenticated():
    user_id = current_user.id
    c_all = Circos.query.filter_by(user_id=user_id).all()
    return render_template('mycircos.html', title='MyCircos', c_all=c_all)


####################################
##				  ##
##	      GET PNG	 	  ##
##				  ##
####################################
@app.route('/get_png/<unique>', endpoint='get_png')
@login_required
def get_png(unique):
  user = authenticate()
  directory = 'circos/usr/%s/%s' % (user, unique)
  return send_file('%s/circos_%s.png' % (directory, unique), mimetype='image/png')




  





