"""
TODO: Update description of the file here
"""

# Flask imports
from flask import Flask, current_app
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

# Library imports
from itsdangerous import URLSafeTimedSerializer, URLSafeSerializer

# Custom imports
from database import *
from filters import balanceformat, datetimeformat, datetimeformatshort, inputformat
from blueprints.auth import auth_bp, login_manager
from blueprints.main import main_bp

def create_app(config_object="config.DevelopmentConfig"):
  app = Flask(__name__)
  app.config.from_object(config_object)

  # Initilze csrf extension (TODO: May not need this if all forms are Flask WTForms)
  csrf = CSRFProtect(app)
  app.csrf = csrf

  # Initialize mail extension
  mail = Mail(app)
  app.mail = mail

  # Initialize URLSafeTimedSerializer
  timed_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
  app.timed_serializer = timed_serializer

  # Initialize URLSafeSerializer
  serializer = URLSafeSerializer(app.config['SECRET_KEY'])
  app.serializer = serializer

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

  return app

#MAKES SURE DEBUG IS TURNED OFF FOR MAIN DEPLOYMENT
if __name__ == '__main__':
  app = create_app()
  if app_platform == 'Windows':
      app.run(debug=True)
  else:
    app.run(debug=False)