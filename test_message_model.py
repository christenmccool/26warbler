"""Message model tests."""


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_message_model(self):
        """Does basic model work?"""

        u = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="User.image_url.default.arg"
        )

        db.session.add(u)
        db.session.commit()

        m = Message(
            text="Went to the ocean today!",
            user_id=u.id
        )

        db.session.add(m)
        db.session.commit()

        self.assertIsInstance(m, Message)
        self.assertEqual(m.user, u)

    def test_no_message(self):
        """Does Message fail to create a new Message when a non-nullable field is left blank?"""
        u = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="User.image_url.default.arg"
        )
        db.session.add(u)
        db.session.commit()

        m = Message(
            user_id=u.id
        )
        db.session.add(m)

        # User 1 is not created when email field is left blank
        self.assertRaises(IntegrityError, db.session.commit)
   
    