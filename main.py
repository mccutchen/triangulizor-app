from cStringIO import StringIO
import json
import logging
import pprint
import os

from google.appengine.api import urlfetch
import jinja2
import webapp2
import webapp2_extras.sessions

from ext import triangulizor

import secrets


class BaseHandler(webapp2.RequestHandler):

    def __init__(self, *args, **kwargs):
        super(BaseHandler, self).__init__(*args, **kwargs)
        template_dir = self.app.config.get('template_dir')
        loader = jinja2.FileSystemLoader(template_dir)
        self.jinja_env = jinja2.Environment(loader=loader)

    def dispatch(self, *args, **kwargs):
        self.session_store = webapp2_extras.sessions.get_store(
            request=self.request)
        try:
            super(BaseHandler, self).dispatch(*args, **kwargs)
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session()

    def render_string(self, template_path, ctx):
        final_ctx = self.get_default_context()
        final_ctx.update(ctx)
        template = self.jinja_env.get_template(template_path)
        return template.render(final_ctx)

    def render(self, template_path, ctx=None, status=200):
        body = self.render_string(template_path, ctx or {})
        return self.respond(body, status, 'text/html; charset=utf-8')

    def respond_json(self, data, status=200):
        body = json.dumps(data)
        return self.respond(body, status, 'application/json')

    def respond(self, body, status, content_type):
        self.response.headers['Content-Type'] = content_type
        self.response.set_status(status)
        self.response.out.write(body)

    def get_default_context(self):
        return {
            'flashes': self.session.get_flashes(),
            'pformat': pprint.pformat,
        }


class IndexHandler(BaseHandler):
    def get(self):
        return self.render('index.html')


class ImageCollectionHandler(BaseHandler):
    def get(self):
        pass

    def post(self):
        url = self.request.get('url')
        if not url:
            return self.error('Missing URL.')

        try:
            tile_size = int(self.request.get('tile_size') or 0)
        except ValueError:
            return self.error('Tile size must be a number or left blank.')

        logging.info('Fetching %s', url)
        try:
            resp = urlfetch.fetch(url)
        except urlfetch.InvalidURLError:
            return self.error('Invalid URL.')

        image_size = len(resp.content)
        content_type = resp.headers.get('Content-Type')
        logging.info('Got ~%dKB of %s data', image_size / 1024, content_type)

        if resp.status_code != 200:
            msg = 'Error fetching URL: HTTP %s', resp.status_code
            return self.error(msg)

        if image_size > self.app.config['max_file_size']:
            msg = 'Max image size is %dKB (got %dKB)' % (
                self.app.config['max_file_size'] / 1024, image_size / 1024)
            return self.error(msg)

        image = triangulizor.triangulize(StringIO(resp.content), tile_size)
        self.response.headers['Content-Type'] = 'image/png'
        image.save(self.response.out, 'png')

    def error(self, msg):
        self.session.add_flash(msg, 'error')
        ctx = {
            'url': self.request.get('url'),
            'tile_size': self.request.get('tile_size'),
        }
        return self.render('index.html', ctx, status=400)


class ImageHandler(BaseHandler):
    def get(self, key):
        pass


config = {
    'template_dir': os.path.join(os.path.dirname(__file__), 'templates'),
    'max_file_size': 1024 * 1000 * 1, # 1MB
    'webapp2_extras.sessions': {
        'secret_key': secrets.secret_key,
    },
}

urls = [
    (r'^/$', IndexHandler),
    (r'^/images/$', ImageCollectionHandler),
    (r'^/images/([\w\-]+)$', ImageHandler),
]

app = webapp2.WSGIApplication(urls, config=config, debug=True)
