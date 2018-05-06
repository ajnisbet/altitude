import sys

from google.appengine.ext import vendor
from google.appengine.ext.appstats import recording


# Enable appstats performance monitoring.
def webapp_add_wsgi_middleware(app):
    app = recording.appstats_wsgi_middleware(app)
    return app