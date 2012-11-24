import webapp2
import cgi
import codecs
import re
import os

from jinja2 import Environment, FileSystemLoader
env = Environment(autoescape=True,
                  loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))

signupPage = env.get_template('signup.html')
rot13Page = env.get_template('rot13.html')
birthdayPage = env.get_template('birthday.html')

def render_str(template, **params):
    t = env.get_template(template)
    return t.render(params)

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.response.out.write(render_str(template, **kw))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    
class Rot13(BaseHandler):
    def get(self):
        self.render('rot13.html')
    
    def post(self):
        text = self.request.get('text')
        
        if text:
            self.render('rot13.html', text = codecs.encode(text, 'rot13'))

months = ['January',
          'February',
          'March',
          'April',
          'May',
          'June',
          'July',
          'August',
          'September',
          'October',
          'November',
          'December']

def valid_month(month):
    if month.capitalize() in months:
        return month.capitalize()
    return None

def valid_day(day):
    if isinstance(day, basestring) and day.isdigit():
        numDay = int(day)
        if numDay >=1 and numDay <=31:
            return numDay
    return None

def valid_year(year):
    if year and year.isdigit():
        numYear = int(year)
        if numYear >=1900 and numYear <=2020:
            return numYear

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return PASS_RE.match(password)

EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def valid_email(email):
    return not email or EMAIL_RE.match(email)

class MainPage(BaseHandler):
    def get(self):
        self.render('birthday.html')
    
    def post(self):
        month = self.request.get('month')
        day = self.request.get('day')
        year = self.request.get('year')

        validMonth = valid_month(month)
        validDay = valid_day(day)
        validYear = valid_year(year)

        if not (validMonth and validDay and validYear):
            self.render('birthday.html', **{"error": "Something is fishy here. Try again.",
                                            "month": month,
                                            "day": day,
                                            "year": year})
        else:
            self.redirect('/thanks')

class ThanksHandler(BaseHandler):
    def get(self):
        self.render("thanks.html")

class SignUp(BaseHandler):
    def get(self):
        self.render('signup.html')
        
    def post(self):
        args = {}

        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        if not valid_username(username):
            args["userError"] = "That isn't a valid username."
        if not valid_password(password):
            args["passwordError"] = "That isn't a valid password."
        if not verify == password:
            args["verifyError"] = "Your passwords don't match."
        if not valid_email(email):
            args["emailError"] = "That isn't a valid email."

        if args:
            args["userValue"] = username
            args["emailValue"] = email

            self.render('signup.html', **args)
        else:
            self.redirect('/welcome?username=' + username)

class Welcome(BaseHandler):
    def get(self):
        self.render('welcome.html', username = self.request.get('username'))
        
app = webapp2.WSGIApplication([('/', MainPage),
                               ('/thanks', ThanksHandler),
                               ('/rot13', Rot13),
                               ('/signup', SignUp),
                               ('/welcome', Welcome)],
                                debug=True)