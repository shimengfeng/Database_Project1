from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort,url_for,g,Response,abort
import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
#from flask_socketio import SocketIO
import random
from datetime import datetime

# from flask.ext.bcrypt import Bcrypt

 



tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
#socketio = SocketIO(app)


#setup the proper URL
DB_USER = "sf2911"
DB_PASSWORD = "dfct78AQYR"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"


#create engine and connect
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass



@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        output_note = dict(feedback = "There is something wrong with your login")
        return render_template('login.html',**output_note)
 
 # now after the user inpu user information, 
 # will check whether the input is valid by confirm the data within database

@app.route('/login', methods=['POST'])
def login():
    # g.conn.execute("DROP VIEW IF EXISTS user_temp;")

    error = None
    if request.method =='POST':
        username = request.form['username']
        user_entered = request.form['password']
 
        cursor = g.conn.execute("SELECT * FROM users WHERE username =%s", username)

        if len(list(cursor)) == 0:
            error = 'Invalid Username'
            return render_template('login.html',error=error)
        cursor = g.conn.execute("SELECT * FROM users WHERE username =%s", username)
    
        if cursor is not None:
            data = cursor.fetchone()
            password = data['password']
            
            # A = int(password) == int(user_entered)
            # user_context = dict(password1=A)
            if str(password) == str(user_entered):
                app.logger.info('Password Matched')
                session['logged_in'] = True
                session['age'] = data['age']
                session['first_name'] = data['first_name']
                session['last_name'] = data['last_name']
                session['address'] = data['address']
                session['u_id'] = data['u_id']
                session['email'] = data['email']
                session['username'] = username
                flash('You are now logged in', 'success')
                cursor.close()
                # g.conn.execute("CREATE VIEW user_temp AS SELECT * FROM users WHERE first_name =%s", username)
                return redirect (url_for('index'))

            else:
                error = "invalid password"
                return render_template('login.html',error=error)






#this is the mainpage for users after login
@app.route('/mainpage')
def index():
  print(request.args)
  try:
    listing_cursor = g.conn.execute("SELECT name,price,l_id FROM housing_query")
  except:
    listing_cursor = g.conn.execute("select L.name,AV.price,L.l_id from listings L,available AV,are A where L.l_id = A.l_id and A.a_id = AV.a_id")

  # user_name = g.conn.execute("SELECT first_name FROM user_temp")
  # user_name=tuple(user_name)
  name_dict = dict(name = session.get('username')) 
  
  housing_names=[]
  for result in listing_cursor:
    result = tuple(result)
    result+=(''.join(['static/',str(result[2]),'.jpg']),)
    housing_names.append(result)  # can also be accessed using result[0]

  listing_cursor.close()
  housing_context = dict(listings = housing_names)
  count_number = len(housing_names)
  count_context = dict(count = count_number)
  location_names = []
  location_cursor =  g.conn.execute("SELECT country FROM location")
  for result in location_cursor:
      location_names.append(result)
  location_cursor.close()
  location_context = dict(locations = location_names)
  
  
  housing_context = dict(listings = housing_names,locations = location_names,count = count_number,name = session.get('username'))
  
  g.conn.execute("DROP VIEW IF EXISTS housing_query;")

  return render_template("index.html", **housing_context)


# This is the listing page for each housing after click on individual page
# @app.route('/mainpage/<number>')
@app.route('/<int:number>')
def another(number):
  number = int(number)
  try:
      listing_cursor = g.conn.execute("select L.name,AV.price,L.l_id,D.summary,D.room, D.space,L.u_id from contains_description D,\
                                      listings L,available AV,are A where D.l_id = L.l_id and L.l_id = A.l_id and A.a_id = AV.a_id and L.l_id = %s",number)
  except:
       listing_cursor = g.conn.execute("select  L.name,AV.price,L.l_id,D.summary,D.room, D.space,L.u_id from contains_description D, listings L,available AV,are A where D.l_id = L.l_id and L.l_id = A.l_id and A.a_id = AV.a_id")
  housing_names=[]
  for result in listing_cursor:
    result = tuple(result)
    session['post_u_id'] = result[6]
    result+=(''.join(['static/',str(result[2]),'.jpg']),)
    housing_names.append(result)  # can also be accessed using result[0]

  listing_cursor.close()
  review_cursor = g.conn.execute("select R.comment, U.first_name from review R,users U  where U.u_id = R.u_id and R.l_id = %s",number)
  g.conn.execute("DROP VIEW IF EXISTS housing_query;")
  reviews=[]
  for result in review_cursor:
      result = tuple(result)
      reviews.append(result)
      session['number']=number
      
      
  review_context = dict(review=reviews)
  g.conn.execute("DROP VIEW IF EXISTS housing_query;")
  # user_name = g.conn.execute("SELECT first_name FROM user_temp")
  # user_name=tuple(user_name)
  name_dict = dict(name = session.get('username'))
  housing_context = dict(listings = housing_names,review=reviews,name = session.get('username'))

  return render_template("anotherfile.html",**housing_context)

#This is the page where you can select the criterial and select your own housing

@app.route('/add', methods=['POST'])
def add():
  trip_start = request.form['trip_start']
  trip_end = request.form['trip_end']
  trip_location = request.form['trip_location']
  args = (trip_start,trip_end,trip_location)


  engine.execute("DROP VIEW IF EXISTS housing_query;")
  if trip_location!='':
      g.conn.execute("CREATE VIEW housing_query AS SELECT L.name,\
                     AV.price,L.l_id from listings L,location LOC\
                     ,available AV,are A, posses P where\
                     L.l_id = A.l_id and A.a_id = AV.a_id and P.l_id = L.l_id and P.loc_id = LOC.loc_id and\
                     AV.availability_beginning_date>=%s and AV.availability_ending_date<=%s and LOC.country = %s",args)
  else:
      g.conn.execute("CREATE VIEW housing_query AS SELECT L.name,\
             AV.price,L.l_id from listings L\
             ,available AV,are A where\
             L.l_id = A.l_id and A.a_id = AV.a_id and\
             AV.availability_beginning_date>=%s and AV.availability_ending_date<=%s",(trip_start,trip_end))
  return redirect('/mainpage')


# This is the page lead to a chat window
# @app.route("/chat")
# def chat():
#     return render_template('chat.html')


@app.route('/chat')
def sessions():
    return render_template('session.html')

def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

#@socketio.on('my event')
#def handle_my_custom_event(json, methods=['GET', 'POST']):
#    print('received my event: ' + str(json))
#    socketio.emit('my response', json, callback=messageReceived)


#set the logout 
@app.route("/logout")
def logout():
      session['logged_in'] = False
      session.pop('logged_in',None)
      flash('You are logged out')
      return redirect(url_for('home'))

@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/create",methods=['POST'])
def create():
    session['username'] = request.form['username']
    session['firstname'] = request.form['firstname']
    session['lastname'] = request.form['lastname']
    session['address'] = request.form['address']
    session['age'] = request.form['age']
    session['password'] = request.form['psw']
    session['email'] = request.form['email']
    
    args = (random.randint(1,94543),session['age'],session['username'],session['firstname'],session['firstname'],session['address'],session['password'])
    g.conn.execute("INSERT INTO users(u_id,age,username,first_name,last_name,address,password) VALUES (%s,%s,%s,%s,%s,%s,%s)",args)

    return redirect(url_for("home"))
        
@app.route("/post",methods=['POST'])
def post():
    review = request.form['comment']
    u_id =  g.conn.execute("SELECT u_id FROM users where username =%s ", session.get('username'))
    # for u in u_id:
    #     u_id = str(u[0])
    u_id_new = u_id.fetchone()
    ## We need to be able to transfer l_id here
    number = session.get('number')
    r_id = str(random.randint(1,94543))
    args = (r_id,review,number,u_id_new[0])
    g.conn.execute("INSERT INTO review (r_id,comment,l_id,u_id) VALUES (%s,%s,%s,%s)",args)

    redir = ''.join(['/',str(number)])   
    return redirect(redir)


@app.route("/userprofile")
def userprofile():
    total_dict = dict(first_name = session.get('first_name'),last_name = session.get('last_name'),age = session.get('age'),
      address = session.get('address')) 

    return render_template("user.html",**total_dict)


@app.route("/book/<int:number>")
def book(number):

    number = int(number)
    listing_cursor = g.conn.execute("select L.name,AV.price,L.l_id,D.summary from contains_description D, listings L,available AV,are A where D.l_id = L.l_id and L.l_id = A.l_id and A.a_id = AV.a_id and L.l_id = %s",number)
    housing_names=[]
    for result in listing_cursor:
        result = tuple(result)
        result+=(''.join(['static/',str(result[2]),'.jpg']),)
    housing_names.append(result)  # can also be accessed using result[0]
    
    availability_cursor =  g.conn.execute("SELECT AV.availability_beginning_date, \
                                          AV.availability_ending_date  FROM available AV,are A,listings L where\
                                          L.l_id = A.l_id and AV.a_id = A.a_id and L.l_id =%s",number)
    
    
    
    
    dates = []
    for results in availability_cursor:
        dates.append(results)
    date_context = dict(date = dates)
    housing_context = dict(listings = housing_names,date = dates)
    return render_template("book.html",**housing_context)


@app.route('/booknow/<int:number>', methods=['POST'])
def booknow(number):
  try:
      number = int(number)
      # chat = request.form['chat']
      # if chat != None:
      #   return redirect('/chat')
      
      session['rent_room'] = request.form['room_number']
      session['move_in'] =  request.form['trip_start']
      session['move_out'] =  request.form['trip_end']
      d1 = datetime.strptime(session['move_in'], "%Y-%m-%d")
      d2 = datetime.strptime(session['move_out'], "%Y-%m-%d")
      price = g.conn.execute("select AV.price from contains_description D, listings L,available AV,are A where D.l_id = L.l_id and L.l_id = A.l_id and A.a_id = AV.a_id and L.l_id = %s",number)
      price = tuple(price)[0]
      booking_args = [ session.get('rent_room'), session.get('move_in'), session.get('move_out'),abs((d2 - d1).days),price[0],price[0]*abs((d2 - d1).days)*int(session.get('rent_room'))]
      booking_information = dict(booking_info = booking_args)
      return render_template("creditcard.html",**booking_information)
  except:
      return another(number)

@app.route("/chat_history",methods=['POST'])
def chat_history():
    #get u_sender ID from user who within session
    u_id = session.get('u_id')
    #get u_receiver ID from user who posted the listing
    u_receiver = session.get('post_u_id')
    args =  (u_id, u_receiver)
    history_list=[]
    try:
        chat_history = g.conn.execute("SELECT M.m_id, M.content,U1.first_name,U2.first_name FROM messages M,users U1,users U2 WHERE U2.u_id=u_sender and U1.u_id =u_receiver and u_sender=%s and u_receiver=%s",args)
        for history in chat_history:
            history_list.append(history)
        chat_dict=dict(history = history_list)   
    except:
        chat_dict=dict(history="No Chat History")
        
        
    try:
       message_sent = request.form['message']
       u_id = session.get('u_id')
       u_receiver = session.get('post_u_id')
       args =  (str(random.randint(1,94543)),message_sent, u_id, u_receiver)
       g.conn.execute("INSERT INTO messages(m_id, content,u_sender,u_receiver) VALUES (%s,%s,%s,%s)",args)
    except:
        pass
    return render_template("chat.html",**chat_dict)



if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=8111)
#    socketio.run(app, debug=True)





# if __name__ == "__main__":
#   import click

#   @click.command()
#   @click.option('--debug', is_flag=True)
#   @click.option('--threaded', is_flag=True)
#   @click.argument('HOST', default='0.0.0.0')
#   @click.argument('PORT', default=8111, type=int)
#   def run(debug, threaded, host, port):
 

#     HOST, PORT = host, port
#     print ("running on %s:%d" % (HOST, PORT))
#     app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


#   run()

