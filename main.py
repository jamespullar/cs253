import webapp2
import cgi
import codecs
import re
import os
from google.appengine.ext import db
from jinja2 import Environment, FileSystemLoader
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
    return USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return PASS_RE.match(password)

EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def valid_email(email):
    return not email or EMAIL_RE.match(email)

# Creates a User object for storing users in db
class User(db.Model):
    username = db.StringProperty()
    password = db.StringProperty()
    email = db.Email()

class SignUp(BaseHandler):
    def get(self):
        self.render('signup.html')

    def post(self):
        args = {}
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        # Validate form data and return errors if invalid
        if not valid_username(username):
            args["userError"] = "That isn't a valid username."
        if not valid_password(password):
            args["passwordError"] = "That isn't a valid password."
        if not verify == password:
            args["verifyError"] = "Your passwords don't match."
        if not valid_email(email):
            args["emailError"] = "That isn't a valid email."

        # If errors exist render the page with the errors
        # If no errors exist redirect to welcome page 
        if args:
            args["userValue"] = username
            args["emailValue"] = email

            self.render('signup.html', **args)
        else:
            # Create the user entity with validated data
            user = User(username = username, password = password, email = email)

            # Generate a cookie storing user_id
            self.response.headers.add_header('Set-Cookie', 'user=%s; Path=/' % str(username))

            self.redirect('/welcome')

class Welcome(BaseHandler):
    def get(self):
        username = self.request.cookies.get('user')
        if username:
            self.render('welcome.html', username = username)
        else:
            self.render('signup.html')

app = webapp2.WSGIApplication([('/signup', SignUp),
                               ('/welcome', Welcome)],
                                debug=True)

