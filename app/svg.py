# function reads configuration file to find <plot>
# if found, adds 'svgdata-' parameters
# allows interactivity 

import re

def svg(f):
  s = '<rules>\n'
  e = '</rules>\n'

  track = '<<include svg_rule_track.conf>>\n'
  link = '<<include svg_rule_link.conf>>\n' 
  
  #c = 0
  p = []
  r = []
  l = []

  #looking for <plot>
  for i, line in enumerate(open(f)):
    for match in re.finditer('<plot>|</plot>', line):
      #c = c + 1
      p.append(i+1)
    for match in re.finditer('<link>|</link>', line):
      l.append(i+1)
  
  if (len(p) != 0) or (len(l) != 0):
    print 'There are some plots/links'
    for i, line in enumerate(open(f)):
      for match in re.finditer('<rules>', line):
        r.append(i+1)

  print "p: %s" % (p)
  print "l: %s" % (l)
  print "r: %s" % (r)
  
  with open(f, 'r') as conf:
    lines = conf.readlines()

  if (len(r) == 0):
    for y in range(0, len(p), 2):
      lines[p[y]] = '%s%s%s%s' % (s, track, e, lines[p[y]])
    for y in range(0, len(l), 2):
      lines[l[y]] = '%s%s%s%s' % (s, link, e, lines[l[y]])
  else:
    if (p):
      for i in range(0, (len(p) - len(r))):
	r.append(0)
      for y in range(0, len(p), 2): #line of <plot> ---- y+1 is line of </plot>
	for x in range(0, len(r)): #line of <rules>
	  if (r[x] > p[y]) and (r[x] < p[y+1]):
	    lines[r[x]] = '%s%s' % (track, lines[r[x]])
	    print 'there is a rule at line %s between <plot> %s, %s' % (r[x], p[y], p[y+1])
	    del r[x]
            print r
	    break
	  else:
	    print('there is no rule between <plot> %s, %s' % (p[y], p[y+1]))
	    lines[p[y]] = '%s%s%s%s' % (s, track, e, lines[p[y]])
	    break
    if (l):
      for i in range(0, (len(l) - len(r))):
	r.append(0)
      for y in range(0, len(l), 2): #line of <link> ---- y+1 is line of </plot>
	for x in range(0, len(r)): #line of <rules>
	  if (r[x] > l[y]) and (r[x] < l[y+1]):
            print 'there is a rule at line %s between <link> %s, %s' % (r[x], l[y], l[y+1])
	    lines[r[x]] = '%s%s' % (link, lines[r[x]])
	    del r[x]
	    print r
	    break
	  else:
	    print('there is no rule between <link> %s, %s' % (l[y], l[y+1]))
	    lines[l[y]] = '%s%s%s%s' % (s, link, e, lines[l[y]])
	    break
  
  with open(f, 'w') as conf:
    for i in range(0, len(lines)):
      conf.write(lines[i])
