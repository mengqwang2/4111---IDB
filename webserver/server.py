#!/usr/bin/env python2.7

"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@w4111a.eastus.cloudapp.azure.com/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@w4111a.eastus.cloudapp.azure.com/proj1part2"
#
#DATABASEURI = "postgresql://mw3061:3591@w4111a.eastus.cloudapp.azure.com/proj1part2"
DATABASEURI = "postgresql://mw3061:3591@w4111vm.eastus.cloudapp.azure.com/w4111"

#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
'''
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
'''

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  #print request.args


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM test")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
  return render_template("another.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test VALUES (NULL, ?)', name)
  return redirect('/')


@app.route('/login', methods=['POST'])
def login():
    userid = str(request.form['ID'])
    password = str(request.form['Password'])
    role = str(request.form['role'])
    stmt = ""
    if role=="student":
      stmt = "SELECT pwd FROM Student_Login WHERE sid=" + "'" + str(userid) + "'"
    if role=="professor":
      stmt = "SELECT pwd FROM Professor_Login WHERE pid=" + "'" + str(userid) + "'"
    try:
      cursor = g.conn.execute(stmt)
    except:
      return render_template("error.html")
    for result in cursor:
      if(str(result[0])==password):
        session['uid'] = userid
        session['role'] = role
        cursor.close()

        if role=="student":
          # fetch schedule
          stmt = "SELECT Course.cid, Course.cname, Course.time, Location.building, Location.classroom FROM Course, Student_enroll_course, Location WHERE " + "'" + str(userid) + "'" + "= Student_enroll_course.sid AND Student_enroll_course.cid = Course.cid AND Location.lid = Course.lid"
          try:
            cursor1 = g.conn.execute(stmt)
          except:
            return render_template("error.html")
          std_course = []
          for result1 in cursor1:
            std_course.append(result1)
          cursor1.close()
          
          context = dict(std_course = std_course)
          return render_template("schedule.html", **context)
        else:
          # fetch schedule
          stmt = "SELECT Course.cid, Course.cname, Course.time, Location.building, Location.classroom FROM Course, Professor_teach_course, Location WHERE " + "'" + str(userid) + "'" + "= Professor_teach_course.pid AND Professor_teach_course.cid = Course.cid AND Location.lid = Course.lid"
          try:
            cursor1 = g.conn.execute(stmt)
          except:
            return render_template("error.html")
          std_course = []
          for result1 in cursor1:
            std_course.append(result1)
          cursor1.close()
          
          context = dict(std_course = std_course)
          return render_template("schedule_professor.html", **context)
      else:
        cursor.close()
        return render_template("error.html")

    return render_template("error.html")

@app.route('/course_info/<int:ccid>', methods=['GET'])
def course_info(ccid):
  if "uid" not in session:
    return render_template("index.html")
  role = session["role"]
  isProf = False
  if role=="professor":
    isProf = True
  stmt = "SELECT cid, cname, dname, term, time, capacity, credit FROM Course, Department WHERE Course.cid=" + "'" + str(ccid) + "'" + " AND Department.did = Course.did"
  keylist = ["Course ID", "Course Name", "Department", "Term", "Time", "Capacity", "Credits", "Current Enrollment", "Coursework"]
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  course_info = []
  i = 0
  for result in cursor:
    for ind in result:
      course_info.append((keylist[i], ind))
      i += 1
  cursor.close()

  stmt = "SELECT COUNT(*) FROM Student_enroll_course WHERE cid=" + "'" + str(ccid) + "'"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  for result in cursor:
    course_info.append((keylist[i], int(result[0])))
    i += 1

  cursor.close()

  stmt = "SELECT cwid, cwname FROM Coursework WHERE cid=" + "'" + str(ccid) + "'"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  cwlist = []
  for result in cursor:
    cwlist.append((int(result[0]), str(result[1])))

  course_info.append((keylist[i], cwlist))
  i += 1

  cursor.close()

  context = dict(course_info = course_info, isProf = isProf, cid = ccid)
  return render_template("course_info.html", **context)

@app.route('/cw_info/<int:cwid>', methods=['GET'])
def cw_info(cwid):
  if "uid" not in session:
    return render_template("index.html")
  stmt = "SELECT cwname, cid, min_group_size, max_group_size FROM Coursework WHERE cwid=" + "'" + str(cwid) + "'"
  keylist = ["Coursework", "Course ID", "Minimum Group Size", "Maximum Group Size"]
  cw_info = []
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  i = 0
  for result in cursor:
    for ind in result:
      if keylist[i]=="Minimum Group Size" or keylist[i]=="Maximum Group Size":
        cw_info.append((keylist[i], int(str(ind))))
      else:
        cw_info.append((keylist[i], str(ind)))
      i += 1

  cursor.close()

  uid = session['uid']
  role = session['role']


  if(role=="student"):
    groupProj = False
    fd = False
    tid = 0
    grade = 0
    approved = False
    mem_cnt = 0
    teamlist = []
    if int(cw_info[3][1])>1:
      groupProj = True
      stmt = "SELECT tid, grade, approved FROM Student_form_cw_team WHERE sid=" + "'" + str(uid) + "'" + " AND cwid=" + "'" + str(cwid) + "'"
      try:
        cursor = g.conn.execute(stmt)
      except:
        return render_template("error.html")
      
      for result in cursor:
        fd = True
        tid = int(result[0])
        grade = int(result[1])
        approved = result[2]

      cursor.close()

      if fd:
        stmt = "SELECT COUNT(*) FROM Student_form_cw_team WHERE tid=" + "'" + str(tid) + "'" + " AND cwid=" + "'" + str(cwid) + "'"
        try:
          cursor = g.conn.execute(stmt)
        except:
          return render_template("error.html")
        for result in cursor:
          mem_cnt = int(result[0])
        cursor.close()
        stmt = "SELECT sid FROM Student_form_cw_team WHERE tid=" + "'" + str(tid) + "'" + " AND cwid=" + "'" + str(cwid) + "'"
        try:
          cursor = g.conn.execute(stmt)
        except:
          return render_template("error.html")
        for result in cursor:
          teamlist.append(str(result[0]))
        cursor.close()

    context = dict(cw_info = cw_info, groupProj = True, group = fd, cwid = cwid, tid = tid, grade = grade, approved = approved, mem_cnt = mem_cnt, teamlist = teamlist)
    return render_template("cw_info.html", **context)
  else:
    stmt = "SELECT Team.tid, tname, approved FROM Team, Student_form_cw_team WHERE Team.cwid=" + "'" + str(cwid) + "' AND Student_form_cw_team.cwid=" + "'" + str(cwid) + "' AND Student_form_cw_team.tid=Team.tid"
    try:
      cursor = g.conn.execute(stmt)
    except:
      return render_template("error.html")
    teaminfo = []
    for result in cursor:
      print str(result[2])
      teaminfo.append([str(result[0]), str(result[1]), str(result[2])])

    context = dict(cw_info = cw_info, teaminfo = teaminfo, cwid = cwid)
    return render_template("cw_info_professor.html", **context)

@app.route('/team_edit/<int:cwid>/<int:tid>', methods=['GET'])
def team_edit(cwid, tid):
  if "uid" not in session:
    return render_template("index.html")
  stmt = "SELECT tname FROM team WHERE tid=" + "'" + str(tid) + "'" + " AND cwid=" + "'" + str(cwid) + "'"
  tname = ""
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  for result in cursor:
    tname = result[0]
  cursor.close()
  uid = session["uid"]
  stmt = "SELECT sid FROM Student_form_cw_team WHERE tid=" + "'" + str(tid) + "'" + " AND cwid=" + "'" + str(cwid) + "'"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  teamlist = []

  for result in cursor:
    print result
    teamlist.append(int(str(result[0])))
  cursor.close()

  candidate = []
  stmt = "SELECT DISTINCT(Student_enroll_course.sid) FROM Student_enroll_course, Student_form_cw_team, Coursework, Course WHERE Coursework.cwid=" + "'" + str(cwid)  + "'" + " AND Coursework.cid=Course.cid AND Student_enroll_course.cid=Course.cid AND Student_enroll_course.sid NOT IN (SELECT sid FROM student_form_cw_team where cwid="  + "'" + str(cwid) + "'" + ")" 
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  for result in cursor:
    print result
    candidate.append(int(str(result[0])))

  cursor.close()

  mem_cnt = 0
  stmt = "SELECT COUNT(*) FROM Student_form_cw_team WHERE tid=" + "'" + str(tid) + "'" + " AND cwid=" + "'" + str(cwid) + "'"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  for result in cursor:
    mem_cnt = int(result[0])
  cursor.close()

  context = dict(tname = tname, teamlist = teamlist, uid = uid, candidate = candidate, mem_cnt = mem_cnt, cwid = cwid)
  return render_template("team_edit.html", **context)

@app.route('/team_submit', methods=['POST'])
def team_submit():
  if "uid" not in session:
    return render_template("index.html")
  userid = str(request.form['member'])
  sid = str(session['uid'])
  mem_cnt = int(request.form['cnt'])
  cwid = request.form['cwid']

  maxsize = 0
  stmt = "SELECT max_group_size FROM Coursework WHERE cwid=" + "'" + str(cwid) + "'"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  for result in cursor:
    maxsize = int(result[0])
  cursor.close()


  tid = ''
  stmt = "SELECT tid FROM Student_form_cw_team WHERE sid=" + "'" + str(sid) + "'" + " AND cwid=" + "'" + str(cwid) + "'"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  for result in cursor:
    tid = result[0]
  cursor.close()


  if mem_cnt>=maxsize:
    return render_template("error.html")
  else:
    stmt = "INSERT INTO Student_form_cw_team VALUES (" + "'" + str(userid)  + "','" + str(cwid) + "','" + str(tid) + "', NULL, False)"
    try:
      cursor = g.conn.execute(stmt)
    except:
      return render_template("error.html")

  cursor.close()


  stmt = "SELECT sid FROM Student_form_cw_team WHERE tid=" + "'" + str(tid) + "'" + " AND cwid=" + "'" + str(cwid) + "'"
  teamlist = []
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  for result in cursor:
    teamlist.append(str(result[0]))
  cursor.close()

  stmt = "SELECT tname FROM team WHERE tid=" + "'" + str(tid) + "'" + " AND cwid=" + "'" + str(cwid) + "'"
  tname = ""
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  for result in cursor:
    tname = result[0]
  cursor.close()

  candidate = []
  stmt = "SELECT DISTINCT(Student_enroll_course.sid) FROM Student_enroll_course, Student_form_cw_team, Coursework, Course WHERE Coursework.cwid=" + "'" + str(cwid)  + "'" + " AND Coursework.cid=Course.cid AND Student_enroll_course.cid=Course.cid AND Student_enroll_course.sid NOT IN (SELECT sid FROM student_form_cw_team where cwid="  + "'" + str(cwid) + "'" + ")" 
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  for result in cursor:
    candidate.append(int(str(result[0])))

  cursor.close()


  context = dict(tname = tname, teamlist = teamlist, uid = userid, candidate = candidate, mem_cnt = mem_cnt, cwid = cwid)
  return render_template("team_edit.html", **context)

@app.route('/register_course', methods=['GET'])
def register_course():
  if "uid" not in session:
    return render_template("index.html")
  sid = session["uid"]
  courselist = []
  stmt = "SELECT Course.cid, Course.cname FROM Course WHERE Course.cid NOT IN (SELECT Student_enroll_course.cid FROM Student_enroll_course WHERE Student_enroll_course.sid = " + "'" +  str(sid)  + "'" + ")"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  for result in cursor:
    courselist.append((str(result[0]), str(result[1])))

  context = dict(courselist = courselist)
  cursor.close()

  return render_template("register_course.html", **context)

@app.route('/course_submit', methods=['POST'])
def course_submit():
  if "uid" not in session:
    return render_template("index.html")
  sid = session["uid"]
  cid = request.form["newcourse"]

  stmt = "INSERT INTO Student_enroll_course VALUES (" + "'" + str(sid) + "', '" + str(cid) + "', NULL)"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  cursor.close()

  stmt = "SELECT Course.cid, Course.cname, Course.time, Location.building, Location.classroom FROM Course, Student_enroll_course, Location WHERE " + "'" + str(sid) + "'" + "= Student_enroll_course.sid AND Student_enroll_course.cid = Course.cid AND Location.lid = Course.lid"
  try:
    cursor1 = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  std_course = []
  for result1 in cursor1:
    std_course.append(result1)
  cursor1.close()
          
  context = dict(std_course = std_course)

  return render_template("schedule.html", **context)

@app.route('/create_course', methods=['GET'])
def create_course():
  if "uid" not in session:
    return render_template("index.html")
  stmt = "SELECT cid FROM Course"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  cur = 0
  for result in cursor:
    cur = max(cur, int(result[0]))
  cursor.close()

  stmt = "SELECT did, dname FROM Department"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  deptlist = []
  for result in cursor:
    deptlist.append((str(result[0]), str(result[1])))
  cursor.close()

  stmt = "SELECT lid, building FROM Location"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  locationlist = []
  for result in cursor:
    locationlist.append((str(result[0]),str(result[1])))
  cursor.close()

  context = dict(max_cid = cur+1, deptlist = deptlist, locationlist = locationlist)

  return render_template("create_course.html", **context)

@app.route('/course_create_submit', methods=['POST'])
def course_create_submit():
  if "uid" not in session:
    return render_template("index.html")
  cid = request.form["cid"]
  cname = request.form["cname"]
  did = request.form["department"]
  term = request.form["term"]
  time = request.form["time"]
  capacity = request.form["capacity"]
  credit = request.form["credit"]
  location = request.form["location"]


  stmt = "INSERT INTO Course VALUES (" + "'" + str(cid) + "', '" + str(cname) + "', '" + str(did) + "', '" + str(term) + "', '" + str(time) + "', '" + str(capacity) + "', '" + str(credit) + "', '" + str(location) + "')"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  cursor.close()
  pid = session["uid"]

  stmt = "INSERT INTO Professor_teach_course VALUES (" + "'" + str(pid) + "', '" + str(cid) + "')"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  cursor.close()


  stmt = "SELECT Course.cid, Course.cname, Course.time, Location.building, Location.classroom FROM Course, Professor_teach_course, Location WHERE " + "'" + str(pid) + "'" + "= Professor_teach_course.pid AND Professor_teach_course.cid = Course.cid AND Location.lid = Course.lid"
  try:
    cursor1 = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  std_course = []
  for result1 in cursor1:
    std_course.append(result1)
  cursor1.close()
  
  context = dict(std_course = std_course)

  return render_template("schedule_professor.html", **context)

@app.route('/remove_course', methods=['GET'])
def remove_course():
  if "uid" not in session:
    return render_template("index.html")
  pid = session["uid"]
  stmt = "SELECT Professor_teach_course.cid, Course.cname FROM Professor_teach_course, Course WHERE pid=" + "'" + str(pid) + "' AND Professor_teach_course.cid=Course.cid";
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")

  courselist = []
  for result in cursor:
    courselist.append((str(result[0]), str(result[1])))

  cursor.close()

  context = dict(courselist = courselist)
  return render_template("remove_course.html", **context)

@app.route('/remove_submit', methods=['POST'])
def remove_submit():
  if "uid" not in session:
    return render_template("index.html")
  cid = request.form["course"]
  pid = session["uid"]
  # get coursework id
  cwid = []
  stmt = "SELECT cwid FROM coursework WHERE cid=" + "'" + str(cid) + "'"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  for result in cursor:
    cwid.append(str(result[0]))

  for cw in cwid:
    # remove team
    stmt = "DELETE FROM team WHERE cwid=" + "'" + str(cw) + "'"
    try:
      g.conn.execute(stmt)
    except:
      return render_template("error.html")

    # remove student_form_cw_team
    stmt = "DELETE FROM Student_form_cw_team WHERE cwid=" + "'" + str(cw) + "'"
    try:
      g.conn.execute(stmt)
    except:
      return render_template("error.html")

    # remove coursework
    stmt = "DELETE FROM Coursework WHERE cwid=" + "'" + str(cw) + "'"
    try:
      g.conn.execute(stmt)
    except:
      return render_template("error.html")

  # remove student_enroll_course
  stmt = "DELETE FROM Student_enroll_course WHERE cid=" + "'" + str(cid) + "'"
  try:
    g.conn.execute(stmt)
  except:
    return render_template("error.html")

  # remove professor_teach_course
  stmt = "DELETE FROM Professor_teach_course WHERE cid=" + "'" + str(cid) + "'"
  try:
    g.conn.execute(stmt)
  except:
    return render_template("error.html")

  # remove course
  stmt = "DELETE FROM Course WHERE cid=" + "'" + str(cid) + "'"
  try:
    g.conn.execute(stmt)
  except:
    return render_template("error.html")


  stmt = "SELECT Course.cid, Course.cname, Course.time, Location.building, Location.classroom FROM Course, Professor_teach_course, Location WHERE " + "'" + str(pid) + "'" + "= Professor_teach_course.pid AND Professor_teach_course.cid = Course.cid AND Location.lid = Course.lid"
  try:
    cursor1 = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  std_course = []
  for result1 in cursor1:
    std_course.append(result1)
  cursor1.close()
  
  context = dict(std_course = std_course)

  return render_template("schedule_professor.html", **context)

@app.route('/create_cw/<int:cid>', methods=['GET'])
def create_cw(cid):
  if "uid" not in session:
    return render_template("index.html")
  context = dict(cid = cid)
  return render_template("create_cw.html", **context)

@app.route('/cw_create_submit', methods=['POST'])
def cw_create_submit():
  if "uid" not in session:
    return render_template("index.html")
  cid = request.form["cid"]
  cwname = request.form["cwname"]
  minsize = int(request.form["minsize"])
  maxsize = int(request.form["maxsize"])

  stmt = "INSERT INTO Coursework (cwname, min_group_size, max_group_size, cid) VALUES (" + "'" + str(cwname) + "', " + str(minsize) + ", " + str(maxsize) + ", '" + str(cid) + "')"
  try:
    g.conn.execute(stmt)
  except:
    return render_template("error.html")


  ccid = cid

  role = session["role"]
  isProf = False
  if role=="professor":
    isProf = True
  stmt = "SELECT cid, cname, dname, term, time, capacity, credit FROM Course, Department WHERE Course.cid=" + "'" + str(ccid) + "'" + " AND Department.did = Course.did"
  keylist = ["Course ID", "Course Name", "Department", "Term", "Time", "Capacity", "Credits", "Current Enrollment", "Coursework"]
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  course_info = []
  i = 0
  for result in cursor:
    for ind in result:
      course_info.append((keylist[i], ind))
      i += 1
  cursor.close()

  stmt = "SELECT COUNT(*) FROM Student_enroll_course WHERE cid=" + "'" + str(ccid) + "'"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  for result in cursor:
    course_info.append((keylist[i], int(result[0])))
    i += 1

  cursor.close()

  stmt = "SELECT cwid, cwname FROM Coursework WHERE cid=" + "'" + str(ccid) + "'"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  cwlist = []
  for result in cursor:
    cwlist.append((int(result[0]), str(result[1])))

  course_info.append((keylist[i], cwlist))
  i += 1

  cursor.close()

  context = dict(course_info = course_info, isProf = isProf, cid = ccid)
  return render_template("course_info.html", **context)

@app.route('/approve_team', methods=['POST'])
def approve_team():
  if "uid" not in session:
    return render_template("index.html")
  cwid = request.form["cwid"]
  stmt = "UPDATE Student_form_cw_team SET approved=True WHERE cwid=" + "'" + str(cwid) + "'"
  try:
    g.conn.execute(stmt)
  except:
    return render_template("error.html")

  stmt = "SELECT cwname, cid, min_group_size, max_group_size FROM Coursework WHERE cwid=" + "'" + str(cwid) + "'"
  keylist = ["Coursework", "Course ID", "Minimum Group Size", "Maximum Group Size"]
  cw_info = []
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  i = 0
  for result in cursor:
    for ind in result:
      if keylist[i]=="Minimum Group Size" or keylist[i]=="Maximum Group Size":
        cw_info.append((keylist[i], int(str(ind))))
      else:
        cw_info.append((keylist[i], str(ind)))
      i += 1

  stmt = "SELECT Team.tid, tname, approved FROM Team, Student_form_cw_team WHERE Team.cwid=" + "'" + str(cwid) + "' AND Student_form_cw_team.cwid=" + "'" + str(cwid) + "' AND Student_form_cw_team.tid=Team.tid"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  teaminfo = []
  for result in cursor:
    print str(result[2])
    teaminfo.append([str(result[0]), str(result[1]), str(result[2])])

  context = dict(cw_info = cw_info, teaminfo = teaminfo, cwid = cwid)

  return render_template("cw_info_professor.html", **context)

@app.route('/above_average', methods=['GET'])
def above_average():
  if "uid" not in session:
    return render_template("index.html")
  stmt = "SELECT DISTINCT S.sid, S.name FROM Student S, Grade G, Student_Enroll_Course SEC, (SELECT SEC1.cid, AVG(G1.n_grade) AS avgn_grade FROM Student_Enroll_Course SEC1, Grade G1 WHERE SEC1.l_grade = G1.l_grade GROUP BY SEC1.cid) C_grade WHERE SEC.cid = C_grade.cid AND SEC.l_grade=G.l_grade AND G.n_grade > C_grade.avgn_grade AND SEC.sid = S.sid;"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  stdlist = []
  for result in cursor:
    stdlist.append((str(result[0]),str(result[1])))

  context = dict(stdlist = stdlist)
  return render_template("above_average.html", **context)


@app.route('/horrible_course', methods=['GET'])
def horrible_course():
  if "uid" not in session:
    return render_template("index.html")
  stmt = "SELECT C.cid, C.cname FROM Course C, (SELECT SEC1.cid, MAX(G1.n_grade) AS maxgrade, MIN(G1.n_grade) AS mingrade FROM Student_Enroll_Course SEC1, Grade G1 WHERE SEC1.l_grade = G1.l_grade GROUP BY SEC1.cid) CM WHERE C.cid = CM.cid AND CM.maxgrade > 1.1 * CM.mingrade;"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  hc = []
  for result in cursor:
    hc.append((str(result[0]),str(result[1])))

  context = dict(hc = hc)
  return render_template("horrible_course.html", **context)


@app.route('/project_star', methods=['GET'])
def project_star():
  if "uid" not in session:
    return render_template("index.html")
  stmt = "select STUDENT.sid, STUDENT.did from (select did, MAX(gpa) as g from (select STUDENT.sid, STUDENT_ENROLL_COURSE.cid, cwavg.cwid from STUDENT, STUDENT_ENROLL_COURSE, STUDENT_FORM_CW_TEAM, COURSEWORK, (select STUDENT_FORM_CW_TEAM.cwid, AVG(grade) as g from STUDENT_FORM_CW_TEAM, (select cwid, cid from COURSEWORK where min_group_size>1) as tp where tp.cwid=STUDENT_FORM_CW_TEAM.cwid group by STUDENT_FORM_CW_TEAM.cwid) as cwavg where STUDENT_ENROLL_COURSE.cid = COURSEWORK.cid  and COURSEWORK.cwid = STUDENT_FORM_CW_TEAM.cwid and STUDENT_FORM_CW_TEAM.grade > cwavg.g and cwavg.cwid=STUDENT_FORM_CW_TEAM.cwid) as std_above_avg, STUDENT where STUDENT.sid = std_above_avg.sid group by did) as ps_max, student where gpa=ps_max.g and ps_max.did=STUDENT.did;"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  stdlist = []
  for result in cursor:
    stdlist.append((str(result[0]),str(result[1])))

  context = dict(stdlist = stdlist)
  return render_template("project_star.html", **context)

@app.route('/register/<int:role>', methods=['GET'])
def register(role):
  stmt = "SELECT did from Department";
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")

  didlist = []
  for result in cursor:
    didlist.append(str(result[0]))

  cursor.close()

  if role==1:
    stmt = "SELECT sid from Student";
    try:
      cursor = g.conn.execute(stmt)
    except:
      return render_template("error.html")
    maxid = 0
    for result in cursor:
      maxid = max(maxid, int(result[0]))

    maxid += 1
    context = dict(maxid = maxid, role = role, didlist = didlist)
    return render_template("registration.html", **context)

  else:
    stmt = "SELECT pid from Professor";
    try:
      cursor = g.conn.execute(stmt)
    except:
      return render_template("error.html")
    maxid = 0
    for result in cursor:
      maxid = max(maxid, int(result[0]))
    maxid += 1

    context = dict(maxid = maxid, role = role, didlist = didlist)
    return render_template("registration.html", **context)
  return render_template("error.html")

@app.route('/register_submit', methods=['POST'])
def register_submit():
  if "uid" not in session:
    return render_template("index.html")
  role = request.form["role"]
  id = request.form["id"]
  name = request.form["name"]
  did = request.form["did"]
  if role=="1":
    cohort = request.form["cohort"]
    gender = request.form["gender"]

    stmt = "INSERT INTO Student VALUES (" + "'" + str(id) + "', '" + str(name) + "', '" + str(cohort) + "', '" + str(gender) + "', 0, '" + str(did) + "')"
    try:
      cursor = g.conn.execute(stmt)
    except:
      return render_template("error.html")
    cursor.close()
    stmt = "INSERT INTO Student_Login VALUES (" + "'" + str(id) + "', '12345')"
    try:
      cursor = g.conn.execute(stmt)
    except:
      return render_template("error.html")
    cursor.close()
    return render_template("index.html")
  else:
    title = request.form["title"]
    stmt = "INSERT INTO Professor VALUES (" + "'" + str(id) + "', '" + str(name) + "', '" + str(did) + "', '" + str(title) + "')"
    try:
      cursor = g.conn.execute(stmt)
    except:
      return render_template("error.html")
    cursor.close()
    stmt = "INSERT INTO Professor_Login VALUES (" + "'" + str(id) + "', '12345')"
    try:
      cursor = g.conn.execute(stmt)
    except:
      return render_template("error.html")
    return render_template("index.html")
  return render_template("error.html")

@app.route('/initiate_team/<int:cwid>', methods=['GET'])
def initiate_team(cwid):
  if "uid" not in session:
    return render_template("index.html")
  print cwid
  stmt = "SELECT tid FROM team WHERE cwid=" + "'" + str(cwid) + "'"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  maxtid = 0
  for result in cursor:
    maxtid = max(maxtid, int(result[0]))
  maxtid += 1
  cursor.close()

  print maxtid

  stmt = "INSERT INTO team VALUES (" + "'" + str(maxtid) + "', '" + str(cwid) + "', 'Bunny')"
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")

  cursor.close()



  stmt = "SELECT cwname, cid, min_group_size, max_group_size FROM Coursework WHERE cwid=" + "'" + str(cwid) + "'"
  keylist = ["Coursework", "Course ID", "Minimum Group Size", "Maximum Group Size"]
  cw_info = []
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")
  i = 0
  for result in cursor:
    for ind in result:
      if keylist[i]=="Minimum Group Size" or keylist[i]=="Maximum Group Size":
        cw_info.append((keylist[i], int(str(ind))))
      else:
        cw_info.append((keylist[i], str(ind)))
      i += 1

  cursor.close()


  uid = session['uid']
  role = session['role']

  stmt = "INSERT INTO Student_form_cw_team VALUES (" + "'" + str(uid) + "', '" + str(cwid) + "', '" + str(maxtid) + "', 0, False)" 
  try:
    cursor = g.conn.execute(stmt)
  except:
    return render_template("error.html")

  cursor.close()


  groupProj = False
  fd = False
  tid = 0
  grade = 0
  approved = False
  mem_cnt = 0
  teamlist = []
  if int(cw_info[3][1])>1:
    groupProj = True
    stmt = "SELECT tid, grade, approved FROM Student_form_cw_team WHERE sid=" + "'" + str(uid) + "'" + " AND cwid=" + "'" + str(cwid) + "'"
    try:
      cursor = g.conn.execute(stmt)
    except:
      return render_template("error.html")
    
    for result in cursor:
      fd = True
      tid = int(result[0])
      grade = int(result[1])
      approved = result[2]

    cursor.close()

    if fd:
      stmt = "SELECT COUNT(*) FROM Student_form_cw_team WHERE tid=" + "'" + str(tid) + "'" + " AND cwid=" + "'" + str(cwid) + "'"
      try:
        cursor = g.conn.execute(stmt)
      except:
        return render_template("error.html")
      for result in cursor:
        mem_cnt = int(result[0])
      cursor.close()
      stmt = "SELECT sid FROM Student_form_cw_team WHERE tid=" + "'" + str(tid) + "'" + " AND cwid=" + "'" + str(cwid) + "'"
      try:
        cursor = g.conn.execute(stmt)
      except:
        return render_template("error.html")
      for result in cursor:
        teamlist.append(str(result[0]))
      cursor.close()

  context = dict(cw_info = cw_info, groupProj = True, group = fd, cwid = cwid, tid = tid, grade = grade, approved = approved, mem_cnt = mem_cnt, teamlist = teamlist)
  

  return render_template("cw_info.html", **context)



if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', default=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
