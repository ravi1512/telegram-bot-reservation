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

import json
import urllib
import logging
from datetime import datetime
import datetime as DT
import re


import webapp2
from google.appengine.api import urlfetch
from google.appengine.api import mail
from google.appengine.ext import ndb


EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
API_TOKEN = 'f123456789:onhyyf7fdndkidi9HSDHHDH'
URL = 'https://api.telegram.org/bot{0}/'.format(API_TOKEN)
PROJECT_ID = 'telegram-bot-201215'

logger = logging.getLogger("SastaZomato")
logger.setLevel(logging.DEBUG)


class Chat(ndb.Model):
    """Models a Chat entry"""
    date = ndb.DateProperty()
    table_size = ndb.IntegerProperty()
    table_num = ndb.IntegerProperty()
    time = ndb.TimeProperty()
    state = ndb.StringProperty()
    user_id = ndb.StringProperty()
    user_email = ndb.StringProperty()
    first_name = ndb.StringProperty()


class UserDetails(ndb.Model):
    """Persists user details"""
    email = ndb.StringProperty()
    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()


def set_timeout(sec=60):
    """Set timeout."""
    urlfetch.set_default_fetch_deadline(sec)


def send_message(text, chat_id, reply_markup=None):
    """Method to send message to the end user."""
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


def send_mail_to_user(email_id, operation, chat_dict):
    """Method to send email to the end user."""
    logger.info("Preparing email body")
    subject = "Booking " + operation + " at Khaana Khazana"
    booking_details = "Table for : " + str(chat_dict["table_size"]) + " People.\n"
    booking_details += "Date : " + str(chat_dict["date"]) + "\n"
    booking_details += "Time : " + str(chat_dict["time"])

    message_body = "Dear {0}, your booking details are as follows - \n{1} \n\n" \
                   "Yours, \nKhaana Khazana Team".format(chat_dict['first_name'], booking_details)

    mail.send_mail(sender='noreply@{0}.appspotmail.com'.format(PROJECT_ID),
                   to=email_id,
                   subject=subject,
                   body=message_body)


def update_db(chat_dict, chat_info):
    """Method to update Datastore Models defined above for Chat"""
    if chat_info is None:
        chat_info = Chat(user_id=chat_dict.get('user_id'), user_email=chat_dict.get('user_email'),
                         table_num=chat_dict.get('table_num'), time=chat_dict.get('time'),
                         state=chat_dict.get('state'), table_size=chat_dict.get('table_size'),
                         date=chat_dict.get('date'), first_name=chat_dict.get('first_name'),
                         id=chat_dict.get('id'))
    else:
        chat_info.user_id = chat_dict.get('user_id')
        chat_info.user_email = chat_dict.get('user_email')
        chat_info.date = chat_dict.get('date')
        chat_info.state = chat_dict.get('state')
        chat_info.time = chat_dict.get('time')
        chat_info.table_num = chat_dict.get('table_num')
        chat_info.table_size = chat_dict.get('table_size')
        chat_info.first_name = chat_dict.get('first_name')

    chat_info.put()
    logger.info("Chat State : {0}".format(chat_dict.get('state')))


def get_keyboard(keyboard_type, input_date):
    """Returns Keyboard structure for date and time input in a Chat"""
    if keyboard_type == "date":
        today = DT.date.today()
        keyboard = [[str(today + DT.timedelta(days=0)), str(today + DT.timedelta(days=1))],
                    [str(today + DT.timedelta(days=2)), str(today + DT.timedelta(days=3))],
                    [str(today + DT.timedelta(days=4)), str(today + DT.timedelta(days=5))],
                    [str(today + DT.timedelta(days=6))]]
    else:
        # Opening time 2PM, Closing Time 11PM | Time slots 1 Hour
        start_time = input_date.replace(hour=14, minute=00)
        keyboard = [[str(start_time), str(start_time + DT.timedelta(hours=1))],
                    [str(start_time + DT.timedelta(hours=2)), str(start_time + DT.timedelta(hours=3))],
                    [str(start_time + DT.timedelta(hours=4)), str(start_time + DT.timedelta(hours=5))],
                    [str(start_time + DT.timedelta(hours=6)), str(start_time + DT.timedelta(hours=7))],
                    [str(start_time + DT.timedelta(hours=8)), str(start_time + DT.timedelta(hours=9))]]
    return keyboard


class MainPage(webapp2.RequestHandler):
    """Check if Application is working with Hello, World!"""
    def get(self):
        """RequestHandler's GET Method."""
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World!')


class MeHandler(webapp2.RequestHandler):
    """Basic information about our bot."""
    def get(self):
        """RequestHandler's GET Method."""
        url = URL + 'getMe'
        about_me = urlfetch.fetch(url)

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(about_me.content)


class GetWebhookHandler(webapp2.RequestHandler):
    """Get information about webhook status read."""
    def get(self):
        """RequestHandler's GET Method."""
        url = URL + 'getWebhookInfo'
        telegram_response = urlfetch.fetch(url)

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(telegram_response.content)


class SetWebhookHandler(webapp2.RequestHandler):
    """Webhook url for Telegram to POST to"""
    def get(self):
        """RequestHandler's GET Method."""
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


class DeleteWebhookHandler(webapp2.RequestHandler):
    """Remove webhook integration"""
    def get(self):
        """RequestHandler's GET Method."""
        url = URL + 'deleteWebhook'
        response_msg = urlfetch.fetch(url)

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(response_msg.content)


class WebhookHandler(webapp2.RequestHandler):
    """Handle updates coming from Telegram : User interaction messages and flow.
    Telegram will POST the body."""
    def post(self):
        """RequestHandler's POST Method."""
        logger.info("Received request: {0} from {1}"
                    .format(self.request.url, self.request.remote_addr))

        if API_TOKEN not in self.request.url:
            # Not coming from Telegram
            logger.error("Post request without access_token from : {0}"
                         .format(self.request.remote_addr))
            return

        # Get chat details from received chat body, from Telegram.
        body = json.loads(self.request.body)
        chat_id = body["message"]["chat"]["id"]
        user_id = body["message"]["from"]["id"]
        first_name = body["message"]["from"]["first_name"]
        last_name = body["message"]["from"]["last_name"]

        try:
            text = body["message"]["text"]
            chat_dict = {'id': chat_id, 'user_id': str(user_id), 'first_name': first_name}

            # Query datastore, if chat_id exists
            chat_info = Chat.get_by_id(chat_id)

            # New user
            if chat_info is None:
                # Show the welcome message.
                if text == "/start":
                    response_message = "Welcome to Khaana Khazana - Real taste of Madhepur. " \
                                       "Start the conversation with /bookatable command. " \
                                       "Let's see how it goes."
                    send_message("{0}".format(response_message), chat_id)

                # Start the conversation with end-user.
                elif text == "/bookatable":
                    keyboard = [['2 People', '4 People'],
                                ['6 People', '8 People'],
                                ['10 People']]
                    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
                    send_message("Hello {0}! Booking for how many people?"
                                 .format(first_name), chat_id, reply_markup)

                    chat_dict['state'] = 'waiting_for_count'
                    update_db(chat_dict, chat_info)
                else:
                    send_message("Hello {0}! Please start the conversation with /bookatable "
                                 "command.".format(first_name), chat_id)
            else:
                chat_dict = chat_info.to_dict()
                chat_state = chat_dict["state"]

                # Waiting for table size.
                if chat_state == 'waiting_for_count':
                    try:
                        people_count = int(text.split(" ")[0])
                    except Exception as exc:
                        send_message("Uh-Oh! Invalid input. Choose values from my keyboard!",
                                     chat_id)
                        return

                    keyboard = get_keyboard("date", None)
                    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
                    send_message("Please select a date from the next seven days ", chat_id, reply_markup)

                    chat_dict['state'] = 'waiting_for_date'
                    chat_dict['table_size'] = people_count
                    update_db(chat_dict, chat_info)

                # Waiting for reservation date.
                elif chat_state == 'waiting_for_date':
                    try:
                        input_date = datetime.strptime(text, "%Y-%m-%d")
                    except Exception as exc:
                        send_message("Uh-Oh! Invalid input. Choose values from my keyboard!", chat_id)
                        return

                    keyboard = get_keyboard("time", input_date)
                    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}

                    send_message("Please select a time-slot for {0}".format(input_date.strftime('%d %B %Y')),
                                 chat_id, reply_markup)

                    chat_dict['state'] = 'waiting_for_time'
                    chat_dict['date'] = input_date.date()
                    update_db(chat_dict, chat_info)

                # Waiting to accept a time-slot from the end-user, from pre-defined time slots in our keyboard.
                elif chat_state == 'waiting_for_time':
                    try:
                        input_time = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
                    except Exception as exc:
                        send_message("Uh-Oh! Invalid input. Choose values from my keyboard!", chat_id)
                        return

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
                                     "the reservation. You will be receiving an email shortly."
                                     % chat_dict['user_email'], chat_id)
                        send_mail_to_user(chat_dict['user_email'], 'success', chat_dict)

                    logger.info("chat_info values : {0}".format(chat_dict['time']))
                    update_db(chat_dict, chat_info)

                # Waiting for email value from user for booking confirmation.
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
                        send_mail_to_user(text, 'success', chat_dict)
                        send_message("Booking completed!  Use /details command to fetch details and /cancel to cancel "
                                     "the reservation. You will be receiving an email shortly.", chat_id)
                # Booking completed. Only two commands are supported after successful booking.
                elif chat_state == "scheduled":
                    if text == "/cancel":
                        send_mail_to_user(chat_dict['user_email'], 'cancelled', chat_dict)
                        key = ndb.Key('Chat', int(chat_id))
                        key.delete()
                        send_message("Reservation cancelled. You will be receiving an email shortly.", chat_id)

                    elif text == "/details":
                        booking_details = "Name : " + first_name + " " + last_name + "\n"
                        booking_details += "Table for : " + str(chat_dict["table_size"]) + " People.\n"
                        booking_details += "Date : " + str(chat_dict["date"]) + "\n"
                        booking_details += "Time : " + str(chat_dict["time"]) + "\n"

                        send_message("Booking details \n%s" % booking_details, chat_id)
                    else:
                        send_message("Booking completed by your name. To modify, "
                                     "first /cancel and then /bookatable again. "
                                     "/details command to fetch booking details.", chat_id)
        except Exception as exc:
            send_message("Bad news, %s - I crashed! I will be smarter one day. "
                         "Please start the conversation with /bookatable command." % first_name, chat_id)

            # Exception occured, delete on-going conversation. Hope for a fresh start!
            key = ndb.Key('Chat', int(chat_id))
            key.delete()

            # Log the exception and return.
            logger.info("Exception thrown : {0}".format(exc.message))
            return


app = webapp2.WSGIApplication([
    ('/hello', MainPage),
    ('/about', MeHandler),
    ('/get_webhook', GetWebhookHandler),
    ('/del_webhook', DeleteWebhookHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/book.*', WebhookHandler)
], debug=True)
