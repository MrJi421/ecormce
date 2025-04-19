# File: /ecommerce-flask-app/ecommerce-flask-app/src/routes/__init__.py

from flask import Blueprint

# Initialize the routes blueprint
routes = Blueprint('routes', __name__)

# Import routes to register them
from . import auth, products, cart, orders