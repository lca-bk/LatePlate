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
import sys
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


class LatePlate(ndb.Model):
	Meals = ["Lunch", "Dinner"]
	Weekdays = range(5)
	WeekdayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

	user = ndb.UserProperty()
	meal = ndb.StringProperty()	#	"lunch" or "dinner"


class RecurringLatePlate(LatePlate):
	weekday = ndb.IntegerProperty()	#	0 = Monday, 6 = Sunday, etc

class OneoffLatePlate(LatePlate):
	date = ndb.DateProperty()


class MyPlatesHandler(webapp2.RequestHandler):
	def user_schedule(self, user):
		schedule = {}
		for meal in LatePlate.Meals:
			schedule[meal] = []
			for weekday in range(5):
				plate = RecurringLatePlate.query(ancestor=chapter_key()).filter(RecurringLatePlate.weekday==weekday, LatePlate.user==user, LatePlate.meal==meal)
				schedule[meal].append(plate.count() > 0)
				# sys.stderr.write(str(plate))
				# sys.stderr.write("count = " + str(plate.count()))

		return schedule


	def user_oneoff_listing(self, user):
		plates = OneoffLatePlate.query(ancestor=chapter_key()).filter(LatePlate.user==user)	#FIXME: only show non-expired late plates
		return plates

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

		sys.stderr.write(str(self.user_schedule(user)))

		template_values = {
			'available_oneoff_days': available_oneoff_days,
			'user': user,
			'available_days': LatePlate.WeekdayNames,
			'meals': LatePlate.Meals,
			'recurring_plates': self.user_schedule(user),
			'oneoff_listing': self.user_oneoff_listing(user)
		}
		template = JINJA_ENVIRONMENT.get_template('user.html')
		self.response.write(template.render(template_values))


class ScheduleHandler(webapp2.RequestHandler):

	def post(self):
		#	Require login
		user = users.get_current_user()
		if user == None:
			self.redirect(users.create_login_url(self.request.uri))
			return

		#	trash all the old recurring plates
		prev_recurr = RecurringLatePlate.query(ancestor=chapter_key()).filter(LatePlate.user == user)
		for old_plate in prev_recurr:
			old_plate.key.delete()

		#	Add all the new scheduled plates
		try:
			for meal in LatePlate.Meals:
				for weekday in LatePlate.Weekdays:
					argKey = meal + "[" + str(weekday) + "]"
					if argKey in self.request.POST:
						val = self.request.POST[argKey] == "on"

						if val == True:
							p = RecurringLatePlate(parent=chapter_key(), user=user, meal=meal, weekday=weekday)
							p.put()
							sys.stderr.write("Scheduled " + meal + LatePlate.WeekdayNames[weekday] + "\n")

		except:
			self.error(500)
			return

		self.redirect("/me")


class OneoffRequestHandler(webapp2.RequestHandler):
	
	def request_plate(self, user):
		date = self.request.get('date')
		date = datetime.datetime.strptime(date, '%m/%d/%Y').date()

		meal = self.request.get('meal')
		# self.response.write("meal: " + meal)
		# return webapp2.Response("meal: " + meal)

		if meal not in LatePlate.Meals:
			self.response.write("Invalid meal" + meal)
			return

		#	Create and save the late plate
		plate = OneoffLatePlate(parent=chapter_key(), meal=meal, user=user, date=date)
		plate.put()

		self.redirect("/me")


	def post(self):
		user = users.get_current_user()
		if user == None:
			self.redirect(users.create_login_url(self.request.uri))
			return

		action = self.request.get('action')
		if action == "delete":
			self.delete_plate(user)
		elif action == "create":
			self.request_plate(user)
		else:
			self.error(404)

	def delete_plate(self, user):
		plate_id = int(self.request.get('plate_id'))
		plate = OneoffLatePlate.get_by_id(id=plate_id, parent=chapter_key())

		if plate == None:
			self.error(404)
			return

		plate.key.delete()

		self.redirect("/me")


class MainHandler(webapp2.RequestHandler):

	def get(self):
		user = users.get_current_user()


		date = datetime.date.today()

		weekday = date.weekday()

		recurring_plates = RecurringLatePlate.query(ancestor=chapter_key()).filter(RecurringLatePlate.weekday==weekday, LatePlate.user==user)
		recurring_lunches = recurring_plates.filter(LatePlate.meal=="Lunch")
		recurring_dinners = recurring_plates.filter(LatePlate.meal=="Dinner")

		oneoff_plates = OneoffLatePlate.query(ancestor=chapter_key())
		oneoff_lunches = oneoff_plates.filter(OneoffLatePlate.meal == "Lunch")
		oneoff_dinners = oneoff_plates.filter(OneoffLatePlate.meal == "Dinner")


		template_values = {
			'lunch_plates': [l for l in oneoff_lunches] + [l for l in recurring_lunches],
			'dinner_plates': [d for d in oneoff_dinners] + [d for d in recurring_dinners],
			'day_desc': date.strftime("%m/%d/%Y")
		}
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
	('/', MainHandler),
	('/me', MyPlatesHandler),
	('/schedule', ScheduleHandler),
	('/request', OneoffRequestHandler)
], debug=True)
