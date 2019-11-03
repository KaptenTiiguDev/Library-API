from flask import Flask

from .config import app_config
from .models import db, bcrypt

from .views.UserView import user_api as user_blueprint
from .views.BookView import book_api as book_blueprint
from .views.BookView import issue_api as issue_blueprint

from flask_user import roles_required, UserMixin

from .models.UserModel import UserModel, UserSchema, Role, UserRoles
from .models.BookModel import BookModel
from .models.BookModel import BookIssueModel

def create_app(env_name):
    """Create an app"""

    app = Flask(__name__)

    app.config.from_object(app_config[env_name])

    bcrypt.init_app(app)

    db.init_app(app)

    app.register_blueprint(user_blueprint, url_prefix='/api/v1/users')
    app.register_blueprint(book_blueprint, url_prefix='/api/v1/books')
    app.register_blueprint(issue_blueprint, url_prefix='/api/v1/issues')

    @app.before_request
    def before_request_func():
        """Insert test roles and users for development"""
        if env_name == 'development':
            if not Role.query.all():
                role1 = Role(name='Admin')
                role2 = Role(name='Librarian')
                role3 = Role(name='Patron')

                db.session.add(role1)
                db.session.add(role2)
                db.session.add(role3)

                db.session.commit()

        if not UserModel.query.all():
            users = [
                {
                    "role": "Admin",
                    "data": {"name": "Ben White", "email": "ben@test.com", "password": "testpass123"}
                },
                {

                    "role": "Librarian",
                    "data": {"name": "Sarah Smith", "email": "sarah@test.com", "password": "testpass123"}
                },

                {
                    "role": "Patron",
                    "data": {"name": "Jessica Parker", "email": "jess@test.com", "password": "testpass123"}
                },

                {
                    "role": "Patron",
                    "data": {"name": "Angelina Jolie", "email": "angie@test.com", "password": "testpass123"}
                }
            ]

            for user_data in users:
                new_user = UserModel(user_data["data"])
                new_user.roles = [Role.query.filter_by(name=user_data["role"]).first(), ]
                db.session.add(new_user)
                db.session.commit()

    @app.route('/', methods=['GET'])
    def index():
        """Root endpoint"""
        return 'Hello world'

    return app
