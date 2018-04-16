# Copyright 2016 Google Inc.
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

import webapp2
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import json
import urllib
import logging
from datetime import datetime
import datetime as DT

import re

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
API_TOKEN = 'sgsvgcvgs:8217276266236'
URL = 'https://api.telegram.org/bot{0}/'.format(API_TOKEN)
PROJECT_ID = 'telegram-bot-201215'

logger = logging.getLogger("SastaZomato")
logger.setLevel(logging.DEBUG)

ongoing_chats = []


class Chat(ndb.Model):
    """Models a Chat entry"""
    date = ndb.DateProperty()
    table_size = ndb.IntegerProperty()
    table_num = ndb.IntegerProperty()
    time = ndb.TimeProperty()
    state = ndb.StringProperty()
    user_id = ndb.StringProperty()
    user_email = ndb.StringProperty()


class UserDetails(ndb.Model):
    """Persists user details"""
    email = ndb.StringProperty()
    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()


# Utility functions to extract updates from Telegram
def get_text(update):
    return update["message"]["text"]


def get_chat_id(update):
    return update["message"]["chat"]["id"]


def get_name(update):
    return update["message"]["from"]["first_name"]


def get_result(update):
    return update["result"]


def set_timeout(sec=60):
    urlfetch.set_default_fetch_deadline(sec)


# Method to send message to the end user.
def send_message(text, chat_id, reply_markup=None):
    url = URL + 'sendMessage'
    payload = {"chat_id": chat_id, "text": text}

    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup)

    params = urllib.urlencode(payload)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    result = urlfetch.fetch(
        url=url,
        payload=params,
        method=urlfetch.POST,
        headers=headers)
    logger.info("Message status : {0}".format(result.content))


# Method to update Datastore Models defined above for Chat
def update_db(chat_dict, chat_info):
    if chat_info is None:
        chat_info = Chat(user_id=chat_dict.get('user_id'), user_email=chat_dict.get('user_email'), state=chat_dict.get('state'),
                       time=chat_dict.get('time'), table_num=chat_dict.get('table_num'), table_size=chat_dict.get('table_size'),
                       date=chat_dict.get('date'), id=chat_dict.get('id'))
    else:
        chat_info.user_id = chat_dict.get('user_id')
        chat_info.user_email = chat_dict.get('user_email')
        chat_info.date = chat_dict.get('date')
        chat_info.state = chat_dict.get('state')
        chat_info.time = chat_dict.get('time')
        chat_info.table_num = chat_dict.get('table_num')
        chat_info.table_size = chat_dict.get('table_size')
    chat_info.put()

    logger.info("Chat State : {0}".format(chat_dict.get('state')))


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World!')

# basic information about our bot.
class MeHandler(webapp2.RequestHandler):
    def get(self):
        url = URL + 'getMe'
        about_me = urlfetch.fetch(url)

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(about_me.content)


# Get information about webhook status read
class GetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        url = URL + 'getWebhookInfo'
        telegram_response = urlfetch.fetch(url)

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(telegram_response.content)


# Webhook url for Telegram to POST to
class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        hook_url = 'https://%s.appspot.com/book%s' % (PROJECT_ID, API_TOKEN)
        url = URL + 'setWebhook'
        data = {'url': hook_url}

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        result = urlfetch.fetch(
            url=url,
            payload=json.dumps(data),
            method=urlfetch.POST,
            headers=headers)

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(result.content)


# Remove webhook integration
class DeleteWebhookHandler(webapp2.RequestHandler):
    def get(self):
        url = URL + 'deleteWebhook'
        response_msg = urlfetch.fetch(url)

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(response_msg.content)


# Handle updates coming from Telegram : User interaction messages. Telegram will POST the body.
class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        logger.info("Received request: %s from %s" % (self.request.url, self.request.remote_addr))
        logger.info("Incoming body : %s " % (json.loads(self.request.body)))
        if API_TOKEN not in self.request.url:
            # Not coming from Telegram
            logger.error("Post request without access_token from : %s" % self.request.remote_addr)
            return

        body = json.loads(self.request.body)
        chat_id = get_chat_id(body)
        user_id = body["message"]["from"]["id"]
        first_name = body["message"]["from"]["first_name"]
        last_name = body["message"]["from"]["last_name"]
        try:
            text = get_text(body)
            chat_dict = {'id': chat_id, 'user_id': str(user_id)}

            # Query datastore, if chat_id exists
            chat_info = Chat.get_by_id(chat_id)
            logger.info("chat_info values : {0}".format(chat_info))
            if chat_info is None:
                if text == "/start":
                    response_message = "Welcome to Khaana Khazana - Real taste of Madhepur. Start the conversation " \
                                       "with /bookatable command. Let's see how it goes."
                    send_message("%s" % response_message, chat_id)
                elif text == "/bookatable":
                    keyboard = [['2 People', '4 People'],
                                ['6 People', '8 People'],
                                ['10 People']]
                    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
                    send_message("Hello %s! Booking for how many people?" % get_name(body), chat_id, reply_markup)

                    chat_dict['state'] = 'waiting_for_count'
                    update_db(chat_dict, chat_info)
                else:
                    send_message("Hello %s! Please start the conversation with /bookatable command." % get_name(body), chat_id)
            else:
                chat_dict = chat_info.to_dict()
                chat_state = chat_dict["state"]
                if chat_state == 'waiting_for_count':
                    today = DT.date.today()
                    keyboard = [[str(today + DT.timedelta(days=0)), str(today + DT.timedelta(days=1))],
                                [str(today + DT.timedelta(days=2)), str(today + DT.timedelta(days=3))],
                                [str(today + DT.timedelta(days=4)), str(today + DT.timedelta(days=5))],
                                [str(today + DT.timedelta(days=6))]]
                    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
                    send_message("Please select a date from the next seven days ", chat_id, reply_markup)

                    chat_dict['state'] = 'waiting_for_date'
                    chat_dict['table_size'] = int(text.split(" ")[0])
                    update_db(chat_dict, chat_info)
                elif chat_state == 'waiting_for_date':
                    input_date = datetime.strptime(text, "%Y-%m-%d")

                    # Opening time 2PM, Closing Time 11PM | Time slots 1 Hour
                    start_time = input_date.replace(hour=14, minute=00)
                    keyboard = [[str(start_time), str(start_time + DT.timedelta(hours=1))],
                                [str(start_time + DT.timedelta(hours=2)), str(start_time + DT.timedelta(hours=3))],
                                [str(start_time + DT.timedelta(hours=4)), str(start_time + DT.timedelta(hours=5))],
                                [str(start_time + DT.timedelta(hours=6)), str(start_time + DT.timedelta(hours=7))],
                                [str(start_time + DT.timedelta(hours=8)), str(start_time + DT.timedelta(hours=9))]]
                    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}

                    send_message("Please select a time-slot for %s " % input_date.strftime('%d %B %Y'), chat_id, reply_markup)
                    chat_dict['state'] = 'waiting_for_time'
                    chat_dict['date'] = input_date.date()
                    logger.info("chat_info values : {0}".format(chat_dict['date']))
                    update_db(chat_dict, chat_info)

                elif chat_state == 'waiting_for_time':
                    input_time = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
                    chat_dict['time'] = input_time.time()

                    # Check if it's an existing user.
                    user_info = UserDetails.get_by_id(user_id)
                    if user_info is None:
                        send_message("Please type your email address for confirmation message ", chat_id)
                        chat_dict['state'] = 'waiting_for_email'
                    else:
                        chat_dict['user_email'] = user_info.email
                        chat_dict['state'] = 'scheduled'
                        send_message("Booking completed with your existing email ID : %s \n"
                                     "Use /details command to fetch details and /cancel to cancel "
                                     "the reservation." % chat_dict['user_email'], chat_id)

                    logger.info("chat_info values : {0}".format(chat_dict['time']))
                    update_db(chat_dict, chat_info)

                elif chat_state == "waiting_for_email":
                    if not EMAIL_REGEX.match(text):
                        send_message("Invalid e-mail address, please type again ", chat_id)
                        return
                    else:
                        # Persist new user details.
                        new_user_info = UserDetails(first_name=first_name, last_name=last_name, email=text, id=user_id)
                        new_user_info.put()

                        chat_dict['state'] = 'scheduled'
                        chat_dict['user_email'] = text
                        update_db(chat_dict, chat_info)
                        send_message("Booking completed!  Use /details command to fetch details and /cancel to cancel "
                                     "the reservation..", chat_id)

                elif chat_state == "scheduled":
                    if text == "/cancel":
                        key = ndb.Key('Chat', int(chat_id))
                        key.delete()
                        send_message("Reservation cancelled.", chat_id)

                    if text == "/details":
                        booking_details = "Name : " + first_name + " " + last_name + "\n"
                        booking_details += "Table for : " + str(chat_dict["table_size"]) + " People.\n"
                        booking_details += "Date : " + str(chat_dict["date"]) + "\n"
                        booking_details += "Time : " + str(chat_dict["time"]) + "\n"

                        send_message("Booking details \n%s" % booking_details,  chat_id)
        except Exception as e:
            send_message("Bad news, %s - I crashed! I will be smarter one day. "
                         "Please start the conversation with /bookatable command." % get_name(body), chat_id)
            logger.info("Exception thrown : {}".format(e.message))
            return


app = webapp2.WSGIApplication([
    ('/hello', MainPage),
    ('/about', MeHandler),
    ('/get_webhook', GetWebhookHandler),
    ('/del_webhook', DeleteWebhookHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/book.*', WebhookHandler)
], debug=True)