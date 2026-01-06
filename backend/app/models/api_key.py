"""
API Key Model - For agent authentication
"""
from datetime import datetime, timezone
import secrets
import hashlib
from app import db


class APIKey(db.Model):
    """API Key model for agent authentication."""
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    key_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    key_prefix = db.Column(db.String(8), nullable=False)  # First 8 chars for identification

    # Permissions
    can_write = db.Column(db.Boolean, default=True)
    can_read = db.Column(db.Boolean, default=True)

    # Rate limiting
    rate_limit_per_minute = db.Column(db.Integer, default=60)

    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_used = db.Column(db.DateTime)
    usage_count = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<APIKey {self.name} ({self.key_prefix}...)>'

    @staticmethod
    def generate_key():
        """Generate a new API key."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_key(key):
        """Hash an API key for secure storage."""
        return hashlib.sha256(key.encode()).hexdigest()

    @classmethod
    def create(cls, name, expires_at=None):
        """Create a new API key and return the key and model."""
        key = cls.generate_key()
        api_key = cls(
            name=name,
            key_hash=cls.hash_key(key),
            key_prefix=key[:8],
            expires_at=expires_at
        )
        return key, api_key

    @classmethod
    def validate(cls, key):
        """Validate an API key and return the model if valid."""
        key_hash = cls.hash_key(key)
        api_key = cls.query.filter_by(key_hash=key_hash, is_active=True).first()

        if api_key:
            # Check expiration
            if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
                return None

            # Update usage
            api_key.last_used = datetime.now(timezone.utc)
            api_key.usage_count += 1
            return api_key

        return None

    def to_dict(self):
        """Convert API key to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'key_prefix': self.key_prefix,
            'can_write': self.can_write,
            'can_read': self.can_read,
            'is_active': self.is_active,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
