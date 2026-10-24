from flask import Flask, render_template, session
from models import db
from routes.auth import auth
from routes.admin import admin
from routes.user import user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking_app.db'
app.config['SECRET_KEY'] = 'my_parking_app_secret'

db.init_app(app)
app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(user)

@app.route('/')
def index():
    return render_template('index.html')

with app.app_context():
    db.create_all()

## print("Database created successfully!")

app.run(debug=True)