from __future__ import division
import os, os.path
from flask import render_template, redirect, url_for, request, send_from_directory, send_file, jsonify, make_response, session, g
import requests, sys, json
import re
from flask.ext.login import login_user, logout_user, current_user, login_required
from werkzeug import secure_filename
from app import app, db, lm, models
import datetime, time, random, subprocess, collections, shutil, tarfile, zipfile
from random import randint
from subprocess import Popen, PIPE
from celery import signature
from celery.result import AsyncResult
from views_session import *
from util import *
from task import *
from upload import *
from svg import *
from circos import *
from celery_tasks import *
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
tasks = {}

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

@app.errorhandler(502)
def proxy(e):
  return render_template('502.html'), 502

@app.errorhandler(503)
def unavailable(e):
  return render_template('503.html'), 503


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
##	    TABULAR FORM	  ##
##				  ##
####################################
@app.route('/generate/tabular', endpoint='tabular')
@login_required
def tabular():
  return render_template('index_tabular.html', title='Circos-Tabular')

####################################
##				  ##
##	 HOW TO PERSONALIZE	  ##
##				  ##
####################################
@app.route('/howTo/personalize', endpoint='personalize')
@login_required
def personalize():
  return render_template('personalize.html', title='How to... Personalize')

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

  #main configuraiton file
  shutil.copy('%s/circos.conf' % (CONF), '%s/%s/%s' % (USER, user, unique))

  if request.method == 'POST':
    all_values = request.form #list of every values (no files)
    ids = track_list(all_values)
       
    #VALUES
    values.update({'karyotype': request.values['karyotype'], 'chr': request.values['chr'], 'density': request.values['density']})
    shutil.copy('%s/karyotype.%s.txt' % (KARYOTYPE, values['karyotype']), TASK)

    #writing basic information
    with open(INFO, 'a' ) as f: 
      f.write('Type: Data file(s)\nDescription: %s\n\nDate: %s\nID: %s\nKaryotype: %s\nDensity: %s\n\n' % (request.values['comments'], datetime.date.today(), unique, values['karyotype'], values['density']))
    
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
      shutil.copy('%s/%s.txt' % (CONF,values['karyotype']), TASK)
      plots['density'] = {'file': '%s.txt' % (values['karyotype']), 'type': 'histogram', 'orientation': 'in', 'r1': str(start) + 'r', 'r0': str(start - width) + 'r', 'fill_color': 'grey', 'max': 50, 'min': 0}
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
        plots[track] = {'file': track_filename, 'type': request.form[graph], 'orientation': request.form[orientation], 'r1': str(track_radius) + 'r', 'r0': str(track_radius - width) + 'r', 'fill_color': 'white'}
        track_radius = track_radius - width - pad
      else:
	return redirect(url_for('error', template='index_data', error='Track file(s) missing or with wrong extension. Please upload your files.'))    

    #generating the configuration files and the image
    generate(unique=unique, plots=plots, links=links, values=values)
    c_r = circos.delay('%s/circos.conf' % (TASK), unique, user, 'data', current_user.id, request.host_url)
    print c_r
    print "just called circos process"
    tasks[unique] = c_r
    return redirect(url_for('circos_display', type='data', unique=unique))
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
  CONF = 'app/circos'
  INFO = '%s/%s/%s/info.txt' % (USER, user, unique)
  TASK = '%s/%s/%s' % (USER, user, unique)
  CIR_CONF = '%s/%s/%s/circos.conf' % (USER, user, unique)
  
  if request.method == 'POST': 
    folder = request.files['config']
    
    if folder and allowed_file(folder.filename):
      file_upload(folder, unique)
      folder_filename = secure_filename(folder.filename)
      #path to the uploaded folder
      data = '%s/%s' % (TASK, folder_filename)

      #unpacking data
      if tarfile.is_tarfile(data):
        un_tar(data, unique)
      elif zipfile.is_zipfile(data):
        un_zip(data, unique)

      #allow interactivity
      shutil.copy('%s/svg_rule_track.conf' % (CONF), TASK)
      shutil.copy('%s/svg_rule_link.conf' % (CONF), TASK)
      file_conf = os.listdir(TASK)
      print(file_conf)
      for fc in file_conf:
        if ('.conf' in fc):
	  svg('%s/%s' % (TASK, fc))

      #look for circos.conf
      if os.path.exists(CIR_CONF):
        #writing info.txt
	with open(INFO, 'a' ) as f:
	  f.write('Type: Configuration files\nDescription: %s\n\nDate: %s\nID: %s\nZIP: %s\n\n' % (request.values['comments'], datetime.date.today(), unique, folder_filename))
	print 'specific conf'
	specific(unique)
	c_r = circos.delay(CIR_CONF, unique, user, 'conf', current_user.id, request.host_url)
        tasks[unique] = c_r
	return redirect(url_for('circos_display', type='configuration', unique=unique))
      else:
	return redirect(url_for('error', template='index_config', error='No circos.conf found. Please define your main configuration file as circos.conf.'))	      
    return redirect(url_for('error', template='index_config', error='File(s) missing or with wrong extension. Please upload your files.'))
  return redirect(url_for('error', template='index_config', error='An error occured while uploading your files. Please upload your files.'))


####################################
##				  ##
##	  GENERATE TABULAR	  ##
##				  ##
####################################
@app.route('/index_tabular', methods=['GET', 'POST'], endpoint='index_tabular')
@login_required
def index_tabular():
  unique = maintenance()
  user = authenticate()
  TASK = '%s/%s/%s' % (USER, user, unique)
  INFO = '%s/%s/%s/info.txt' % (USER, user, unique)
  parse_table = '%s/parse-table.conf' % (TASK)
  color_conf = '%s/color.conf' % (TASK)
  to_parse = '%s/to_parse.txt' % (TASK)
  circos = '%s/circos.conf' % (TASK)

  #main configuration files
  copy_dir('%s/tabular/etc' % (CONF), 'etc', '%s/%s/%s/' % (USER, user, unique))
    
  if request.method == 'POST':
    table = request.files['tabular']
    color = request.values['color']
    normal = request.values['normal']
    links = request.values['links']
    min_val = request.values['min']
    sym = request.values['sym']
    link_color = '%s/%s.conf' % (TASK, links)
    
    print links
    # sym or asym
    with open(circos, 'a') as ci:
      if sym == 'no':
        ci.write('\n<<include %s/row_col.conf>>' % (TASK))
      if sym == 'yes':
        ci.write('\n<<include %s/all.conf>>' % (TASK))
    

    #looking for value range
    if links == 'value':
      if (min_val == ''):
	return redirect(url_for('error', template='index_tabular', error='When choosing VALUE to represent your link, you need to enter a complete range. Please try again.'))   
 
    if table and allowed_file(table.filename):
      file_upload(table, unique)
      table_name = secure_filename(table.filename)
      table_path = '%s/%s' % (TASK, table_name)

      #writing info.txt
      with open(INFO, 'a' ) as f:
        f.write('Type: Tabular Visualization\nDescription: %s\n\nDate: %s\nID: %s\nTable: %s\n\n' % (request.values['comments'], datetime.date.today(), unique, table_name))
      
      #parse-table.conf
      with open(parse_table, 'a') as p:
        #normalization
        #by default, will be normalized
	p.write('normalize_contribution = %s\n' % (normal))
	p.write('use_segment_normalization = %s\n' % (normal))
	#<linkcolor>
	p.write('<<include %s/%s.conf>>\n' % (TASK, links))

      	#color.conf
      	if links == 'percentile':
	  #color
	  p.write('<<include %s/color.conf>>\n' % (TASK))
	  p.write('ribbon_variable = yes\n')
	  p.write('ribbon_variable_intra_collapse = yes\n')     
	  with open(color_conf, 'a') as c:
	    #c.write('cell_q3_color    = lgrey\n')
	    c.write('cell_q4_color    = %s\n' % (color))
	    #c.write('cell_q3_nostroke = yes\n')
	    #c.write('cell_q4_nostroke = yes\n')

	if links == 'value':
	  if sym == 'no':
	    p.write('ribbon_variable = no\n')
	    p.write('ribbon_variable_intra_collapse = no\n')
	  if sym == 'yes':
	    p.write('ribbon_variable = yes\n')
	    p.write('ribbon_variable_intra_collapse = yes\n')
  	

      #<linkcolor>
      #value.conf
      if links == 'value':
	v1 = float(min_val) / 4
	v2 = float(min_val) / 2
	#v3 = float(min_val) - 1
	v4 = float(min_val)
	#min_val = int(min_val) - 0.0001
	max_val = 10000
	print v1, v2, v4
	
	with open(link_color, 'a') as v:
	  c = 'color = '
	  t = 'transparency = 1'
	  st = 'stroke_thickness = 0'
	  v.write('%s\n%s\n' % (t, st))
	  v.write('<value %s>\n%s vvlgrey\n%s\n%s\n</value>\n' % (v1, c, t, st)) #
	  v.write('<value %s>\n%s vlgrey\n%s\n%s\n</value>\n' % (v2, c, t, st)) #
	  v.write('<value %s>\n%s lgrey\n%s\n%s\n</value>\n' % (v4, c, t, st)) #
	  #v.write('<value %s>\n%s vlgrey\n%s\n%s\n</value>\n' % (min_val, c, t, st))#, color))
	  v.write('<value %s>\n%s %s\n%s\n%s\n</value>\n' % (max_val, c, color, t, st))
	  v.write('</linkcolor>')
	 
      #segment order & color
      with open(table_path, 'r') as upload:
	uploaded = upload.readlines()
      with open(to_parse, 'a') as parse:
        n = uploaded[0].count('\t') + 1
	u = upload[0]
	print u        
	print n
        parse.write("segment_order\t")
        for x in range(1, n):
          parse.write('%s\t' % (x))
        parse.write('\n')
        parse.write("segment_color\t")
        for x in range(1, n):
          parse.write('"0,0,0"\t')
        parse.write('\n')
        for x in range(0, (n)):
	  parse.write(uploaded[x])  

      #parse table + make conf 
      c_r = tabular_circos.delay(to_parse, parse_table, TASK, unique, user, current_user.id, request.host_url)
      tasks[unique] = c_r
      return redirect(url_for('circos_display', type='tabular', unique=unique))
    return redirect(url_for('error', template='index_tabular', error='File missing or with wrong extension. Please upload your file.'))
  return redirect(url_for('error', template='index_tabular', error='An error occured while uploading your files. Please upload your files.')) 


####################################
##				  ##
##	     DISPLAY	 	  ##
##				  ##
####################################
@app.route('/circos_display/<type>/<unique>', endpoint='circos_display')
@login_required
def circos_display(type, unique):
  #print C_R.ready()
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
  print type
  return render_template('image.html', lines_info=lines_info, lines_legend=lines_legend, unique=unique, type=type, user=user)


####################################
##				  ##
##	      GET SVG	 	  ##
##				  ##
####################################
@app.route('/get_svg/<unique>/<type>', endpoint='get_svg')
@login_required
def get_svg(unique, type):
  user = authenticate()
  TASK = '%s/%s/%s' % (USER, user, unique)
  INFO = '%s/info.txt' % (TASK)
  LEGEND = '%s/legend.txt' % (TASK)
  TAB = '%s/tab.txt' % (TASK)
  ERROR = '%s/error.txt' % (TASK)
  SVG = '%s/circos_%s.svg' % (TASK, unique)
  PNG = '%s/circos_%s.png' % (TASK, unique)
  CIR_CONF = '%s/circos.conf' % (TASK)
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
    #look if task is complete
    results = circos.AsyncResult(tasks[unique].id)
    print results.ready()
    if not results.ready(): #process not completed
      return content

    elif results.ready():
      #print 'looking for error in circos'
      #look for any error
      #with open(ERROR, 'r') as f:
	#line = f.readline()
        #for line in f:
          #if '*** CIRCOS ERROR ***' in line:
            #content = 'error'
            #print 'an error was found'
	    #return content
      #print 'no error'
    
      if os.path.isfile(SVG): 
       #file_ready(SVG)
       content = open(SVG).read()
       return content
      else:
        content = 'error'
        return content

####################################
##				  ##
##	      GENE INFO	 	  ##
##				  ##
####################################
@app.route('/gene_info/<c>/<s>/<e>/<species>', methods=['GET', 'POST'], endpoint='gene_info')
@login_required
def gene_info(c, s, e, species):
  #print c, s, e
  server = "http://rest.ensembl.org"
  
  #get mapped start and end of gene (if position relate to gene)
  ext1 = "//map/" + species + "/GRCh37/" + str(c) + ":" + str(s) + ".." + str(e) + ":1/GRCh38?"
  r1 = requests.get(server + ext1, headers = {"Content-Type" : "application/json"})
  if not r1.ok:
    r1.raise_for_status()
    sys.exit()
  i1 = r1.json()
  if i1 == []:
    print "This position does not correspond to a gene"
    i = "This position does not correspond to a gene"
    return i
  else:
    ms = i1["mappings"][0]["mapped"]["start"]
    me = i1["mappings"][0]["mapped"]["end"]
    #print ms, me

  #get external name
  ext2 = "/overlap/region/" + species + "/" + str(c) + ":" + str(ms) + "-" + str(me) + "?feature=gene"
  r2 = requests.get(server + ext2, headers = {"Content-Type" : "application/json"})
  if not r2.ok:
    r2.raise_for_status()
    sys.exit()
  i2 = r2.json()
  if i2 == []:
    print "This position does not correspond to a gene"
    i = "This position does not correspond to a gene"
    return i
  else: 
    #n = ["Name", "ID", "Biotype", "Description"] #parameters name
    i = [i2[0]["external_name"], i2[0]["gene_id"], i2[0]["biotype"], i2[0]["description"]] #gene info
    i = json.dumps(i) #gene info
    #i = json.dumps([i2[0][3], i2[0][9], i2[0][14], i2[0][12]]) #gene info
    #print n
    #print i
    return i
    #n = i2[0]["external_name"]
    #i = i2[0]["gene_id"]
    #b = i2[0]["biotype"]
    #d = i2[0]["description"]
    #return n, i, b, d

####################################
##				  ##
##	      DOWNLOAD	 	  ##
##				  ##
####################################
# h = highlights
# f = file
@app.route('/download/<unique>/<to_download>', endpoint='download')
@login_required
def download(unique, to_download):
  user = authenticate()
  TASK = '%s/%s/%s' % (USER, user, unique)
  if ".svg" in to_download:
    name = "%s.svg" % (unique)
  elif ".zip" in to_download:
    name = "%s.zip" % (unique)

  content = open('%s/%s' % (TASK, to_download)).read()
  response = make_response(content)
  response.headers["content-Type"] = "application/octet-stream" 
  response.headers["content-Disposition"] = "attachment; filename = %s" % (name)
  return response

@app.route('/download_highlights/<unique>', methods=['POST'], endpoint='download_highlights')
@login_required
def download_highlights(unique):
  print 'step 1'
  print unique
  _data = request.values['data']
  print 'step 2'
  #content = _data.read()
  response = make_response(_data)
  print 'step 3'
  response.headers["content-Type"] = "application/octet-stream" 
  response.headers["content-Disposition"] = "attachment; filename = %s.svg" % (unique) 
  print "download this svg"
  return response

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
  print 'deleting'
  print unique
  
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
  user = authenticate()
  print "mycircos"
  #list of every circos and their type
  c_lst = []
  #get user_id
  if current_user.is_authenticated():
    user_id = current_user.id
    print user_id
    #get every circos id
    c_all = Circos.query.filter_by(user_id=user_id).all()
    c_ord = list(reversed(c_all))
    print c_ord
    for c in c_ord:
      #get some info assossiated with the id
      with open('%s/%s/%s/info.txt' % (USER, user, c), 'r') as i:
        lines = i.readlines()
	for l in lines:
	  if 'Type:' in l:
	    type = l[6:]
	    tup = (c, type)
          if 'ZIP:' in l:
	    zip = l[5:]
	    tup = tup + (zip,)
	  if 'Description:' in l:
	    description = l[13:]
	    tup = tup + (description,)
	  if 'Date:' in l:
	    date = l[6:]
	    tup = tup + (date,)
        c_lst.append(tup)
    print c_lst
    return render_template('mycircos.html', title='MyCircos', c_lst=c_lst, user=user)


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




  





