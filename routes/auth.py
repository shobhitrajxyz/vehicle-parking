from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db
from models.user import User

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        new_user = User(username=username, password=password, full_name=full_name)
        db.session.add(new_user)
        db.session.commit()
        return "Registration successful! You can now login."
    
    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # admin check
        if username == 'admin' and password == 'admin123':
            session['user_id'] = 'admin'
            session['role'] = 'admin'
            return redirect(url_for('admin.dashboard'))
        else:
            # for users other than admin
            user = User.query.filter_by(username=username, password=password).first()
            if user:
                session['user_id'] = user.id
                session['role'] = 'user'
                return redirect(url_for('user.dashboard'))
            else:
                return "Invalid credentials!"
    
    return render_template('login.html')


@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))