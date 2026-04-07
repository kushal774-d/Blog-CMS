import os
import pyodbc
from flask import Flask, render_template, request, redirect, url_for, g, session, flash
from werkzeug.utils import secure_filename
import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_in_production'

# --- IMAGE UPLOAD CONFIG ---
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- CONNECTION STRING CONFIGURATION ---
CONNECTION_STRING = (
    r"Driver={ODBC Driver 17 for SQL Server};"
    r"Server=DESKTOP-BRNB217\MSSQLSERVER01;"
    r"Database=BlogCMS;"
    r"Trusted_Connection=yes;"
)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = pyodbc.connect(CONNECTION_STRING)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def format_row(row, columns):
    d = dict(zip(columns, row))
    if 'created_at' in d and isinstance(d['created_at'], datetime.datetime):
        d['created_at'] = d['created_at'].strftime('%B %d, %Y - %H:%M')
    return d

def fetch_all_dicts(cursor):
    columns = [column[0] for column in cursor.description]
    return [format_row(row, columns) for row in cursor.fetchall()]

def fetch_one_dict(cursor):
    row = cursor.fetchone()
    if row is None:
        return None
    columns = [column[0] for column in cursor.description]
    return format_row(row, columns)

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Check if table exists, if not create it in MSSQL
        cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='posts' and xtype='U')
            BEGIN
                CREATE TABLE posts (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    title NVARCHAR(MAX) NOT NULL,
                    content NVARCHAR(MAX) NOT NULL,
                    image_path NVARCHAR(MAX) NULL,
                    created_at DATETIME DEFAULT GETDATE()
                )
            END
        ''')
        db.commit()

        # Attempt to add image_path column if table already exists without it
        try:
            cursor.execute("ALTER TABLE posts ADD image_path NVARCHAR(MAX) NULL")
            db.commit()
        except:
            pass

        # Create admins table
        cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='admins' and xtype='U')
            BEGIN
                CREATE TABLE admins (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    username NVARCHAR(50) NOT NULL,
                    password NVARCHAR(100) NOT NULL
                );
                INSERT INTO admins (username, password) VALUES ('kushal', '1213');
            END
            ELSE
            BEGIN
                IF NOT EXISTS(SELECT * FROM admins WHERE username='kushal')
                BEGIN
                    INSERT INTO admins (username, password) VALUES ('kushal', '1213');
                END
            END
        ''')
        db.commit()

        # Create writers table
        cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='writers' and xtype='U')
            BEGIN
                CREATE TABLE writers (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    username NVARCHAR(50) NOT NULL,
                    password NVARCHAR(100) NOT NULL
                );
            END
        ''')
        db.commit()


@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM posts ORDER BY created_at DESC')
    posts = fetch_all_dicts(cursor)
    return render_template('index.html', posts=posts)

@app.route('/post/<int:post_id>')
def post(post_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    post = fetch_one_dict(cursor)
    if post is None:
        return "Post not found", 404
    return render_template('post.html', post=post)

@app.route('/login/admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM admins WHERE username = ? AND password = ?', (username, password))
        user = fetch_one_dict(cursor)
        
        if user:
            session['user_id'] = user['id']
            session['role'] = 'admin'
            session['username'] = user['username']
            return redirect(url_for('admin'))
        else:
            flash("Invalid admin credentials!")
            
    return render_template('login_admin.html')

@app.route('/login/writer', methods=['GET', 'POST'])
def login_writer():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM writers WHERE username = ? AND password = ?', (username, password))
        user = fetch_one_dict(cursor)
        
        if user:
            session['user_id'] = user['id']
            session['role'] = 'writer'
            session['username'] = user['username']
            return redirect(url_for('writer'))
        else:
            flash("Invalid content writer credentials!")
            
    return render_template('login_writer.html')

@app.route('/register/writer', methods=['GET', 'POST'])
def register_writer():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        
        # Check if username exists
        cursor.execute('SELECT * FROM writers WHERE username = ?', (username,))
        existing_user = fetch_one_dict(cursor)
        
        if existing_user:
            flash("Username already exists! Please choose a different one.")
            return redirect(url_for('register_writer'))
            
        # Insert new writer
        cursor.execute("INSERT INTO writers (username, password) VALUES (?, ?)", (username, password))
        db.commit()
        
        flash("Registration successful! You can now log in.")
        return redirect(url_for('login_writer'))
        
    return render_template('register_writer.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET'])
def admin():
    if session.get('role') != 'admin':
        return redirect(url_for('login_admin'))
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM posts ORDER BY created_at DESC')
    posts = fetch_all_dicts(cursor)
    return render_template('admin.html', posts=posts)

@app.route('/writer', methods=['GET'])
def writer():
    if session.get('role') != 'writer':
        return redirect(url_for('login_writer'))
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM posts ORDER BY created_at DESC')
    posts = fetch_all_dicts(cursor)
    return render_template('writer.html', posts=posts)

@app.route('/add_post', methods=['POST'])
def add_post():
    if session.get('role') not in ['admin', 'writer']:
        return redirect(url_for('index'))
        
    title = request.form.get('title')
    content = request.form.get('content')
    image = request.files.get('image')
    image_path = None
    
    if image and image.filename != '':
        filename = secure_filename(image.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(path)
        image_path = f"uploads/{filename}"
        
    if title and content:
        db = get_db()
        cursor = db.cursor()
        if image_path:
            cursor.execute('INSERT INTO posts (title, content, image_path) VALUES (?, ?, ?)', (title, content, image_path))
        else:
            cursor.execute('INSERT INTO posts (title, content) VALUES (?, ?)', (title, content))
        db.commit()
        
    if session.get('role') == 'admin':
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('writer'))

@app.route('/admin/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if session.get('role') != 'admin':
        return "Unauthorized", 403
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    db.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    # Initialize the database table
    try:
        init_db()
        print("✅ Database connected and initialized successfully!")
    except Exception as e:
        print("❌ Could not connect or initialize database. Check your CONNECTION_STRING in app.py!")
        print("Error details:", e)
    app.run(debug=True, port=5000)
