from flask import request, json, Response, Blueprint, g
from ..models.UserModel import UserModel, UserSchema, Role
from ..shared.Authentication import Auth
from webargs import flaskparser
from flask_user import roles_required, UserMixin
import sys
import logging
from flask import current_app as app

parser = flaskparser.FlaskParser()

user_api = Blueprint("user_api", __name__)
user_schema = UserSchema()

def has_role_required(g, required_roles):
    """Check if user has role required"""

    for role in required_roles:
        for user_role in UserModel.query.get(g.user.get("id")).roles:
            if role == user_role.name:
                return True
    return False


@user_api.route("/patrons/", methods=["POST"])
@Auth.auth_required
def create_patron():
    """Create Patron Function"""

    if not has_role_required(g, ["Admin", "Librarian"]):
        return custom_response({"error": "Authorization Required"}, 401)

    req_data = request.get_json()
    data = user_schema.load(req_data)

    user_in_db = UserModel.get_user_by_email(data.get("email"))
    if user_in_db:
        message = {
            "error": "User already exist, please supply another \
        email address"
        }
        return custom_response(message, 400)

    user = UserModel(data)
    user.roles = [Role.query.filter_by(name="Patron").first()]
    user.save()
    ser_data = user_schema.dump(user)
    token = Auth.generate_token(ser_data.get("id"))
    app.logger.info(f'Patron created ({user.name})')
    return custom_response({"jwt_token": token}, 201)


@user_api.route("/patrons/", methods=["GET"])
@Auth.auth_required
def get_all_patrons():
    """Get all patrons"""

    if not has_role_required(g, ["Admin", "Librarian"]):
        return custom_response({"error": "Authorization Required"}, 401)

    query = request.args.get("query")
    users = {}

    if query:
        users = UserModel.get_users_by_role_and_query("Patron", query)
    else:
        users = UserModel.get_users_by_role("Patron")

    ser_users = user_schema.dump(users, many=True)
    return custom_response(ser_users, 200)


@user_api.route("/patrons/<int:user_id>", methods=["GET"])
@Auth.auth_required
def get_a_patron(user_id):
    """Get a single patron"""

    if not has_role_required(g, ["Admin", "Librarian"]):
        return custom_response({"error": "Authorization Required"}, 401)

    user = UserModel.get_one_user(user_id)
    if not user:
        return custom_response({"error": "user not found"}, 404)

    ser_user = user_schema.dump(user)
    return custom_response(ser_user, 200)


@user_api.route("/login/", methods=["POST"])
def login():
    """User Login Function"""

    req_data = request.get_json()

    data = user_schema.load(req_data, partial=True)

    if not data.get("email") or not data.get("password"):
        return custom_response(
            {
                "error": "you need email and password \
        to sign in"
            },
            400,
        )
    user = UserModel.get_user_by_email(data.get("email"))
    if not user:
        return custom_response({"error": "invalid credentials"}, 400)
    if not user.check_hash(data.get("password")):
        return custom_response({"error": "invalid credentials"}, 400)
    ser_data = user_schema.dump(user)
    token = Auth.generate_token(ser_data.get("id"))
    return custom_response({"jwt_token": token}, 200)


def custom_response(res, status_code):
    """Custom Response Function"""

    return Response(
        mimetype="application/json", response=json.dumps(res), status=status_code
    )


@parser.error_handler
def handle_request_parsing_error(err, req, schema):
    """webargs error handler that uses Flask-RESTful's abort function to return
    a JSON error response to the client.
    """

    abort(422, errors=err.messages)
