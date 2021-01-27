from flask import Flask, request, redirect
from flask_sqlalchemy import SQLAlchemy
import datetime
from flask import render_template
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField
from wtforms.validators import DataRequired


app=Flask(__name__)

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


@app.route("/")
def index():
    
    all_posts = Entry.query.filter_by(is_published=True).order_by(Entry.pub_date.desc())

    return render_template("homepage.html", all_posts=all_posts)



@app.route("/new-post/", methods=["GET", "POST"])
def create_entry():
   form = EntryForm()
   errors = None
   if request.method == 'POST':
       if form.validate_on_submit():
           entry = Entry(
               title=form.title.data,
               body=form.body.data,
               is_published=form.is_published.data
           )
           db.session.add(entry)
           db.session.commit()
       else:
           errors = form.errors
   return render_template("entry_form.html", form=form, errors=errors)

@app.route("/edit-post/<int:entry_id>", methods=["GET", "POST"])
def edit_entry(entry_id):
   entry = Entry.query.filter_by(id=entry_id).first_or_404()
   form = EntryForm(obj=entry)
   errors = None
   if request.method == 'POST':
       if form.validate_on_submit():
           form.populate_obj(entry)
           db.session.commit()
       else:
           errors = form.errors
   return render_template("entry_form.html", form=form, errors=errors)