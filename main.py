#!/usr/bin/env python

import os
import re
import random
import hashlib
import hmac
import logging
from string import letters

import words

import jinja2
import webapp2

#from google.appengine.api import memcache
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = "aDvD/?xhM@Nio6THLAmV.-os|+;C^]U4_TvL/O>IAHFotvqsF.S0V:cH-TjAnZ"
                               
def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())
 
def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    
    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)
        
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    # Two part cookie: User_key_id|Cookie
    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    # If cookie value exists, check the value
    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)
    
    # Use the user ID as first part of cookie.
    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))
    
    # Clear cookie on logout.
    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
 
    # Initialized upon __init__ of Handler.
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id') # Check for user cookie
        self.user = uid and User.by_id(int(uid)) # If exists, store in user obj

    def notfound(self):
        self.error(404)
        self.write('<h1>404: Not Found</h1>Sorry, that page does not exist.')


### Password functions ###        

def make_salt(length=64):
        return ''.join(random.choice(letters) for x in xrange(length))
        
def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name+pw+salt).hexdigest()
    return '%s|%s' % (salt, h)

def valid_pw(name, pw, h):
    salt = h.split('|')[0]
    return h == make_pw_hash(name, pw, salt)

### End password functions ###

class User(db.Model):
    name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()
    
    # Get user id.
    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid)
    
    # If user with the input name exists, return the user obj, else return None.
    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u
    
    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name) # Check if user exists
        if u and valid_pw(name, pw, u.pw_hash): # Check if login pw is valid
            return u
    
    # When user signs up, create password hash based on input password
    @classmethod
    def register(cls, name, pw, email=None):
        pw_hash = make_pw_hash(name, pw)
        return User(name = name, 
                    pw_hash = pw_hash, 
                    email = email)


### Form validation functions ###
                    
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PW_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PW_RE.match(password)

VERIFY_RE = re.compile(r"^.{3,20}$")
def valid_verify(verify):
    return verify and VERIFY_RE.match(verify)

EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def valid_email(email):
    return not email or EMAIL_RE.match(email)

### End form validation functions ###

class Signup(Handler):
    def get(self):
        next_url = self.request.headers.get('referer', '/')
        self.render("signup.html", next_url = next_url)

    def post(self):
        have_error = False
        
        next_url = str(self.request.get('next_url'))
        if not next_url or next_url.startswith('/login'):
            next_url = '/'
        
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username = self.username,
                      email = self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True

        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True
        
        if have_error:
            self.render('signup.html', **params)
        else:
            u = User.by_name(self.username)
            if u:
                error = "That user already exists."
                self.render('signup.html', error_user_exists = error)
            else:
                u = User.register(self.username, self.password, self.email)
                u.put()

                self.login(u)
                self.redirect(next_url)


class Login(Handler):
    def get(self):
        next_url = self.request.headers.get('referer', '/')
        self.render("login.html", next_url = next_url)

    def post(self):
        have_error = False
        username = self.request.get('username')
        password = self.request.get('password')
        
        next_url = str(self.request.get('next_url'))

        if not next_url or next_url.startswith('/login'):
            next_url = '/'

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect(next_url)
        else:
            error = "Invalid login"
            self.render("login.html", error = error)    


class Logout(Handler):
    def get(self):
        next_url = self.request.headers.get('referer', '/')
        self.logout()
        return self.redirect(next_url)

        
class Story(db.Model):
    subject = db.StringProperty(required = True)
    lines = db.IntegerProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
        
def create_story(subject,lines):

    story = ""
    lines = int(lines)
    
    n = random.sample(words.nouns, lines)
    a = random.sample(words.adjectives, lines)
        
    for i in range(lines - 1):
        s = (subject, n.pop(), a.pop())
        story += "That's not my %s. Its %s is too %s.\n" % s
    story += "That's my %s! Its %s is so %s." % (subject, n[0], a[0])
    
    return story

class MainPage(Handler):
    def get(self):
        self.render("index.html")
        
    def post(self):
        
        subject = self.request.get('subject')
        lines = self.request.get('lines')        
        content = create_story(subject,lines)

        story = Story(subject = subject, lines = int(lines), content = content)
        story.put()
        
        self.write(content)
        #self.redirect("/thats-not-my-" + subject)
        
class StoryPage(Handler):
    def get(self, path):
        self.write("We're making progress!")

class NotFound(Handler):
    def get(self, path):
        return self.notfound()

STORY_RE = r'([a-zA-Z0-9]*)'        
#STORY_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([('/', MainPage)], debug=True)

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/signup', Signup),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/thats-not-my-' + STORY_RE, StoryPage),
                               (STORY_RE, NotFound)
                               ],
                              debug=True)
