import re
import model
from google.appengine.ext import db

# Validators for form data
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

def valid_username(username):
    userInDB = model.Users.gql("where name = :1", username).get()
    if userInDB:
        return None
    return USER_RE.match(username)

def valid_password(password):
    return PASS_RE.match(password)

def valid_email(email):
    return not email or EMAIL_RE.match(email)

@db.transactional
def edit_page(key, user_id, content):
	page = db.get(key)
	page.content = content
	page.put()
