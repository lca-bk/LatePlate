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

	member = ndb.KeyProperty()
	meal = ndb.StringProperty()	#	"Lunch" or "Linner"


class RecurringLatePlate(LatePlate):
	weekday = ndb.IntegerProperty()	#	0 = Monday, 6 = Sunday, etc

class OneoffLatePlate(LatePlate):
	date = ndb.DateProperty()


class Member(ndb.Model):
	name = ndb.StringProperty()
	user = ndb.UserProperty()
	

	@classmethod
	def from_user(cls, user):
		if user == None: return None

		member = Member.query(ancestor=chapter_key()).filter(Member.user==user).get()
		
		# if they don't exist yet, create
		if member == None:
			member = Member(parent=chapter_key(), user=user, name=user.nickname())
			member.put()

		return member


# redirects to login page and returns None if they're not logged in
# returns a Member if they are logged in
def require_member(handler):
	user = users.get_current_user()
	if user == None:
		handler.redirect(users.create_login_url(handler.request.uri))
		return None
	else:
		return Member.from_user(user)



class MyWebHandler(webapp2.RequestHandler):
	def errorOutWithString(self, errCode=500, errStr="The LatePlates are running late :("):
		sys.stderr.printLn("Error = " + errStr)
		self.response.write("The server has encountered an error")
		self.error(errCode)


class MemberHandler(MyWebHandler):

	# the update method changes the member's name
	def post(self):
		newName = self.request.get('name')
		if newName == None:
			self.error(404)

		#	Require user to sign in
		member = require_member(self)
		if member == None: return

		member.name = newName
		member.put()

		self.redirect('/me')


class MyPlatesHandler(MyWebHandler):
	# all of the user's recurring plates
	def member_schedule(self, member):
		schedule = {}
		for meal in LatePlate.Meals:
			schedule[meal] = []
			for weekday in range(5):
				plate = RecurringLatePlate.query(ancestor=chapter_key()).filter(RecurringLatePlate.weekday==weekday, LatePlate.member==member.key, LatePlate.meal==meal)
				schedule[meal].append(plate.count() > 0)

		return schedule


	# list of all of a member's oneoff plates
	def member_oneoff_listing(self, member):
		plates = OneoffLatePlate.query(ancestor=chapter_key()).filter(LatePlate.member==member.key)	#FIXME: only show non-expired late plates
		return plates


	def get(self):
		member = require_member(self)
		if member == None: return

		#	Populate the list of days available for oneoff request
		available_oneoff_days = []
		day = datetime.date.today()
		while len(available_oneoff_days) < 3:
			if day.weekday() < 5:
				available_oneoff_days.append(day)
			day += datetime.timedelta(days=1)

		sys.stderr.write(str(self.member_schedule(member)))

		template_values = {
			'available_oneoff_days': available_oneoff_days,
			'available_days': LatePlate.WeekdayNames,
			'meals': LatePlate.Meals,
			'recurring_plates': self.member_schedule(member),
			'oneoff_listing': self.member_oneoff_listing(member),
			'member': member
		}
		template = JINJA_ENVIRONMENT.get_template('user.html')
		self.response.write(template.render(template_values))


class ScheduleHandler(MyWebHandler):

	def post(self):
		#	Require login
		member = require_member(self)

		#	trash all the old recurring plates
		prev_recurr = RecurringLatePlate.query(ancestor=chapter_key())#chapter_key()).filter(LatePlate.member == member)
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
							p = RecurringLatePlate(
									parent=member.key,
									member=member.key,
								 	meal=meal,
								 	weekday=weekday)
							p.put()
							# sys.stderr.write("Scheduled " + meal + LatePlate.WeekdayNames[weekday] + "\n")

		except:
			self.error(500)
			return

		self.redirect("/me")


class OneoffRequestHandler(MyWebHandler):
	
	def request_plate(self, member):
		date = self.request.get('date')
		date = datetime.datetime.strptime(date, '%m/%d/%Y').date()

		meal = self.request.get('meal')

		if meal not in LatePlate.Meals:
			self.response.write("Invalid meal: '" + meal +"'")
			return

		# prevent duplicate oneoff requests
		if OneoffLatePlate.query(ancestor=member.key).filter(LatePlate.meal==meal, OneoffLatePlate.date==date).count() > 0:
			self.response.write("Duplicate")
			return

		#	Create and save the late plate
		plate = OneoffLatePlate(parent=member.key, meal=meal, member=member.key, date=date)
		plate.put()

		self.redirect("/me")


	def post(self):
		member = require_member(self)
		if member == None: return

		action = self.request.get('action')
		if action == "delete":
			self.delete_plate(member)
		elif action == "create":
			self.request_plate(member)
		else:
			self.error(404)

	def delete_plate(self, member):
		plateIDStr = self.request.get('plate_id')
		plate_id = int(plateIDStr)
		plate = OneoffLatePlate.get_by_id(id=plate_id, parent=member.key)

		if plate == None:
			self.errorOutWithString(404, "Unable to locate plate with the given id: '" + plateIDStr + "'")
			return

		plate.key.delete()

		self.redirect("/me")

class ContactHandler(MyWebHandler):
	def get(self):
		template = JINJA_ENVIRONMENT.get_template('contact.html')
		self.response.write(template.render())

class MenuHandler(MyWebHandler):
	def get(self):
		template = JINJA_ENVIRONMENT.get_template('menu.html')
		self.response.write(template.render())

class MainHandler(MyWebHandler):

	def get(self):
		date = datetime.date.today()
		weekday = date.weekday()

		plates = {}

		recurring_plates_query = RecurringLatePlate.query(ancestor=chapter_key()).filter(RecurringLatePlate.weekday==weekday)
		oneoff_plates_query = OneoffLatePlate.query(ancestor=chapter_key())

		for meal in LatePlate.Meals:
			oneoffs = oneoff_plates_query.filter(LatePlate.meal==meal)
			recurrings = recurring_plates_query.filter(LatePlate.meal==meal)
			plates[meal] = [l for l in oneoffs] + [l for l in recurrings]

		template_values = {
			'plates': plates,
			'date': date
		}
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
	('/', MainHandler),
	('/me', MyPlatesHandler),
	('/schedule', ScheduleHandler),
	('/request', OneoffRequestHandler),
	('/member', MemberHandler),
	('/contact', ContactHandler),
	('/menu', MenuHandler)
], debug=True)
