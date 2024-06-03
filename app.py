from flask import Flask, render_template, request, session, redirect, flash, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import logging
from werkzeug.exceptions import HTTPException
from helper import login_required
import Queries as q
import sqlite3
import os
import datetime

app = Flask(__name__)
app.config.from_object('config.Config')

# Ensure database and tables are created
db = q.create_connection("time_travel.db")
import SQL
SQL.main()

app.config['UPLOAD_FOLDER'] = './static/uploads/'


def get_posts(user_era):
    posts_query = """
        SELECT posts.id, posts.uname, posts.title, posts.content, posts.likes, posts.image, posts.created_at
        FROM posts
        WHERE posts.era = ?
        ORDER BY posts.created_at DESC;
    """
    posts = q.sql_select_query(db, posts_query, (user_era,))
    print(f"Posts Query Result for era {user_era}: {posts}")  # Debugging line
    return posts
def get_user(user_id):
    user_query = """SELECT uname, id, bio FROM user WHERE id = ?"""
    user = q.sql_select_query(db, user_query, (user_id,))
    return user[0] if user else None

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get("username")
        email = request.form.get("inputEmail")
        existing_user_query = "SELECT id FROM user WHERE uname = :username"
        existing_user = q.sql_select_query(db, existing_user_query, {"username": username})

        if existing_user:
            flash("Username already exists. Please choose a different username.")
            return render_template("register.html", show_forms=True)

        if request.form.get("password") != request.form.get("confirmPassword"):
            flash("Passwords do not match. Please try again.")
            return render_template("register.html", show_forms=True)

        sql_query = "INSERT INTO user (uname, email, password) VALUES (:username, :email, :password)"
        q.sql_insert_query(db, sql_query, {"username": username, "email": email, "password": generate_password_hash(request.form.get("password"))})

        user_query = "SELECT id FROM user WHERE uname = :username"
        user = q.sql_select_query(db, user_query, {"username": username})
        if user:
            session["user_id"] = user[0]["id"]

        return redirect("/era_picker")

    else:
        return render_template("register.html", show_forms=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        pd = request.form.get("password")
        sql_query = "SELECT * from user where uname = :username"
        rows = q.sql_select_query(db, sql_query, dict(username=username))
        if len(rows) < 1:
            flash("Username does not exist", 'error')
        else:
            user_password = rows[0]["password"]
            if not check_password_hash(user_password, pd):
                flash("Incorrect Password", 'error')
            else:
                session["user_id"] = rows[0]["id"]
                return redirect("/home")
    return render_template("login.html", show_forms=True)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session.clear()
    return redirect("/")

@app.route('/era_picker', methods=['GET', 'POST'])
@login_required
def era_picker():
    if request.method == 'POST':
        selected_era = request.form.get("select-theme")
        user_id = session["user_id"]
        sql_query = "UPDATE user SET era = :era WHERE id = :user_id"
        q.sql_insert_query(db, sql_query, {"era": selected_era, "user_id": user_id})
        return redirect("/home")
    
    pre_existing_era = ["Cyberpunk", "Greece", "England"]
    return render_template("era_picker.html", eras=pre_existing_era)

@app.route('/home')
@login_required
def home():
    if 'user_id' in session:
        user_id = session['user_id']
        user_era_query = "SELECT era FROM user WHERE id = ?"
        user_era = q.sql_select_query(db, user_era_query, (user_id,))[0]['era']
        posts = get_posts(user_era)
        user = get_user(user_id)
        return render_template('home.html', posts=posts, user=user)
    else:
        return redirect('/login')

@app.route('/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        file = request.files['image']

        filename = None
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        user_id = session['user_id']
        user_query = "SELECT uname, era FROM user WHERE id = ?"
        user = q.sql_select_query(db, user_query, (user_id,))
        uname = user[0]['uname']
        era = user[0]['era']
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sql_query = 'INSERT INTO posts (title, content, image, uname, created_at, era) VALUES (?, ?, ?, ?, ?, ?)'
        q.sql_insert_query(db, sql_query, (title, content, filename, uname, created_at, era))

        flash('Post created successfully!')
        return redirect(url_for('home'))

    user_id = session['user_id']
    user_query = "SELECT uname FROM user WHERE id = ?"
    user = q.sql_select_query(db, user_query, (user_id,))
    return render_template('new_post.html', user=user)  # Pass 'user' variable to the template


@app.route('/post/<int:post_id>')
def view_post(post_id):
    post_query = """
        SELECT id, title, content, image, created_at, uname
        FROM posts
        WHERE id = ?
    """
    post = q.sql_select_query(db, post_query, (post_id,))
    if post:
        post = post[0]  # Fetch the first (and only) result
        return render_template('view_post.html', post=post)
    else:
        flash("Post not found.")
        return redirect(url_for('home'))


@app.route('/profile')
@login_required
def user_profile():
    user_id = session.get('user_id')
    if user_id:
        user_query = "SELECT uname FROM user WHERE id = ?"
        user = q.sql_select_query(db, user_query, (user_id,))
        if user:
            uname = user[0]['uname']
            user_posts_query = "SELECT * FROM posts WHERE uname = ?"
            user_posts = q.sql_select_query(db, user_posts_query, (uname,))
            return render_template('profile.html', user=uname, posts=user_posts)
    
    flash('User profile not found.')
    return redirect(url_for('home'))

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    logging.error(f"An error occurred: {str(e)}")
    return render_template("500.html"), 500

if __name__ == '__main__':
    app.run(debug=False)
