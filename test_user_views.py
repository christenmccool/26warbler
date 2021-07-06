"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="password",
                                    image_url=None)

        db.session.commit()

    def test_signup(self):
        """Can add user?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            data={"username":"testuser2",
                  "email":"test2@test.com",
                  "password":"password"}

            resp = c.post("/signup", data=data)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            u = User.query.filter(User.email == "test2@test.com").first()
            self.assertEqual(u.username, "testuser2")
    
    def test_signup_follows_redirects(self):
        """Can add user and follow redirects?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            data={"username":"testuser2",
                  "email":"test2@test.com",
                  "password":"password"}

            resp = c.post("/signup", data=data, follow_redirects=True)
            html = resp.get_data(as_text = True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            u = User.query.filter(User.email == "test2@test.com").first()
            self.assertIn(f'<p>@{u.username}</p>', html)

    
    # def test_no_signup(self):
    #     """Fail to add user when duplicate username?"""

    #     with self.client as c:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id

    #         data={"username":"testuser",
    #               "email":"test2@test.com",
    #               "password":"password"}

    #         resp = c.post("/signup", data=data, follow_redirects=True)

    #         # self.assertEqual(resp.status_code, 302)

    #         html = resp.get_data(as_text = True)

    #         self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)


    def test_logged_in_can_view_following_page(self):
        """Can a logged in user view a following page?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            u2 = User.signup(
                username="testuser2",
                email="test2@test.com",
                password="password",
                image_url=None
            )

            db.session.commit()

            resp = c.get(f"/users/{u2.id}/following")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            self.assertIn(f'<div class="col-sm-9">', html)


    def test_not_logged_in_cant_view_following_page(self):
        """A user that is not logged in cannot view a following page?"""

        with self.client as c:
            u2 = User.signup(
                username="testuser2",
                email="test2@test.com",
                password="password",
                image_url=None
            )

            db.session.commit()

            resp = c.get(f"/users/{u2.id}/following", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            self.assertIn('<div class="home-hero">', html)
            self.assertIn("<h1>What\'s Happening?</h1>", html)


    def test_logged_in_can_add_message(self):
        """Can a logged in user add a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/new", data={"text":"Hello! This is my message!"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            self.assertIn("<p>Hello! This is my message!</p>", html)


    def test_logged_in_can_delete_message(self):
        """Can a logged in user delete a message?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            m = Message(text="Hello! This is my message!", user_id=self.testuser.id)
            db.session.add(m)
            db.session.commit()

            resp = c.post(f"/messages/{m.id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            self.assertNotIn("<p>Hello! This is my message!</p>", html)


    def test_logged_in_cant_add_message(self):
        """A user that is not logged cannot add a message?"""

        with self.client as c:

            resp = c.post(f"/messages/new", data={"text":"Hello! This is my message!"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            self.assertIn('<div class="home-hero">', html)
            self.assertIn("<h1>What\'s Happening?</h1>", html)


    def test_logged_in_cant_delete_message(self):
        """A user that is not logged cannot delete a message?"""

        with self.client as c:

            m = Message(text="Hello! This is my message!", user_id=self.testuser.id)
            db.session.add(m)
            db.session.commit()

            resp = c.post(f"/messages/{m.id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            self.assertIn('<div class="home-hero">', html)
            self.assertIn("<h1>What\'s Happening?</h1>", html)
