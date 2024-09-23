from flask import Blueprint

auth_routes = Blueprint('auth_routes', __name__)

# Import all the views (routes) after initializing the Blueprint
from .routes import *
