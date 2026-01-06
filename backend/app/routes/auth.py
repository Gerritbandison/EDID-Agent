"""
Authentication Routes
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from functools import wraps

from app import db
from app.models import User, APIKey

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def require_api_key(f):
    """Decorator to require valid API key for agent endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            # Fallback to config API key for backward compatibility
            config_api_key = current_app.config.get('API_KEY')
            if api_key == config_api_key:
                return f(*args, **kwargs)
            return jsonify({'error': 'API key required'}), 401

        # Validate API key
        key_model = APIKey.validate(api_key)
        if not key_model:
            # Fallback to config API key
            config_api_key = current_app.config.get('API_KEY')
            if api_key == config_api_key:
                return f(*args, **kwargs)
            return jsonify({'error': 'Invalid API key'}), 401

        db.session.commit()  # Save usage update
        return f(*args, **kwargs)

    return decorated_function


@bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT tokens."""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 401

    # Record login
    user.record_login()
    db.session.commit()

    # Create tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    })


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({'access_token': access_token})


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user.to_dict())


@bp.route('/api-keys', methods=['GET'])
@jwt_required()
def list_api_keys():
    """List all API keys (admin only)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    api_keys = APIKey.query.all()
    return jsonify([key.to_dict() for key in api_keys])


@bp.route('/api-keys', methods=['POST'])
@jwt_required()
def create_api_key():
    """Create a new API key (admin only)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'API key name required'}), 400

    key, api_key = APIKey.create(name=data['name'])
    db.session.add(api_key)
    db.session.commit()

    return jsonify({
        'key': key,  # Only returned once!
        'api_key': api_key.to_dict()
    }), 201


@bp.route('/api-keys/<int:key_id>', methods=['DELETE'])
@jwt_required()
def revoke_api_key(key_id):
    """Revoke an API key (admin only)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    api_key = APIKey.query.get(key_id)
    if not api_key:
        return jsonify({'error': 'API key not found'}), 404

    api_key.is_active = False
    db.session.commit()

    return jsonify({'message': 'API key revoked'})


@bp.route('/register', methods=['POST'])
def register():
    """Register a new user (first user becomes admin)."""
    data = request.get_json()

    required_fields = ['username', 'email', 'password']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Username, email, and password required'}), 400

    # Check if username or email already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400

    # First user becomes admin
    is_first_user = User.query.count() == 0
    role = 'admin' if is_first_user else 'viewer'

    user = User(
        username=data['username'],
        email=data['email'],
        full_name=data.get('full_name'),
        role=role
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'User created successfully',
        'user': user.to_dict()
    }), 201
