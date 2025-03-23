from datetime import datetime
from enum import Enum
from ..extensions import db

class UserRole(str, Enum):
    USER = 'user'
    ADMIN = 'admin'
    PREMIUM = 'premium'

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    profile_pic = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(20), default=UserRole.USER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    youtube_token = db.Column(db.String(255), nullable=True)
    youtube_refresh_token = db.Column(db.String(255), nullable=True)
    youtube_token_expiry = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<User {self.email}>' 