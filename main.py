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
import json
import urllib
import logging
import datetime as DT


API_TOKEN = '16367348484:58djnfjufjnfmfju88'
URL = 'https://api.telegram.org/bot{0}/'.format(API_TOKEN)
PROJECT_ID = 'telegram-bot-201215'

logger = logging.getLogger("SastaZomato")
logger.setLevel(logging.DEBUG)

ongoing_chats = []


# Utility functions to extract updates from Telegram
def get_text(update):
    return update["message"]["text"]


def get_chat_id(update):
    return update["message"]["chat"]["id"]


def get_name(update):
    return update["message"]["from"]["first_name"]


def get_result(update):
    return update["result"]


# Valid commands
commands = ["/book", "/view", "/cancel", "/call-us", "/request"]


def set_timeout(sec=60):
    urlfetch.set_default_fetch_deadline(sec)


def send_message(text, chat_id, reply_markup=None):
    url = URL + 'sendMessage'
    params = urllib.urlencode({
        "chat_id": chat_id,
        "text": text,
        "reply_markup": json.dumps(reply_markup)
    })

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    result = urlfetch.fetch(
        url=url,
        payload=params,
        method=urlfetch.POST,
        headers=headers)
    logger.info("Message status : {0}".format(result.content))


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World!')


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


class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        logger.info("Received request: %s from %s" % (self.request.url, self.request.remote_addr))
        if API_TOKEN not in self.request.url:
            # Not coming from Telegram
            logger.error("Post request without access_token from : %s" % self.request.remote_addr)
            return

        body = json.loads(self.request.body)
        chat_id = get_chat_id(body)

        try:
            text = get_text(body)
        except Exception as e:
            return

        # TODO : Handle updates from Telegram through states
        # states = ['waiting_for_count','waiting_for_date','waiting_for_time',
        # 'waiting_for_contact_details', 'scheduled']
        # TODO : Persist on-going conversation in Cloud Datastore
        # TODO : Code clean up
        # TODO : Add comments

        if text == "/bookatable":
            keyboard = [['2 People', '4 People'],
                        ['6 People', '8 People'],
                        ['10 People']]
            reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
            send_message("Hello %s! Booking for how many people?" % get_name(body), chat_id, reply_markup)
        elif text == "/reservations":
            send_message("Select a day : ", chat_id)
        else:
            send_message("Can't do anything : ", chat_id)


app = webapp2.WSGIApplication([
    ('/hello', MainPage),
    ('/about', MeHandler),
    ('/get_webhook', GetWebhookHandler),
    ('/del_webhook', DeleteWebhookHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/book.*', WebhookHandler)
], debug=True)