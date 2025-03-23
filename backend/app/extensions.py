from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize SQLAlchemy and Migrate without binding to an app
db = SQLAlchemy()
migrate = Migrate() 