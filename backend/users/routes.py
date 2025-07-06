from flask import Blueprint, request, redirect, url_for, flash, render_template, jsonify
from flask_login import login_required, logout_user, UserMixin, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from ..extensions import login_manager, db
from ..models import User


users_bp = Blueprint('users', __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)  # returns the actual SQLAlchemy object


@users_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if 'name' not in request.form or 'password' not in request.form:
            print('Error: Missing name or password')
            flash('Missing name or password', 'error')
            return render_template('register.html')

        name = request.form['name']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        try:
            # Create new user and add to session
            new_user = User(name=name, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('users.login'))
        except IntegrityError:
            db.session.rollback()
            flash('User already exists', 'error')

    # For get requests just render the page
    return render_template('register.html')


@users_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'name' not in request.form or 'password' not in request.form:
            return jsonify({'error': 'Missing name or password'}), 400
        name = request.form['name']
        password = request.form['password']

        # Query user by name
        user = User.query.filter_by(name=name).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('main.library'))
        else:
            flash('Invalid username or password', 'error')

    # For get requests just render the page
    return render_template('login.html')


@users_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('users.login'))

