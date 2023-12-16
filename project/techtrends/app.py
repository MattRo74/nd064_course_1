import sqlite3
import json
import logging

from datetime import datetime
from multiprocessing import Value
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

counter = Value('i', 0)

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    counter.value += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Function to get the number of posts in posts
def count_posts():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM posts')
    results = cursor.fetchall()
    connection.close()
    return len(results)

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)


# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:  
      app.logger.info(datetime.now().strftime("%m/%d/%Y, %H:%M, ") + '404 - A non-existing article is accessed')
      return render_template('404.html'), 404
    else:
      app.logger.info(datetime.now().strftime("%m/%d/%Y, %H:%M, ") + 'An nexisting article is accessed, Article: ' + post[2])
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info(datetime.now().strftime("%m/%d/%Y, %H:%M, ") + 'About Us page is accessed')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            return redirect(url_for('index'))

    app.logger.info(datetime.now().strftime("%m/%d/%Y, %H:%M, ") + 'a new Article is created')

    return render_template('create.html')

# Adding the /healthz Endpoint (health check) MR_1223
@app.route('/healthz')
def healthz():
    response = app.response_class(
        response=json.dumps({"result:":"OK - healthy"}),
        status=200,
        mimetype='application/json'
    )
    return response

# Adding the /metrics Endpoint (health check) MR_1223
@app.route('/metrics')
def metrics():
    db_cons = counter.value
    response = app.response_class(
        response=json.dumps({"db_connection_count:":db_cons,"post_count":count_posts()}),
        status=200,
        mimetype='application/json'
    )
    return response

# start the application on port 3111
if __name__ == "__main__":
   logging.basicConfig(filename='app.log', level=logging.DEBUG)
   app.run(host='0.0.0.0', port='3111')
