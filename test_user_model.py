"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr_method(self):
        """Does repr method work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # repr method should return formatted string
        self.assertEqual(u.__repr__(), f"<User #{u.id}: testuser, test@test.com>")

    def test_is_following_method(self):
        """Does is_following method correctly return True?"""

        u1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        follows = Follows(user_being_followed_id=u2.id, user_following_id=u1.id)
        db.session.add(follows)
        db.session.commit()

        # User 1 is following User 2 so this should return True
        self.assertTrue(u1.is_following(u2))

    def test_is_not_following_method(self):
        """Does is_following method correctly return False?"""

        u1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()


        # User 1 is NOT following User 2 so this should return False
        self.assertFalse(u1.is_following(u2))

    def test_is_followed_by_method(self):
        """Does is_followed_by method correctly return True?"""

        u1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        follows = Follows(user_being_followed_id=u1.id, user_following_id=u2.id)
        db.session.add(follows)
        db.session.commit()

        # User 1 is followed by User 2 so this should return True
        self.assertTrue(u1.is_followed_by(u2))


    def test_is_not_followed_by_method(self):
        """Does is_followed_by method correctly return False?"""

        u1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        # User 1 is NOT followed by User 2 so this should return False
        self.assertFalse(u1.is_followed_by(u2))


    def test_user_signup(self):
        """Does User.signup successfully create a new User?"""

        u = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="User.image_url.default.arg"
        )

        db.session.add(u)
        db.session.commit()

        # User 1 is successfully created
        self.assertIsInstance(u, User)

    def test_no_user_signup(self):
        """Does User.signup fail to create a new User when a non-nullable field is left blank?"""

        # User 1 is not created when email field is left blank
        self.assertRaises(TypeError, User.signup, username="testuser", password="HASHED_PASSWORD", image_url="User.image_url.default.arg")
   

    def test_user_authenticate(self):
        """Does User.signup successfully create a new User?"""

        u = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="User.image_url.default.arg"
        )

        db.session.add(u)
        db.session.commit()

        auth = User.authenticate(username="testuser", password="HASHED_PASSWORD")

        # Authentication succeeds
        self.assertTrue(auth)

    def test_user_authenticate(self):
        """Does User.signup successfully create a new User?"""

        u = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="User.image_url.default.arg"
        )

        db.session.add(u)
        db.session.commit()

        auth1 = User.authenticate(username="testuser1", password="HASHED_PASSWORD")
        auth2 = User.authenticate(username="testuser", password="HASHED_PASSWORD_OOPS")

        # Authentication fails
        self.assertFalse(auth1)
        self.assertFalse(auth2)