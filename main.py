#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import cgi
import urllib
import webapp2
import jinja2
from google.appengine.api import users
from google.appengine.ext import ndb


JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions=['jinja2.ext.autoescape'])


def chapter_key():
	return ndb.key('LatePlate', "Alpha Tau")

def lateplate_key():
	return ndb.key('LatePlateRequest', 'LatePlates')


class Brother(ndb.Model):
	user = ndb.UserProperty()
	approved = ndb.BooleanProperty()
	admin = ndb.BooleanProperty()

class LatePlateRequest(ndb.Model):
	user = ndb.UserProperty()
	meal = ndb.StringProperty()
	request_time = ndb.DateTimeProperty()

class RecurringLatePlateRequest(LatePlateRequest):
	day_of_week = ndb.StringProperty()

class OneoffLatePlateRequest(LatePlateRequest):
	date = ndb.DateProperty()


class LatePlateHandler(webapp2.RequestHandler):


class MainHandler(webapp2.RequestHandler):

	def get(self):
		user = users.get_current_user()

		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))



app = webapp2.WSGIApplication([
	('/', MainHandler),
	('/request', LatePlateHandler),
	('/list', LatePlateHandler),
	('/me', LatePlateHandler)
], debug=True)
