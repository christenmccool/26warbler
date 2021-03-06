import os

from flask import Flask, render_template, request, flash, redirect, session, g, jsonify, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
import functools

from forms import UserAddForm, LoginForm, MessageForm, UserEditForm, ChangePasswordForm
from models import db, connect_db, User, Message, Likes, Follows

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgres:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

def check_loggedin(func):
    @functools.wraps(func)
    def wrapper_check_loggedin(*args, **kwargs):
        if not g.user:
            flash("Access unauthorized. Log in to account to access content.", "danger")
            return redirect("/")
        value = func(*args, **kwargs)
        return value
    return wrapper_check_loggedin

def is_admin(func):
    @functools.wraps(func)
    def wrapper_is_admin(*args, **kwargs):
        if not g.user or not g.user.admin:
            flash("Access unauthorized. Admin access only.", "danger")
            return redirect("/")
        value = func(*args, **kwargs)
        return value
    return wrapper_is_admin

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect(url_for('homepage'))

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    flash("User logged out.", 'success')

    return redirect(url_for('login'))


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', user_list=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    messages = []
    # snagging messages in order from the database;
    # user.messages won't be in order by default
    if (g.user and g.user.is_following(user)) or user.private == False:
        messages = (Message
                    .query
                    .filter(Message.user_id == user_id)
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())
    
    pending_user_list = []
    if g.user.id == user_id:
        pending_user_list = [follower for follower in g.user.followers if follower.is_following(g.user) and not follower.is_following_confirmed(g.user)] 

    return render_template('users/show.html', user=user, message_list=messages, pending=pending_user_list)


@app.route('/users/<int:user_id>/following')
@check_loggedin
def show_following(user_id):
    """Show list of people this user is following."""

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user, user_list=user.following)


@app.route('/users/<int:user_id>/followers')
@check_loggedin
def users_followers(user_id):
    """Show list of followers of this user."""

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    user = User.query.get_or_404(user_id)

    pending_user_list = []
    if g.user.id == user_id:
        pending_user_list = [follower for follower in g.user.followers if follower.is_following(g.user) and not follower.is_following_confirmed(g.user)] 

    return render_template('users/followers.html', user=user, user_list=user.followers, pending=pending_user_list)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
@check_loggedin
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    # return redirect(f"/users/{g.user.id}/following")
    return redirect(url_for('show_following', user_id=g.user.id))



@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
@check_loggedin
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    # return redirect(f"/users/{g.user.id}/following")
    return redirect(url_for('show_following', user_id=g.user.id))

@app.route('/users/accept-follower/<int:follower_id>', methods=['POST'])
@check_loggedin
def accept_follower(follower_id):
    """Accept follower."""

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    follower_user = User.query.get(follower_id)
    follow = Follows.query.filter(Follows.user_being_followed_id==g.user.id, Follows.user_following_id==follower_user.id).first()
    follow.following_confirmed_status = True
    db.session.commit()

    # return redirect(f"/users/{g.user.id}/following")
    return redirect(url_for('users_followers', user_id=g.user.id))


@app.route('/users/profile', methods=["GET", "POST"])
@check_loggedin
def edit_profile():
    """Update profile for current user."""

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    form = UserEditForm(obj=g.user)

    if form.validate_on_submit():
        user = User.authenticate(g.user.username,
                                 form.password.data)
        if user:
            flash("User updated.", "success")

            g.user.username=form.username.data or g.user.username
            g.user.email=form.email.data or g.user.email
            g.user.image_url=form.image_url.data or User.image_url.default.arg
            g.user.header_image_url=form.header_image_url.data or User.header_image_url.default.arg
            g.user.bio=form.bio.data 
            g.user.private=form.private.data

            db.session.commit()

            # return redirect(f"/users/{user.id}")
            return redirect(url_for('users_show', user_id=user.id))
            
        flash("Incorrect password.", 'danger')
    
    return render_template('users/edit.html', form=form)

@app.route('/users/password', methods=["GET", "POST"])
@check_loggedin
def change_password():
    """Change password for current user."""

    form = ChangePasswordForm()

    if form.validate_on_submit():
        user = User.change_password(form.username.data, form.password.data, 
                                    form.newpassword1.data, form.newpassword2.data)
        if user:
            flash("Password updated.", "success")

            db.session.commit()

            return redirect(url_for('users_show', user_id=user.id))
            
        flash("Incorrect password.", 'danger')
    
    return render_template('users/password.html', form=form)



@app.route('/users/delete', methods=["POST"])
@check_loggedin
def delete_self():
    """Delete user."""

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect(url_for('signup'))


@app.route('/users/<int:user_id>/delete', methods=["POST"])
@check_loggedin
@is_admin
def delete_user(user_id):
    """Delete user by admin only."""

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('homepage'))


##############################################################################
# Messages routes:

# @app.route('/messages/new', methods=["GET", "POST"])
# def messages_add():
#     """Add a message:

#     Show form if GET. If valid, update message and redirect to user page.
#     """

#     if not g.user:
#         flash("Access unauthorized.", "danger")
#         return redirect("/")

#     form = MessageForm()

#     if form.validate_on_submit():
#         msg = Message(text=form.text.data)
#         g.user.messages.append(msg)
#         db.session.commit()

#         return redirect(f"/users/{g.user.id}")
        # return redirect(url_for('users_show', user_id=g.user.id))


#     return render_template('messages/new.html', form=form)

@app.route('/messages/new', methods=["POST"])
@check_loggedin
def messages_add():
    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")
        
    print(request.json)
    msg = Message(text=request.json["text"])
    g.user.messages.append(msg)
    db.session.commit()
    response_json = jsonify(message={'id': msg.id, 
                                     'text': msg.text, 'timestamp': msg.timestamp.strftime('%d %B %Y'), 
                                     'user_id': msg.user_id, 'username': msg.user.username, 
                                     'image_url': msg.user.image_url})
    return (response_json, 201)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get_or_404(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
@check_loggedin
def messages_destroy(message_id):
    """Delete a message."""

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    msg = Message.query.get(message_id)

    if msg.user_id != g.user.id and g.user.admin == False:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    db.session.delete(msg)
    db.session.commit()

    # return redirect(f"/users/{g.user.id}")
    return redirect(url_for('users_show', user_id=g.user.id))

@app.route('/users/<int:user_id>/messages')
@check_loggedin
def show_own_messages(user_id):
    """Show list of user's messages."""

    user = User.query.get_or_404(user_id)

    if (g.user and g.user.is_following(user)) or user.private == False:
        messages = (Message
                    .query
                    .filter(Message.user_id == user_id)
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

    return render_template('users/messages.html', user=user, message_list=messages)



##############################################################################
# Like routes:

# @app.route('/users/add_like/<int:message_id>', methods=['POST'])
# def likes_add(message_id):
#     """Add a like to a message"""

#     if not g.user:
#         flash("Access unauthorized.", "danger")
#         return redirect("/")

#     msg = Message.query.get_or_404(message_id)

#     if msg in g.user.likes:
#         g.user.likes.remove(msg)
#     else:
#         g.user.likes.append(msg)

#     db.session.commit()

#     return redirect("/")

@app.route('/users/add_like/<int:message_id>', methods=["POST"])
@check_loggedin
def likes_add(message_id):
    """Add a like to a message"""

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")


    msg = Message.query.get_or_404(message_id)

    if msg in g.user.likes:
        g.user.likes.remove(msg)
    else:
        g.user.likes.append(msg)

    db.session.commit()

    liked = True if msg in g.user.likes else False

    return jsonify({"liked": liked})

@app.route('/users/<int:user_id>/likes')
def users_likes(user_id):
    """Show list of likes of this user."""

    user = User.query.get_or_404(user_id)

    return render_template('users/likes.html', user=user, message_list=user.likes)

##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:
        messages = (Message
                    .query
                    .filter((Message.user_id == g.user.id) | (Message.user_id.in_(user.id for user in g.user.following)))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        likes = g.user.likes

        return render_template('home.html', message_list=messages)

    else:
        return render_template('home-anon.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404



##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
