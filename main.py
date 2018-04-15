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
import webapp2
import logging
import json
from google.appengine.api import urlfetch


_API_TOKEN = '123456789:32145djdfnmjffnnmf'
_URL = "https://api.telegram.org/bot{0}/".format(_API_TOKEN)
_PROJECT_ID = "telegram-bot-reservations"

logger = logging.getLogger("SastaZomato")
logger.setLevel(logging.DEBUG)


# Utility functions to extract updates from Telegram
def get_text(update):
    return update["message"]["text"]


def get_chat_id(update):
    return update["message"]["chat"]["id"]


def get_name(update):
    return update["message"]["from"]["first_name"]


def get_result(update):
    return update["result"]


# Accepted commands
commands = ["/book", "/view", "/cancel", "/call-us", "/request"]


def set_timeout(sec=60):
    urlfetch.set_default_fetch_deadline(sec)


def format_response(obj):
    parsed = json.load(obj)
    return json.dumps(parsed, indent=4, sort_keys=True)


def send_message(text, chat_id):
    params = {
        "chat_id": str(chat_id),
        "text": text.encode("utf-8"),
        "parse_mode": "Markdown",
    }

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    result = urlfetch.fetch(
        url=_URL + "sendMessage",
        payload=params,
        method=urlfetch.POST,
        headers=headers)
    print result.content


# Return basic information about the bot
class MeHandler(webapp2.RequestHandler):
    def get(self):
        set_timeout()
        url = _URL + "getMe"
        about_me = urlfetch.fetch(url)

        self.response.headers["Content-Type"] = "text/plain"
        self.response.write(format_response(about_me))


# Get information about webhook status
class GetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        set_timeout()
        url = _URL + "getWebhookInfo"
        telegram_response =  urlfetch.fetch(url)

        self.response.headers["Content-Type"] = "text/plain"
        self.response.write(format_response(telegram_response))


# Set a webhook url for Telegram to POST to
class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        set_timeout()
        hook_url = "https://%s.appspot.com/book%s" % (_PROJECT_ID, _API_TOKEN)
        logger.info("Setting new webhook to: %s" % hook_url)

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response_msg = urlfetch.fetch(
            url=_URL + "setWebhook",
            payload={"url": hook_url},
            method=urlfetch.POST,
            headers=headers)

        self.response.headers["Content-Type"] = "text/plain"
        self.response.write(format_response(response_msg))


# Remove webhook integration
class DeleteWebhookHandler(webapp2.RequestHandler):
    def get(self):
        set_timeout()
        url = _URL + "deleteWebhook"
        response_msg = urlfetch.fetch(url)

        self.response.headers["Content-Type"] = "text/plain"
        self.response.write(format_response(response_msg))


class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        set_timeout()
        logger.info("Received request: %s from %s" % (self.request.url, self.request.remote_addr))

        if _API_TOKEN not in self.request.url:
            # Not coming from Telegram
            logger.error("Post request without access_token from : %s" % self.request.remote_addr)
            return

        body = json.loads(self.request.body)

        chat_id = get_chat_id(body)
        logger.info("Response body: " + str(body))

        try:
            text = get_text(body)
        except Exception as e:
            logger.info("No text field in update. Try to get location")
            return

        if text == "/bookatable":
            send_message("Hello %s! Why not try the commands below:" % get_name(body), chat_id)

        elif text == "/reservations":
            send_message("Select a day : ", chat_id)

        else:
            send_message("Can't do anything : ", chat_id)


app = webapp2.WSGIApplication([
    ('/', MeHandler),
    ('/book.*', WebhookHandler)
], debug=True)
