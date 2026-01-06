#!/usr/bin/env python3
"""
Device Inventory Management System - Backend Server
"""
import os
from app import create_app, db
from app.models import User

app = create_app()


@app.cli.command('init-db')
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized.')


@app.cli.command('create-admin')
def create_admin():
    """Create an admin user."""
    import getpass

    username = input('Admin username: ')
    email = input('Admin email: ')
    password = getpass.getpass('Admin password: ')

    if User.query.filter_by(username=username).first():
        print(f'User {username} already exists.')
        return

    user = User(
        username=username,
        email=email,
        role='admin'
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    print(f'Admin user {username} created successfully.')


@app.cli.command('generate-api-key')
def generate_api_key():
    """Generate a new API key for agents."""
    from app.models import APIKey

    name = input('API key name: ')
    key, api_key = APIKey.create(name=name)

    db.session.add(api_key)
    db.session.commit()

    print(f'\nAPI Key created successfully!')
    print(f'Name: {name}')
    print(f'Key: {key}')
    print(f'\nSave this key - it will not be shown again!')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
