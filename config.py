from secret import SECRET_KEY, MAIL_PASSWORD, MAIL_USERNAME, SECURITY_PASSWORD_SALT, PRODUCTION_DATABASE_PATH, LOCAL_DATABASE_PATH, LOCAL_UPLOAD_FOLDER

class Config:
    """Base configuration class with default settings."""
    FLASK_ENV = 'development'
    SECRET_KEY = SECRET_KEY
    WTF_CSRF_ENABLED = True
    TESTING = False

    # Flask-Mail config settings
    MAIL_SERVER = 'smtp.zoho.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = MAIL_USERNAME
    MAIL_PASSWORD = MAIL_PASSWORD
    MAIL_DEFAULT_SENDER = {'Budgeteer Help', MAIL_USERNAME}

    UPLOAD_FOLDER = 'uploads'
    SECURITY_PASSWORD_SALT = SECURITY_PASSWORD_SALT
    DATABASE_URI = None
    # MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size  # TODO: Implment this later?. Ask AI what the implications are of using this instead of manually checking file sizes

class DevelopmentConfig(Config):
    """Configuration for development environment."""
    DEBUG = True  # Comment this out if you want to see custom http error pages
    WTF_CSRF_ENABLED = False #TODO: When all forms are flask-wtforms, remove this so it's always true
    DATABASE_URI = LOCAL_DATABASE_PATH

class TestingConfig(Config):
    """Configuration for testing environment."""
    TESTING = True
    DATABASE_URI = ':memory:'
    MAIL_SUPPRESS_SEND = True
    MAIL_BACKEND = 'memory'
    UPLOAD_FOLDER = LOCAL_UPLOAD_FOLDER # TODO: This needs to be platform agnostic

class ProductionConfig(Config):
    """Configuration for production environment."""
    FLASK_ENV = 'production'
    DATABASE_URI = PRODUCTION_DATABASE_PATH
    WTF_CSRF_ENABLED = False #TODO: When all forms are flask-wtforms, remove this so it's always true

# Configuration dictionary mapping names to classes
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
