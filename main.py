import webapp2
import cgi
import codecs
import re
import os
from jinja2 import Environment, FileSystemLoader
from google.appengine.ext import db

env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
                  autoescape=True)

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.response.out.write(self.render_str(template, **kw))
    
    def render_str(self, template, **params):
        t = env.get_template(template)
        return t.render(params)

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

# Validators for form data
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    userInDB = Users.gql("where name = :1", username).get()
    if userInDB:
        return None
    return USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return PASS_RE.match(password)

EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def valid_email(email):
    return not email or EMAIL_RE.match(email)

# Creates a Users object for storing users in db
class Users(db.Model):
    name = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.EmailProperty(required=False)
    created = db.DateTimeProperty(auto_now_add=True)

class SignUp(BaseHandler):
    def get(self):
        self.render('signup.html')

    def post(self):
        errors = {}

        # Get all values from signup form
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        # Validate form data and return errors if invalid
        if not valid_username(username):
            errors["userError"] = "That isn't a valid username."
        if not valid_password(password):
            errors["passwordError"] = "That isn't a valid password."
        if not verify == password:
            errors["verifyError"] = "Your passwords don't match."
        if not valid_email(email):
            errors["emailError"] = "That isn't a valid email."

        # If errors exist render the page with the errors
        # If no errors exist redirect to welcome page 
        if errors:
            errors["userValue"] = username
            errors["emailValue"] = email

            self.render('signup.html', **errors)
        else:
            # Create the user entity with validated data
            if email:
                user = Users(name = username, password = password, email = email)
            else:
                user = Users(name = username, password = password)
            user.put()

            # Generate a cookie storing user_id
            self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % str(user.key().id()))

            self.redirect('/welcome')

class Login(BaseHandler):
    def get(self):
        self.render('login.html')

    def post(self):
        pass

class Welcome(BaseHandler):
    def get(self):
        user_id = self.request.cookies.get('user_id', False)
        user = Users.get_by_id(int(user_id))
        if user_id:
            self.render('welcome.html', username = user.name)
        else:
            self.render('signup.html')

app = webapp2.WSGIApplication([('/signup', SignUp),
                               ('/welcome', Welcome),
                               ('/login', Login)],
                                debug=True)

