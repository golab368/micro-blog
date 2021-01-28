from flask import Flask, request, redirect,render_template,session, flash,  url_for
from flask_sqlalchemy import SQLAlchemy
import datetime
import functools
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField
from wtforms.validators import DataRequired
import os

app=Flask(__name__)

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "pass")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECRET_KEY'] = 'key'
db = SQLAlchemy(app)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    body = db.Column(db.Text, nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False,
        default=datetime.datetime.utcnow)
    is_published = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return "<User(title='%s', body='%s', pub_date='%s')>" % (self.title, self.body, self.pub_date)

class EntryForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    body = TextAreaField('Content', validators=[DataRequired()])
    is_published = BooleanField('Is Published?')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])

    def validate_username(self, field):
        if field.data != ADMIN_USERNAME:
            raise ValidationError("Invalid username")
        return field.data

    def validate_password(self, field):
        if field.data != ADMIN_PASSWORD:
            raise ValidationError("Invalid password")
        return field.data


def login_required(view_func):
    @functools.wraps(view_func)
    def check_permissions(*args, **kwargs):
        if session.get('logged_in'):
            return view_func(*args, **kwargs)
        return redirect(url_for('login', next=request.path))
    return check_permissions


@app.route("/login/", methods=['GET', 'POST'])
def login():
   form = LoginForm()
   errors = None
   next_url = request.args.get('next')
   if request.method == 'POST':
       if form.validate_on_submit():
           session['logged_in'] = True
           session.permanent = True  # Use cookie to store session.
           flash('You are now logged in.', 'success')
           return redirect(next_url or url_for('index'))
       else:
           errors = form.errors
   return render_template("login_form.html", form=form, errors=errors)


@app.route('/logout/', methods=['GET', 'POST'])
def logout():
   if request.method == 'POST':
       session.clear()
       flash('You are now logged out.', 'success')
   return redirect(url_for('index'))



@app.route("/")
def index():
    
    all_posts = Entry.query.filter_by(is_published=True).order_by(Entry.pub_date.desc())

    return render_template("homepage.html", all_posts=all_posts)


def create_entry_oredit_entry(entry_id, entry, form):
    errors = None
    if request.method == 'POST':
        if form.validate_on_submit() and entry_id:
            form.populate_obj(entry)
            db.session.commit()
            return redirect("/homepage")
        elif form.validate_on_submit():
            db.session.add(entry)
            db.session.commit()
        else:
            errors = form.errors
    return render_template('entry_form.html', form=form, errors=errors, entry_id=entry_id)

@app.route("/new-post/", methods=['GET', 'POST'])
@login_required
def create_entry():
    form = EntryForm()
    entry_id = None
    entry = Entry(
        title=form.title.data,
        body=form.body.data,
        is_published=form.is_published.data
        )
    return create_entry_oredit_entry(entry_id, entry, form)


@app.route("/edit-post/<int:entry_id>", methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    entry = Entry.query.filter_by(id=entry_id).first_or_404()
    form = EntryForm(obj=entry)
    return create_entry_oredit_entry(entry_id, entry, form)
    

@app.route("/drafts/", methods=['GET'])
@login_required
def list_drafts():
   drafts = Entry.query.filter_by(is_published=False).order_by(Entry.pub_date.desc())
   return render_template("drafts.html", drafts=drafts)

@app.route("/delete/<int:draft_id>", methods=['POST'])
def delete_entry(draft_id):
    draft = Entry.query.filter_by(id=draft_id).first_or_404()
    db.session.delete(draft)
    db.session.commit()
    return redirect("/")