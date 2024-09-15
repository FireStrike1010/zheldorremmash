from flask import Flask, session, flash, redirect, url_for, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_caching import Cache


db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
cache = Cache()

def create_app():
    app = Flask(__name__, template_folder='../templates')

    app.secret_key = 'secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://flask:123@localhost:5432/zheldormash"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 604800 ## 1 week
    app.config['MESSAGE_FLASHING_OPTION'] = {'duration': 3} ## 3 seconds

    from blueprints import (base, auth, dashboard, profile, data)
    app.register_blueprint(base)
    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(profile)
    app.register_blueprint(data)

    with app.app_context():
        db.init_app(app)
        migrate.init_app(app, db)
        bcrypt.init_app(app)
        cache.init_app(app)

    from user import User
    @app.before_request
    def before_request():
        if request.endpoint not in ('auth.signin', 'static', 'dashboard.facility_dashboard'):
            try:
                user = User(session=session)
                g.user = user
            except LookupError:
                flash('Пожалуйста, сначала войдите.', )
                return redirect(url_for('auth.signin'))
            except ValueError:
                flash('Ваша сессия устарела. Перезайдите пожалуйста.', category='warning')
                return redirect(url_for('auth.signin'))

    return app