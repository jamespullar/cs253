import webapp2
import cgi
import codecs
import re
import os
from jinja2 import Environment, FileSystemLoader
from google.appengine.ext import db

env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
                  autoescape=True)

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

class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

# Creates a Users object for storing users in db
class Users(db.Model):
    name = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.EmailProperty(required=False)
    created = db.DateTimeProperty(auto_now_add=True)

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.response.out.write(self.render_str(template, **kw))
    
    def render_str(self, template, **params):
        t = env.get_template(template)
        return t.render(params)

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

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
        # Get all values from signup form
        username = self.request.get("username")
        password = self.request.get("password")

        userInDB = Users.gql("where name = :1", username).get()

        if userInDB:
            userPassword = Users.gql("where password = :1", password).get()

            if userPassword:
                # Generate a cookie storing user_id
                self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % str(userInDB.key().id()))
                self.redirect('/welcome')
            else:
                error = "The username or password is incorrect."

                self.render('login.html', error = error)
        else:
            error = "The username or password is incorrect."

            self.render('login.html', error = error)

class Logout(BaseHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=''; Path=/')

        self.redirect('/signup')

class Welcome(BaseHandler):
    def get(self):
        user_id = self.request.cookies.get('user_id', False)
        user = Users.get_by_id(int(user_id))
        if user_id:
            self.render('welcome.html', username = user.name)
        else:
            self.render('signup.html')

class FrontPage(BaseHandler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created desc limit 10")

        self.render("home.html", posts = posts)

class SubmitPage(BaseHandler):
    def render_page(self, error = "", subject="", content=""):
        self.render("submit.html", error = error, subject = subject, content = content)

    def get(self):
        self.render_page()

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            post = Post(subject = subject, content = content)
            post.put()

            post_id = post.key().id()

            self.redirect("/%i" % post_id)
        else:
            error = "both subject and content required to post"
            self.render_page(error = error, subject = subject, content = content)

class PermaPage(BaseHandler):
    def get(self, post_id):
        post = Post.get_by_id(int(post_id))

        self.render('perma.html', post = post)

app = webapp2.WSGIApplication([('/signup', SignUp),
                               ('/welcome', Welcome),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/', FrontPage),
                               ('/([0-9]+)', PermaPage),
                               ('/newpost', SubmitPage)],
                                debug=True)

def main():
    run_wsgi_app(app)

if __name__ == '__main__':
    main()