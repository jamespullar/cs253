from google.appengine.ext import db

class DictModel(db.Model):
    def to_dict(self):
       return dict([(p, unicode(getattr(self, p))) for p in self.properties()])

class Post(DictModel):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

class Users(DictModel):
    name = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.EmailProperty(required=False)
    created = db.DateTimeProperty(auto_now_add=True)

class PageContent(DictModel):
	title = db.StringProperty(required=True)
	content = db.TextProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	last_modified = db.DateTimeProperty(auto_now=True)

class PageHistory(DictModel):
	page_id = db.IntegerProperty(required=True)
	user_id = db.IntegerProperty(required=True)
	content = db.TextProperty()
	modified = db.DateTimeProperty(auto_now_add=True)