from secret import SECRET_KEY, MAIL_PASSWORD, MAIL_USERNAME, SECURITY_PASSWORD_SALT

class Config:
    """Base configuration class with default settings."""
    SECRET_KEY = SECRET_KEY
    WTF_CSRF_ENABLED = True
    DEBUG = False
    TESTING = False

    # Flask-Mail config settings
    MAIL_SERVER = 'smtp.zoho.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = MAIL_USERNAME
    MAIL_PASSWORD = MAIL_PASSWORD
    UPLOAD_FOLDER = 'uploads'
    SECURITY_PASSWORD_SALT = SECURITY_PASSWORD_SALT
    DATABASE_URI = None

class DevelopmentConfig(Config):
    """Configuration for development environment."""
    DEBUG = True
    DATABASE_URI = 'C:\\Users\\norma\\Documents\\Github\\budgeteer\\database.sqlite'

class TestingConfig(Config):
    """Configuration for testing environment."""
    TESTING = True
    DATABASE_URI = ':memory:'
    # Additional testing-specific settings
    # e.g., DISABLE_EMAILS = True

class ProductionConfig(Config):
    """Configuration for production environment."""
    # Settings optimized for production
    # e.g., Different database, error handling, caching, etc.
    # You might include production-specific environment variables
    DATABASE_URI = '/home/opc/database.sqlite'

# Configuration dictionary mapping names to classes
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
