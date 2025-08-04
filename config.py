from secret import SECRET_KEY, MAIL_PASSWORD, MAIL_USERNAME, SECURITY_PASSWORD_SALT, WINDOWS_DATABASE_PATH, LINUX_DATABASE_PATH

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

class DevelopmentConfig(Config):
    """Configuration for development environment."""
    DEBUG = True
    WTF_CSRF_ENABLED = False #TODO: When all forms are flask-wtforms, remove this so it's always true
    DATABASE_URI = WINDOWS_DATABASE_PATH

class TestingConfig(Config):
    """Configuration for testing environment."""
    TESTING = True
    DATABASE_URI = ':memory:'
    MAIL_SUPPRESS_SEND = True
    MAIL_BACKEND = 'memory'

class ProductionConfig(Config):
    """Configuration for production environment."""
    FLASK_ENV = 'production'
    DATABASE_URI = LINUX_DATABASE_PATH
    WTF_CSRF_ENABLED = False #TODO: When all forms are flask-wtforms, remove this so it's always true

# Configuration dictionary mapping names to classes
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
