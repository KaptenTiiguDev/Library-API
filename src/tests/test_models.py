import unittest
import os
import json
from ..app import create_app, db
import marshmallow
from ..models.UserModel import UserModel, UserSchema, Role

class ModelTest(unittest.TestCase):
    """Test case"""

    def create_user(self, user_data, token=None):
        """Create a sample user"""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Token {token}"

        return self.client().post(
            "/api/v1/users/patrons/",
            headers=headers,
            data=json.dumps(user_data)
        )

    def login_as_admin(self):
        res = self.client().post(
            "/api/v1/users/login/",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"email": "admin@test.com", "password": "testpass123"})
        )
        json_data = json.loads(res.data)
        return json_data.get("jwt_token")

    def login_as_librarian(self):
        res = self.client().post(
            "/api/v1/users/login/",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"email": "librarian@test.com", "password": "testpass123"})
        )
        json_data = json.loads(res.data)
        return json_data.get("jwt_token")

    def create_roles_and_staff(self):
        """Add admin and librarian to the testing database"""

        role1 = Role(name='Admin')
        role2 = Role(name='Librarian')
        role3 = Role(name='Patron')

        db.session.add(role1)
        db.session.add(role2)
        db.session.add(role3)

        db.session.commit()

        test_admin_data = {"name": "Admin Ben", "email": "admin@test.com", "password": "testpass123"}
        test_librarian_data = {"name": "Librarian Sarah", "email": "librarian@test.com", "password": "testpass123"}

        test_admin = UserModel(test_admin_data)
        test_admin.roles = [Role.query.filter_by(name="Admin").first(), ]
        db.session.add(test_admin)

        test_librarian = UserModel(test_librarian_data)
        test_librarian.roles = [Role.query.filter_by(name="Librarian").first(), ]
        db.session.add(test_librarian)

        db.session.commit()

        return test_admin, test_librarian

    def setUp(self):
        """Test Setup"""

        self.app = create_app("testing")
        self.client = self.app.test_client

        with self.app.app_context():
            db.drop_all()
            db.session.remove()
            db.session.commit()
            db.create_all()
            self.admin, self.librarian = self.create_roles_and_staff()

    def test_patron_token_generated_by_admin(self):
        """Test token creation with valid credentials"""

        valid_user_data = {"name": "Name", "email": "name@mail.com", "password": "!pAsSw0rD!"}

        admin_token = self.login_as_admin()

        res = self.create_user(valid_user_data, admin_token)

        self.assertTrue(json.loads(res.data).get("jwt_token"))
        self.assertEqual(res.status_code, 201)

    def test_patron_token_generated_by_librarian(self):
        """Test token creation with valid credentials"""

        valid_user_data = {"name": "Name", "email": "name@mail.com", "password": "!pAsSw0rD!"}

        librarian_token = self.login_as_librarian()

        res = self.create_user(valid_user_data, librarian_token)

        self.assertTrue(json.loads(res.data).get("jwt_token"))
        self.assertEqual(res.status_code, 201)

    def test_patron_token_not_generated_missing_field(self):
        """Test user token not created with invalid credentials"""

        invalid_user_data = {"name": "Name", "email": "", "password": "!pAsSw0rD!"}

        admin_token = self.login_as_admin()

        with self.assertRaises(marshmallow.exceptions.ValidationError):
            self.client().post(
                "/api/v1/users/patrons/",
                headers={"Content-Type": "application/json", "Authorization": f"Token {admin_token}"},
                data=json.dumps(invalid_user_data)
            )

    def test_list_all_patrons(self):
        """Test all patrons are listed"""

        user1_data = {"name": "Jane Doe", "email": "jane.doe@mail.com", "password" : "testpass"}
        user2_data = {"name": "John Doe", "email": "john.doe@mail.com", "password" : "testpass"}

        admin_token = self.login_as_admin()

        res = self.create_user(user1_data, admin_token)
        res = self.create_user(user2_data, admin_token)

        res = self.client().get(
            "/api/v1/users/patrons/",
            headers={"Content-Type": "application/json", "Authorization": f"Token {admin_token}"}
        )
        number_of_patrons = len(json.loads(res.data))

        self.assertEqual(number_of_patrons, 2)

    def test_admin_finds_patron_by_email_and_name(self):

        user1_data = {"name": "Jane Doe", "email": "jane.doe@mail.com", "password" : "testpass"}
        user2_data = {"name": "John Doe", "email": "john.doe@mail.com", "password" : "testpass"}

        admin_token = self.login_as_admin()

        res = self.create_user(user1_data, admin_token)
        res = self.create_user(user2_data, admin_token)

        query_email = "mail"

        res = self.client().get(
            f"/api/v1/users/patrons/?query={query_email}",
            headers={"Content-Type": "application/json", "Authorization": f"Token {admin_token}"},
        )

        number_of_matching_by_email = len(json.loads(res.data))
        self.assertEqual(number_of_matching_by_email, 2)

        query_name = "Jane"

        res = self.client().get(
            f"/api/v1/users/patrons/?query={query_name}",
            headers={"Content-Type": "application/json", "Authorization": f"Token {admin_token}"},
        )

        number_of_matching_by_name = len(json.loads(res.data))
        self.assertEqual(number_of_matching_by_name, 1)

    def test_admin_adds_a_book(self):
        """Test an admin can add a book"""
        token = self.login_as_admin()

        book_data = {"isbn": "99921-58-10-7", "title": "Garry Potter", "location": "AC-132"}

        res = self.client().post(
            "/api/v1/books/",
            headers={"Content-Type": "application/json", "Authorization": f"Token {token}"},
            data=json.dumps(book_data)
        )

        self.assertEqual(res.status_code, 201)
        self.assertEqual(json.loads(res.data).get("isbn"), book_data["isbn"])
        self.assertEqual(json.loads(res.data).get("title"), book_data["title"])
        self.assertEqual(json.loads(res.data).get("location"), book_data["location"])

    def test_librarian_adds_a_book(self):
        """Test a librarian cannot add a book"""
        token = self.login_as_librarian()

        book_data = {"isbn": "99921-58-10-7", "title": "Garry Potter", "location": "AC-132"}

        res = self.client().post(
            "/api/v1/books/",
            headers={"Content-Type": "application/json", "Authorization": f"Token {token}"},
            data=json.dumps(book_data)
        )

        self.assertEqual(res.status_code, 401)


    def test_unathenticated_user_adds_a_book(self):
        """Test unathenticated user cannot add a book"""

        book_data = {"isbn": "99921-58-10-7", "title": "Garry Potter", "location": "AC-132"}

        res = self.client().post(
            "/api/v1/books/",
            headers={"Content-Type": "application/json"},
            data=json.dumps(book_data)
        )

        self.assertEqual(res.status_code, 400)

    def test_unathenticated_user_gets_all_books(self):
        """Test unathenticated user can see the list of book"""
        res = self.client().get("/api/v1/books/")
        self.assertEqual(res.status_code, 200)

    def test_librarian_can_create_an_issue(self):
        """Test librarian can create an issue"""

        valid_user_data = {"name": "Name", "email": "name@mail.com", "password": "!pAsSw0rD!"}
        librarian_token = self.login_as_librarian()
        admin_token = self.login_as_admin()
        res = self.create_user(valid_user_data, admin_token)

        res = self.client().get(
            "/api/v1/users/patrons/",
            headers={"Content-Type": "application/json", "Authorization": f"Token {librarian_token}"}
        )

        patron_id = json.loads(res.data)[0]["id"]

        book_data = {"isbn": "99921-58-10-7", "title": "Garry Potter", "location": "AC-132"}

        res = self.client().post(
            "/api/v1/books/",
            headers={"Content-Type": "application/json", "Authorization": f"Token {admin_token}"},
            data=json.dumps(book_data)
        )

        res = self.client().get(
            "/api/v1/books/",
            headers={"Content-Type": "application/json", "Authorization": f"Token {librarian_token}"}
        )

        book_id = json.loads(res.data)[0]["id"]

        res = self.client().post(
            "/api/v1/issues/",
            headers={"Content-Type": "application/json", "Authorization": f"Token {librarian_token}"},
            data=json.dumps({"patron_id": patron_id, "book_id" : book_id})
        )

        res = self.client().get(
            "/api/v1/issues/",
            headers={"Content-Type": "application/json", "Authorization": f"Token {librarian_token}"}
        )

        received_book_id = json.loads(res.data)[0]["book_id"]
        received_patron_id = json.loads(res.data)[0]["patron_id"]

        self.assertEqual(received_patron_id, patron_id)
        self.assertEqual(received_book_id, book_id)

    def tearDown(self):
        """Tear Down"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            pass


if __name__ == "__main__":
    unittest.main()
