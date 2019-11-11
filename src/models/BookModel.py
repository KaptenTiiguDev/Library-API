# Faili nimi peaks olema book_model (PEP-8)
from marshmallow import fields, Schema
from . import db
import datetime


'''
Mudel võiks olla ainult andmemudel, andmebaasi enda päringud võiks üle viia data access kihti ja äri loogika niinimetatud
service kihti.

Samuti created_at ja modified_at lahendab sqlalchemy ära, et ei pea ise kuupäevi käsitisi määrama.
Init meetodit pole otseselt vaja mudelile kuna kui sa annad ette talle keyword parameetrid siis ta oskab ise mudeli 
ära täita ala. niiviisi BookModel(isbn='123', title='123') või siis dictionary
lahti pakkimisega ala BookModel(**some_data_dictionary)

Ehk näiteks Raamatu mudelist jääks alles ainult selline osa.


class BookModel(db.Model):
    """Book Model"""
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(128), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    location = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=func.current_timestamp())
    modified_at = db.Column(db.DateTime, default=func.current_timestamp())

    days_book_considered_new = 90
    standard_issue_period_days = 28
    short_issue_period_days = 7
    book_shortage_number = 5


data access layer oleks midagi taolist näiteks, esmalt defineeritud baasDao mida teised kasutavad ja siis spetsiifiline
mudeli põhine dao:

class BaseDao:
    model = None
    session = m.db.session

    @classmethod
    def get(cls, instance_id: int) -> m.db.Model:
        return cls.model.query.get(instance_id)

    @classmethod
    def get_all(cls) -> list:
        return cls.model.query.all()

    @classmethod
    def add(cls, instance: m.db.Model) -> None:
        return cls.session.add(instance)

    @classmethod
    def delete(cls, instance: m.db.Model) -> None:
        return cls.session.delete(instance)

    @classmethod
    def update(cls, instance_id: int=None, updated_fields: dict=None) -> bool:
        cls.model.query.filter_by(id=instance_id).update(updated_fields)

    @classmethod
    def commit(cls) -> None:
        cls.session.commit()

    @classmethod
    def rollback(cls) -> None:
        cls.session.rollback()


class BookDao(BaseDao):
    model = m.Book

    @classmethod
    def get_books_by_isbn(cls, isbn: str) -> List[m.Book]:
        return cls.model.query.filter(cls.model.isbn == isbn).all()

'''
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
        if (datetime.datetime.utcnow() - self.created_at).days <= BookModel.days_book_considered_new:
            return BookModel.short_issue_period_days
        if len(BookModel.query.filter(BookModel.isbn==self.isbn).all()) < BookModel.book_shortage_number:
            return BookModel.short_issue_period_days
        return BookModel.standard_issue_period_days

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
