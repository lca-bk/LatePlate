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
import datetime
from google.appengine.api import users
from google.appengine.ext import ndb


JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions=['jinja2.ext.autoescape'])


def chapter_key():
	return ndb.Key('LatePlate', "Alpha Tau")


def available_days():
	return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


class LatePlate(ndb.Model):
	user = ndb.UserProperty()
	meal = ndb.StringProperty()	#	"lunch" or "dinner"

class RecurringLatePlate(LatePlate):
	weekday = ndb.IntegerProperty()	#	0 = Monday, 6 = Sunday, etc

class OneoffLatePlate(LatePlate):
	date = ndb.DateProperty()


class MyPlatesHandler(webapp2.RequestHandler):
	def get(self):
		#	Require user to sign in
		user = users.get_current_user()
		if user == None:
			self.redirect(users.create_login_url(self.request.uri))
			return

		#	Populate the list of days available for oneoff request
		available_oneoff_days = []
		day = datetime.date.today()
		while len(available_oneoff_days) < 3:
			if day.weekday() < 5:
				available_oneoff_days.append(day)
			day += datetime.timedelta(days=1)


		template_values = {
			'available_oneoff_days': available_oneoff_days,
			'user': user,
			'available_days': available_days()
		}
		template = JINJA_ENVIRONMENT.get_template('user.html')
		self.response.write(template.render(template_values))


class ScheduleHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		if user == None:
			self.redirect(users.create_login_url(self.request.uri))
			return

		#	trash all the old recurring plates
		prev_recurr = RecurringLatePlate.query(ancestor_key=chapter_key()).filter(LatePlate.user == user)
		for old_plate in prev_recurr:
			old_plate.delete()



		# FIXME: set new recurring


class OneoffRequestHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		if user == None:
			self.redirect(users.create_login_url(self.request.uri))
			return

		date = self.request.get('date')
		date = datetime.datetime.strptime(date, '%m/%d/%Y').date()

		meal = self.request.get('meal')
		# self.response.write("meal: " + meal)
		# return webapp2.Response("meal: " + meal)

		if meal != "lunch" and meal != "dinner":
			self.redirect(500)
			return

		#	Create and save the late plate
		plate = OneoffLatePlate(parent=chapter_key(), meal=meal, user=user, date=date)
		plate.put()

		self.redirect("/me")


class MainHandler(webapp2.RequestHandler):

	def get(self):
		user = users.get_current_user()


		date = datetime.date.today()
		ancestor_key = chapter_key()


		# make a dummy lateplate
		# n = OneoffLatePlate(parent=ancestor_key, date=datetime.now(), meal="lunch")
		# n.put()


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
	('/me', MyPlatesHandler),
	('/schedule', ScheduleHandler),
	('/request', OneoffRequestHandler)
], debug=True)
