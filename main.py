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

API_TOKEN = '12344jk5rj:9838uu4u4u'
URL = 'https://api.telegram.org/bot{0}/'.format(API_TOKEN)


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


app = webapp2.WSGIApplication([
    ('/hello', MainPage),
    ('/about', MeHandler)
], debug=True)