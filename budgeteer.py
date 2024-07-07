"""
TODO: Update description of the file here
"""

# Flask imports
from flask import Flask, request, render_template
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

# Library imports
from itsdangerous import URLSafeTimedSerializer, URLSafeSerializer
import platform

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

  # # Initialize the database
  # app.db = Database(app.config['DATABASE_URI'])

  # @app.before_request
  # def before_request():
  #   print("BEFORE REQUEST")
  #   app.db.get_conn()

  # @app.teardown_appcontext
  # def close_db(exception=None):
  #   print("TEARDOWN APP CONTEXT")
  #   app.db.close_conn()

  # Error handler for HTTP exceptions (for ajax requests)
  @app.route('/error/<int:error_code>')
  def error_page(error_code):
      error_desc = request.args.get('errorDesc') # Fetch the errorDesc query parameter from the ajax request
      return render_template("error_page.html", message=f"Error {error_code}: {error_desc}"), error_code

  @app.errorhandler(404)
  def not_found(e):
    return render_template("error_page.html", message=f"404 Error: The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."), 404

  return app

if __name__ == '__main__':
  app_platform = platform.system()
  if app_platform == 'Windows':
    app = create_app("config.DevelopmentConfig")
    app.run()
  else:
    app = create_app("config.ProductionConfig")
    app.run()