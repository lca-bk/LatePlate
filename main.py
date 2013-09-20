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
from datetime import datetime
from google.appengine.api import users
from google.appengine.ext import ndb


JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions=['jinja2.ext.autoescape'])


def chapter_key():
	return ndb.Key('LatePlate', "Alpha Tau")

def lateplate_key():
	return ndb.Key('LatePlate', 'LatePlates')


class Brother(ndb.Model):
	user = ndb.UserProperty()
	approved = ndb.BooleanProperty()
	admin = ndb.BooleanProperty()

class LatePlate(ndb.Model):
	user = ndb.UserProperty()
	meal = ndb.StringProperty()
	request_time = ndb.DateTimeProperty()

class RecurringLatePlate(LatePlate):
	day_of_week = ndb.StringProperty()

class OneoffLatePlate(LatePlate):
	date = ndb.DateProperty()


class LatePlateHandler(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()

		oneoff_days_list = ["today", "tomorrow", "the next day"]

		if user == None:
			self.redirect(users.create_login_url(self.request.uri))
			return

		oneoff_list = []

		template_values = {
			'oneoff_days_list': oneoff_days_list,
			'user': user,
			'oneoff_list': oneoff_list
		}
		template = JINJA_ENVIRONMENT.get_template('user.html')
		self.response.write(template.render(template_values))


	def post(self):
		user = users.get_current_user()

		if user == None:
			self.redirect(users.create_login_url(self.request.uri))
			return


class MainHandler(webapp2.RequestHandler):

	def get(self):
		user = users.get_current_user()

		day = datetime.now()
		ancestor_key = chapter_key()



		n = OneoffLatePlate(parent=ancestor_key, date=datetime.now(), meal="lunch")
		n.put()


		oneoff_plates = OneoffLatePlate.query(ancestor=ancestor_key)

		lunch_plates = oneoff_plates.filter(OneoffLatePlate.meal == "lunch")
		dinner_plates = oneoff_plates.filter(OneoffLatePlate.meal == "dinner")


		template_values = {
			'lunch_plates': lunch_plates,
			'dinner_plates': dinner_plates
		}
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))



app = webapp2.WSGIApplication([
	('/', MainHandler),
	('/request', LatePlateHandler),
	('/list', LatePlateHandler),
	('/me', LatePlateHandler)
], debug=True)
