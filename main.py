from cStringIO import StringIO
import json
import logging
import os

from google.appengine.api import urlfetch
import jinja2
import webapp2

from ext import triangulizor


class BaseHandler(webapp2.RequestHandler):

    def __init__(self, *args, **kwargs):
        super(BaseHandler, self).__init__(*args, **kwargs)
        template_dir = self.app.config.get('template_dir')
        loader = jinja2.FileSystemLoader(template_dir)
        self.jinja_env = jinja2.Environment(loader=loader)

    def render_string(self, template_path, ctx):
        template = self.jinja_env.get_template(template_path)
        return template.render(ctx)

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


class IndexHandler(BaseHandler):
    def get(self):
        return self.render('index.html')


class ImageCollectionHandler(BaseHandler):
    def get(self):
        pass

    def post(self):
        url = self.request.get('url')
        tile_size = int(self.request.get('tile_size') or 0)
        logging.info('Fetching %s', url)
        resp = urlfetch.fetch(url)
        logging.info('Got ~%dKB of data', len(resp.content) / 1024)
        image = triangulizor.triangulize(StringIO(resp.content), tile_size)
        self.response.headers['Content-Type'] = 'image/png'
        image.save(self.response.out, 'png')


class ImageHandler(BaseHandler):
    def get(self, key):
        pass


config = {
    'template_dir': os.path.join(os.path.dirname(__file__), 'templates'),
}

urls = [
    (r'^/$', IndexHandler),
    (r'^/images/$', ImageCollectionHandler),
    (r'^/images/([\w\-]+)$', ImageHandler),
]

app = webapp2.WSGIApplication(urls, config=config, debug=True)
