from flask import Flask,render_template,redirect,url_for,session,logging,request,flash
# from data import Articles
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField,validators,Form,TextAreaField
from wtforms.validators import  DataRequired, Length, Email, EqualTo, ValidationError
from passlib.hash import sha256_crypt
from functools import wraps
import os
SECRET_KEY = os.urandom(32)
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Dhirendra32'
app.config['MYSQL_DB'] = 'flaskAPP'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

# Articles = Articles()

@app.route('/')
def index ():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')
    
    
@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()
    # Get articles
    #result = cur.execute("SELECT * FROM articles")
    # Show articles only from the user logged in
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        flash('No Articles Found','info')
        return render_template('articles.html')
    # Close connection
    cur.close()
#note : no space should be given in url
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()
    # Get article
    result = cur.execute("SELECT * FROM articles WHERE ID = %s", [id])
    article = cur.fetchone()
    return render_template('article.html', article=article)
#Register Form
class RegistrationForm (Form):
    name = StringField('Name',validators= [DataRequired(), Length(min=2, max=20)])
    username = StringField('Username', validators= [DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password',
        validators=[DataRequired()])
    confirm_password = PasswordField('Confirm password', validators=[DataRequired(),EqualTo('password', message='Passwords do not match')])
    submit = SubmitField('Sign up')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        #encrypting password before pusing the data
        password = sha256_crypt.encrypt(str(form.password.data))
        # Create cursor
        cur = mysql.connection.cursor()
        # Execute query
        cur.execute("INSERT INTO user(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
        # Commit to DB
        mysql.connection.commit()
        # Close connection
        cur.close()
        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username = request.form['username']
        password_c = request.form['password']
        #Create a cursor to establish connection with mysql flaskapp database to compare password
        cur= mysql.connection.cursor()
        #Get password stored in flaskAPP data base using username
        result = cur.execute('SELECT * FROM user WHERE username = %s',[username] )
        if result>0:
            data = cur.fetchone()
            password = data['password']
            #compare the password
            if sha256_crypt.verify(password_c, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                #In url we pass route login function
                return redirect(url_for('dashboard'))
                cur.close()
            else:
                flash('Incorrect password','danger')
                app.logger.info('password dosnt match')
        else:
            flash(username+' doesnt exist','warning')
            
    return render_template('login.html')

#login Required handling
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized Page acceess . Please login !','danger')
            return redirect(url_for('login', next=request.url))
    return decorated_function
    
#logout handling
@app.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    session.clear()
    flash('You are log out','success')
    return redirect(url_for('login'))

#Dashboard handling
@app.route('/dashboard',methods=['GET','POST'])
@login_required
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()
    # Get articles
    #result = cur.execute("SELECT * FROM articles")
    # Show articles only from the user logged in
    result = cur.execute("SELECT * FROM articles WHERE author = %s", [session['username']])
    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        flash('No Articles Found','info')
        return render_template('dashboard.html')
    
    # Close connection
    cur.close()
    return render_template('dashboard.html')

#article for class
class ArticleForm (Form):
    title = StringField('Title',validators= [DataRequired(), Length(min=2, max=200)])
    body = TextAreaField('Body', validators= [DataRequired(), Length(min=30)])


#add article
@app.route('/add_article', methods=['GET','POST'])
@login_required
def add_article():
    form = ArticleForm(request.form)
    if request.method=='POST':
        title = form.title.data
        body = form.body.data
        #making connecttion to mysql flaskapp table
        cur = mysql.connection.cursor()
        #execute query
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))
        #commit
        mysql.connection.commit()
        #close connection
        cur.close()
        flash("Article created ",'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form=form)
    
# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()
    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE ID=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@login_required
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute column should be case sensitive like datbase
    cur.execute("DELETE FROM articles WHERE ID = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))
    
if __name__ == '__main__':
    app.run(debug=True)
    
