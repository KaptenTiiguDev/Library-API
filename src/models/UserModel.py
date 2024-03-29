from sqlalchemy import Table, Column, Integer, ForeignKey
from marshmallow import fields, Schema
from . import db, bcrypt
import datetime
import sys
from flask_user import roles_required, UserMixin, UserManager
from sqlalchemy.orm import relationship
from sqlalchemy import or_

'''
Samad kommentaarid mis BookModel.py failis
'''

class UserModel(db.Model, UserMixin):
    """User Model"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime)
    modified_at = db.Column(db.DateTime)
    roles = db.relationship("Role", secondary="user_roles")

    def __init__(self, data):
        self.name = data.get("name")
        self.email = data.get("email")
        self.password = self.__generate_hash(data.get("password"))
        self.created_at = datetime.datetime.utcnow()
        self.modified_at = datetime.datetime.utcnow()

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all_users():
        return UserModel.query.all()

    @staticmethod
    def get_one_user(id):
        return UserModel.query.get(id)

    @staticmethod
    def get_user_by_email(value):
        return UserModel.query.filter_by(email=value).first()

    @staticmethod
    def get_users_by_role(role):
        return UserModel.query.filter(UserModel.roles.any(name=role)).all()

    def get_users_by_role_and_query(role, query):
        return (
            UserModel.query.filter(UserModel.roles.any(name=role))
            .filter(
                or_(UserModel.name.contains(query), UserModel.email.contains(query))
            )
            .all()
        )

    def __generate_hash(self, password):
        return bcrypt.generate_password_hash(password, rounds=10).decode("utf-8")

    def check_hash(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def __repr(self):
        return "<id {}>".format(self.id)


class UserSchema(Schema):
    """User Schema"""

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    created_at = fields.DateTime(dump_only=True)
    modified_at = fields.DateTime(dump_only=True)


class Role(db.Model):
    """Role data model"""

    __tablename__ = "roles"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)


class UserRoles(db.Model):
    """UserRoles data model"""

    __tablename__ = "user_roles"

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("users.id", ondelete="CASCADE"))
    role_id = db.Column(db.Integer(), db.ForeignKey("roles.id", ondelete="CASCADE"))
