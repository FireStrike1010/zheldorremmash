from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate


db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()


def create_app():
    app = Flask(__name__, template_folder='../templates')

    app.secret_key = 'secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://flask:123@localhost:5432/zheldormash"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['MESSAGE_FLASHING_OPTION'] = {'duration': 5}

    from blueprints import (base, auth, dashboard, profile, data) 
    app.register_blueprint(base)
    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(profile)
    app.register_blueprint(data)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    return app