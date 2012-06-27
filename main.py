import webapp2
from ext import triangulizor


class TriangulizorHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        return self.response.out.write('OK')


urls = [
    (r'^/$', TriangulizorHandler),
]
app = webapp2.WSGIApplication(urls, debug=True)
