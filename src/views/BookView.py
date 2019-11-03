from flask import request, json, Response, Blueprint, g
from ..models.UserModel import UserModel, UserSchema, Role
from .UserView import has_role_required
from ..models.BookModel import BookModel, BookSchema
from ..models.BookModel import BookIssueModel, BookIssueSchema
from ..shared.Authentication import Auth
from webargs import flaskparser
from flask_user import roles_required, UserMixin
import sys

parser = flaskparser.FlaskParser()

book_api = Blueprint("book_api", __name__)
book_schema = BookSchema()

issue_api = Blueprint("issue_api", __name__)
issue_schema = BookIssueSchema()

@book_api.route("/", methods=["POST"])
@Auth.auth_required
def create():
    """Add a book"""

    if not has_role_required(g, ["Admin"]):
        return custom_response({"error": "Authorization Required"}, 401)

    req_data = request.get_json()
    data = book_schema.load(req_data)
    book = BookModel(data)
    book.save()
    ser_data = book_schema.dump(book)
    return custom_response(data, 201)


@book_api.route("/", methods=["GET"])
def get_all():
    """Get all books"""

    books = BookModel.get_all_books()
    data = book_schema.dump(books, many=True)
    return custom_response(data, 200)


@book_api.route("/<int:book_id>", methods=["GET"])
def get_one(book_id):
    """Get a book"""

    book = BookModel.get_one_book(book_id)
    if not book:
        return custom_response({"error": "book not found"}, 404)
    data = book_schema.dump(book)
    return custom_response(data, 200)


@book_api.route("/<int:book_id>", methods=["DELETE"])
@Auth.auth_required
def delete(book_id):
    """Delete a book"""

    if not has_role_required(g, ["Admin"]):
        return custom_response({"error": "Authorization Required"}, 401)

    book = BookModel.get_one_book(book_id)
    if not book:
        return custom_response({"error": "book not found"}, 404)

    # TODO implement and test if issued
    if not BookIssueModel.is_book_issued(book_id):
        book.delete()
        return custom_response({"message": "deleted"}, 204)
    return custom_response({"error": "Cannot delete an issued book"}, 400)

@issue_api.route("/", methods=["POST"])
@Auth.auth_required
def create_new_issue():
    """Create an issue"""

    if not has_role_required(g, ["Librarian"]):
        return custom_response({"error": "Authorization Required"}, 401)

    # TODO add check if issued
    # if BookIssueModel.is_book_issued(book_id):
    #     return custom_response({"error": "The book is already issued"}, 400)

    req_data = request.get_json()
    data  = issue_schema.load(req_data)
    issue = BookIssueModel(data)
    issue.save()
    ser_data = issue_schema.dump(issue)
    return custom_response(data, 201)

@issue_api.route("/", methods=["GET"])
@Auth.auth_required
def get_all_active_issues():
    """Get all issues"""

    if not has_role_required(g, ["Librarian"]):
        return custom_response({"error": "Authorization Required"}, 401)

    issues = BookIssueModel.get_all_issues()
    data = issue_schema.dump(issues, many=True)
    return custom_response(data, 200)


@issue_api.route('/<int:issue_id>', methods=['PUT'])
@Auth.auth_required
def deactivate_issue(issue_id):
    """Deactivate an Issue"""
    # Not yet implemented
    pass

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
