#!/usr/bin/env python3
"""
Reset or create a user and set a new password (stored as a secure hash).

Usage:
    python tools/reset_password.py <username> <newpassword>

Run this in the project root where `create_app()` can be imported.
"""
import sys
from werkzeug.security import generate_password_hash

if len(sys.argv) < 3:
    print("Usage: python tools/reset_password.py <username> <newpassword>")
    sys.exit(1)

username = sys.argv[1]
newpass = sys.argv[2]

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    user = User.query.filter_by(username=username).first()
    if user:
        user.password = generate_password_hash(newpass)
        db.session.commit()
        print(f"Updated password for user '{username}'")
    else:
        u = User(username=username, password=generate_password_hash(newpass))
        db.session.add(u)
        db.session.commit()
        print(f"Created user '{username}' with provided password")
