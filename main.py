import os
import webapp2
import re
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

class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

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

app = webapp2.WSGIApplication([('/', FrontPage),
                               ('/([0-9]+)', PermaPage),
                               ('/newpost', SubmitPage)],
                                debug=True)

def main():
  run_wsgi_app(app)

if __name__ == '__main__':
  main()