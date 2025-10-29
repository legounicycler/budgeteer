"""
budgeteer.py
This file contains the create_app function which starts the Flask app.
If you run this file directly, it will start the app. Depending on your platform,
the app will start with either the development config or the production config.
"""

# Flask imports
from flask import Flask, render_template
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

# Library imports
from itsdangerous import URLSafeTimedSerializer, URLSafeSerializer

# Custom imports
from database import *
from filters import balanceformat, datetimeformat, datetimeformatshort, inputformat
from blueprints.auth import auth_bp, login_manager
from blueprints.main import main_bp
from blueprints.error_handling import error_handling_bp
from secret import IS_PRODUCTION_MACHINE

def create_app(config_object="config.DevelopmentConfig"):
  app = Flask(__name__)
  app.config.from_object(config_object)

  # Initilze csrf extension (TODO: May not need this if all forms are Flask WTForms)
  app.extensions['csrf'] = CSRFProtect(app)

  # Initialize mail extension
  app.extensions['mail'] = Mail(app)

  # Initialize URLSafeTimedSerializer
  app.extensions['timed_serializer'] = URLSafeTimedSerializer(app.config['SECRET_KEY'])

  # Initialize URLSafeSerializer
  app.extensions['serializer'] = URLSafeSerializer(app.config['SECRET_KEY'])

  # Initalize the LoginManager extension
  login_manager.init_app(app)

  # Configure jinja filters
  app.jinja_env.filters['datetimeformat'] = datetimeformat
  app.jinja_env.filters['datetimeformatshort'] = datetimeformatshort
  app.jinja_env.filters['balanceformat'] = balanceformat
  app.jinja_env.filters['inputformat'] = inputformat

  # Register blueprints
  app.register_blueprint(auth_bp)
  app.register_blueprint(main_bp)
  app.register_blueprint(error_handling_bp)
  @app.errorhandler(404)
  def not_found(e):
      return render_template("error_page.html", message=f"404 Error: The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."), 404

  return app

if __name__ == '__main__':

  if IS_PRODUCTION_MACHINE:
    app = create_app("config.ProductionConfig")
  else:
    app = create_app("config.DevelopmentConfig")

  db = Database(app.config['DATABASE_URI'])
  db.get_conn()
  app.run()