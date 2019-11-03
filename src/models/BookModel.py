from sqlalchemy import Table, Column, Integer, ForeignKey
from marshmallow import fields, Schema
from . import db, bcrypt
import datetime
import sys
from flask_user import roles_required, UserMixin, UserManager
from sqlalchemy.orm import relationship
from sqlalchemy import or_


class BookModel(db.Model):
    """Book Model"""

    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(128), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    location = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime)
    modified_at = db.Column(db.DateTime)

    days_book_considered_new = 90
    standard_issue_period_days = 28
    short_issue_period_days = 7
    book_shortage_number = 5

    def __init__(self, data):
        self.isbn = data.get("isbn")
        self.title = data.get("title")
        self.location = data.get("location")
        self.created_at = datetime.datetime.utcnow()
        self.modified_at = datetime.datetime.utcnow()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self, data):
        for key, item in data.items():
            setattr(self, key, item)
            self.modified_at = datetime.datetime.utcnow()
            db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def get_max_issue_period_in_days(self):
        # TODO test
        if (datetime.datetime.utcnow() - self.created_at).days <= BookModel.days_book_considered_new:
            return BookModel.short_issue_period_days
        if len(BookModel.query.filter(BookModel.isbn).all()) < book_shortage_number:
            return short_issue_period_days
        return standard_issue_period_days

    @staticmethod
    def get_all_books():
        return BookModel.query.all()

    @staticmethod
    def get_one_book(id):
        return BookModel.query.get(id)

    def __repr__(self):
        return "<id {}>".format(self.id)


class BookSchema(Schema):
    """Book Schema"""

    id = fields.Int(dump_only=True)
    isbn = fields.Str(required=True)
    title = fields.Str(required=True)
    location = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)
    modified_at = fields.DateTime(dump_only=True)


class BookIssueModel(db.Model):
    """Book Issue Model"""

    __tablename__ = "issues"

    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, unique=False, default=True, nullable=False)
    book_id = db.Column(
        db.Integer, db.ForeignKey("books.id", ondelete="CASCADE"), nullable=False
    )
    patron_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)
    modified_at = db.Column(db.DateTime)

    def __init__(self, data):
        self.is_active = data.get("is_active")
        self.book_id = data.get("book_id")
        self.patron_id = data.get("patron_id")
        self.due_date = self.set_due_date()
        self.created_at = datetime.datetime.utcnow()
        self.modified_at = datetime.datetime.utcnow()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self, data):
        for key, item in data.items():
            setattr(self, key, item)
            self.modified_at = datetime.datetime.utcnow()
            db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def set_due_date(self):
        days = BookModel.get_one_book(self.book_id).get_max_issue_period_in_days()
        return datetime.datetime.now() + datetime.timedelta(days=days)

    @staticmethod
    def get_all_issues():
        return BookIssueModel.query.all()

    @staticmethod
    def get_one_issue(id):
        return BookIssueModel.query.get(id)

    @staticmethod
    def is_book_issued(book_id):
        if BookIssueModel.query.filter(BookIssueModel.is_active==True) \
              .filter(BookIssueModel.book_id==book_id) \
              .first():
            return True
        return False

    def __repr__(self):
        return "<id {}>".format(self.id)


class BookIssueSchema(Schema):
    """Book IssueSchema"""

    id = fields.Int(dump_only=True)
    is_active = fields.Boolean()
    book_id = fields.Int(required=True)
    patron_id = fields.Int(required=True)
    due_date = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    modified_at = fields.DateTime(dump_only=True)
