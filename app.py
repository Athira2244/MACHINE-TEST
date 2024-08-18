from flask import Flask,request,jsonify,session
from flask_mysqldb import MySQL
import json
import MySQLdb.cursors
import re


app=Flask(__name__)
app.secret_key = '1234'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='password'
app.config['MYSQL_DB']='postify'
mysql=MySQL(app)

@app.route('/signup',methods=['POST'])
def signup():
    details= request.json
    name=details['name']
    username=details['username']
    password=details['password']
    email=details['email']
    mobile=details['mobile']

    if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        return jsonify({"message": "Invalid email address!"}), 400
    if not username or not password or not email:
        return jsonify({"message": "Please fill out the form!"}), 400
    
    if len(password)<8:
        return jsonify({'message':"password  must be 8  characters long !"}),400
    if not re.search(r'[A-Z]', password):
        return jsonify({"message": "Password must contain at least one uppercase letter!"}), 400
    if not re.search(r'[0-9]', password):
        return jsonify({"message": "Password must contain at least one number!"}), 400
    if not re.search(r'[\W_]', password):
        return jsonify({"message": "Password must contain at least one special character!"}), 400
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM signup WHERE username = %s', (username,))
    account = cursor.fetchone()
    
    if account:
        return jsonify({"message": "Username already exists!"}), 400
    else:
        cursor.execute('INSERT INTO signup (name,username, password, email,mobile) VALUES (%s,%s, %s, %s,%s)', (name,username, password, email,mobile))
        mysql.connection.commit()
        return jsonify({"message": "You have successfully registered!"}), 201
    
@app.route('/login',methods=["POST"])
def login():
    details=request.json
    username=details['username']
    password=details['password']

    cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM signup WHERE username=%s AND password=%s',(username,password))
    account=cursor.fetchone()
   

    if account:
        session['user_id'] = account['id']
        return jsonify({"message": "Logged in successfully!"}), 200
    else:
        return jsonify({"message": "Incorrect username/password!"}), 401
    
@app.route('/post', methods=["POST"])
def post():
    if 'user_id' not in session:
        return jsonify({'message':"User is not logged in! cannot create post"}),401
    details = request.json
    title = details['title']
    description = details['description']
    tags = json.dumps(details['tags'])  # Serialize tags as a JSON string
    created_date = details['created_date']
    user_id = details['user_id']
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        'INSERT INTO post (title, description, tags, created_date, user_id) VALUES (%s, %s, %s, %s, %s)',
        (title, description, tags, created_date, user_id)
    )
    mysql.connection.commit()
    
    return jsonify({"message": "Post created!"}), 201

@app.route('/publish_post',methods=["POST"])
def publish_post():
    details=request.json
    user_id=details['user_id']
    post_id=details['post_id']
    status=details['status']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute('SELECT * FROM publish WHERE post_id=%s AND user_id=%s',(post_id,user_id))
    account=cursor.fetchone()
    print(account)
    if not account:
        cursor.execute(
        'INSERT INTO publish (user_id,post_id,status) VALUES (%s, %s, %s)',
        (user_id,post_id,status)
        )
        mysql.connection.commit()
    else:
        cursor.execute(
        'UPDATE publish set status=%s WHERE user_id=%s AND post_id=%s',
        (status,user_id,post_id)
        )
        mysql.connection.commit()
        
    if status=="1":
        return jsonify({'message':'post published!'})
    else:
        return jsonify({'message':'post unpublished'})
    
@app.route('/list_post',methods=["GET"])
def get_post_list():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""SELECT 
        post.title, 
        post.description, 
        post.id, 
        post.tags, 
        DATE_FORMAT(post.created_date, '%d-%m-%Y') AS created_date, 
        publish.status, 
        (SELECT COUNT(*) FROM liked_posts WHERE liked_posts.post_id = post.id AND liked_posts.status = 1) AS like_count 
    FROM 
        post 
    INNER JOIN 
        publish ON post.id = publish.post_id 
    WHERE 
        publish.status = 1""")
    account = cursor.fetchall()
    return jsonify(account),200



@app.route('/liked_posts',methods=["POST"])
def liked_post():
    details=request.json
    user_id=details['user_id']
    post_id=details['post_id']
    status=details['status']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute('SELECT * FROM liked_posts WHERE post_id=%s AND user_id=%s',(post_id,user_id))
    account=cursor.fetchone()
    print(account)
    if not account:
        cursor.execute(
        'INSERT INTO liked_posts (user_id,post_id,status) VALUES (%s, %s, %s)',
        (user_id,post_id,status)
        )
        mysql.connection.commit()
    else:
        cursor.execute(
        'UPDATE liked_posts set status=%s WHERE user_id=%s AND post_id=%s',
        (status,user_id,post_id)
        )
        mysql.connection.commit()
        
    if status=="1":
        return jsonify({'message':'post liked!'})
    else:
        return jsonify({'message':'post unliked'})



if __name__=="__main__":
    app.run(debug=True)