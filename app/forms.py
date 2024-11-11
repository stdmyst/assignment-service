from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    TextAreaField,
    SelectField
    )
from wtforms.fields.datetime import DateTimeLocalField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, InputRequired

from app import db
from app.models import User

import sqlalchemy as sa


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField(name="Username", validators=[DataRequired()])
    email = StringField(name="Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    password_repeat = PasswordField(
        "Repeat password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Reqister")

    def validate_username(self, username):
        user = db.session.scalar(
            sa.select(User).where(User.username == username.data)
            )
        if user:
            raise ValidationError("Please use a different username.")
    
    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user:
            raise ValidationError('Please use a different email address.')


class CreateIssueForm(FlaskForm):
    issue_name = StringField(name="Название поручения", validators=[DataRequired()])
    issue_body = TextAreaField(name="Описание поручения", validators=[DataRequired()])
    date_of_completion = DateTimeLocalField(name="Дата окончания", format="%Y-%m-%dT%H:%M")
    executor = SelectField(name="Исполнитель", coerce=int)
    submit = SubmitField("Create Issue")