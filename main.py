import os, time, codecs, time, logging

import webapp2, urllib, cgi, json
from jinja2 import Environment, FileSystemLoader
from google.appengine.api import memcache

from google.appengine.ext import db
from model import Users, Post
import util

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
        posts = memcache.get('top')
        query_time = memcache.get('time')

        if posts is not None:
            self.render("home.html", posts = posts, query_time = int(time.time() - query_time))
        else:
            posts = db.GqlQuery("select * from Post order by created desc limit 10")
            memcache.set('time', time.time())
            memcache.set('top', posts)
            self.render("home.html", posts = posts, query_time = '0')

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
            memcache.set('time', time.time())

            post_id = post.key().id()

            self.redirect("/%i" % post_id)
        else:
            error = "both subject and content required to post"
            self.render_page(error = error, subject = subject, content = content)

class PermaPage(BaseHandler):
    def get(self, post_id):
        post = Post.get_by_id(int(post_id))
        query_time = memcache.get('time')

        self.render('perma.html', post = post, query_time = int(time.time() - query_time))

class FlushHandler(BaseHandler):
    def get(self):
        memcache.flush_all()
        self.redirect('/')

class JsonHandler(BaseHandler):
    def get(self, *post_id):
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        if post_id:
            post = Post.get_by_id(int(post_id[0]))
            self.write(json.dumps(post.to_dict()))
        else:
            posts_query = Post.all().order('-created')
            posts = posts_query.fetch(10)
            self.write(json.dumps([p.to_dict() for p in posts]))

class Rot13(BaseHandler):
    def get(self):
        self.render('rot13.html')
    
    def post(self):
        text = self.request.get('text')
        
        if text:
            self.render('rot13.html', text = codecs.encode(text, 'rot13'))

class SignUp(BaseHandler):
    def get(self):
        user_id = self.request.cookies.get('user_id')

        if not user_id:
            self.render('signup.html')
        else:
            self.redirect('/')

    def post(self):
        errors = {}

        # Get all values from signup form
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        # Validate form data and return errors if invalid
        if not util.valid_username(username):
            errors["userError"] = "That isn't a valid username."
        if not util.valid_password(password):
            errors["passwordError"] = "That isn't a valid password."
        if not verify == password:
            errors["verifyError"] = "Your passwords don't match."
        if not util.valid_email(email):
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

            self.render('/welcome.html', logged_in = True, username = username)

class Login(BaseHandler):
    def get(self):
        user_id = self.request.cookies.get('user_id')
        
        if user_id:
            self.redirect('/')
        else:
            self.render('login.html', login = "active")

    def post(self):
        # Get all values from signup form
        username = self.request.get("username")
        password = self.request.get("password")

        # Query DB for existing username
        userInDB = Users.gql("where name = :1", username).get()

        # If the username matches the DB query
        if userInDB:
            # Query DB to match password to username
            userPassword = Users.gql("where password = :1", password).get()

            # If the password matches, set cookie with user_id and redirect to welcome screen
            if userPassword:
                # Generate a cookie storing user_id
                self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % str(userInDB.key().id()))
                self.redirect("/")

            # Throw error if password doesn't match
            else:
                error = "The username or password is incorrect."

                self.render('login.html', login = "active", error = error)

        # If the username doesn't match the DB query
        else:
            error = "The username or password is incorrect."

            self.render('login.html', login = "active", error = error)

class Logout(BaseHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=''; Path=/')

        self.redirect('/')

class WikiPage(BaseHandler):
    def get(self, path):
        user_id = self.request.cookies.get('user_id')
        
        if user_id:
            self.render('wikipage.html', logged_in=True, title = path, path = path[1:])
        else:
            self.redirect('/')

class WikiHome(BaseHandler):
    def get(self):
        user_id = self.request.cookies.get('user_id')

        if user_id:
            args = {}

            user = Users.get_by_id(int(user_id))

            args['home'] = "active"
            args['logged_in'] = True
            args['display'] = "none"

            self.render('wikihome.html', **args)
        else:
            self.render('wikihome.html', home = "active", logged_in = False)

class EditPage(BaseHandler):
    def get(self, path):
        user_id = self.request.cookies.get('user_id')
        
        if user_id:
            # Check if page in db

            self.render('wikipage.html', path = path[1:], logged_in=True, title=path[1:], edit=True)

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([('/signup/?', SignUp),
                               ('/welcome/?', Welcome),
                               ('/login/?', Login),
                               ('/logout/?', Logout),
                               ('/blog/?', FrontPage),
                               ('/([0-9]+)/?', PermaPage),
                               ('/newpost/?', SubmitPage),
                               ('/flush/?', FlushHandler),
                               ('/.json', JsonHandler),
                               ('/([0-9]+)/?.json', JsonHandler),
                               ('/rot13/?', Rot13),
                               ('/_edit' + PAGE_RE, EditPage),
                               ('/', WikiHome),
                               (PAGE_RE, WikiPage),
                               ],
                                debug=True)

def main():
    run_wsgi_app(app)

if __name__ == '__main__':
    main()