from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class MessageForm(FlaskForm):
    """Form for adding/editing messages."""

    text = TextAreaField('text', validators=[DataRequired()])


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    image_url = StringField('(Optional) Image URL')
    private = BooleanField('Private account')


class UserEditForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username')
    email = StringField('E-mail', validators=[Email()])
    image_url = StringField('Image URL')
    header_image_url = StringField('Header Image URL')
    bio = TextAreaField('Bio')
    private = BooleanField('Private account')
    password = PasswordField('Password')

class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class ChangePasswordForm(FlaskForm):
    """Form for changing password."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Old password', validators=[DataRequired()])
    newpassword1 = PasswordField('New password', validators=[DataRequired(), Length(6)])
    newpassword2 = PasswordField('New password (to confirm)', validators=[DataRequired(), Length(6), EqualTo('newpassword1')])
