import logging

import webapp2

import handlers





# Set up logging.
logging.getLogger().setLevel(logging.DEBUG)


# Route mapping.
routes = [
    webapp2.Route(r'/', handlers.HomePageHandler, name='home'),
    webapp2.Route(r'/api/v1/json', handlers.ApiHandler, name='api'),


]

# Run the app.
app = webapp2.WSGIApplication(routes, debug=True)
