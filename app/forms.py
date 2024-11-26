from app import db
from app.models import User, UserRights

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    TextAreaField,
    SelectField
)
from wtforms.fields.datetime import DateTimeLocalField, DateField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Optional

import sqlalchemy as sa


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class AddUserForm(FlaskForm):
    username = StringField(name="Username", validators=[DataRequired()])
    email = StringField(name="Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    password_repeat = PasswordField("Repeat password", validators=[DataRequired(), EqualTo("password")])
    user_rights = SelectField(
        name="Права",
        coerce=int,
        choices=[
            (UserRights.basic_rights, 'Базовые права'),
            (UserRights.lid_rights, 'Руководители'),
            (UserRights.admin_rights, 'Администраторы'),
        ]
    )
    submit = SubmitField("Reqister")

    def validate_username(self, username):
        query = sa.select(User).where(User.username == username.data)
        user = db.session.scalar(query)
        if user:
            raise ValidationError("Please use a different username.")
    
    def validate_email(self, email):
        query = sa.select(User).where(User.email == email.data)
        user = db.session.scalar(query)
        if user:
            raise ValidationError('Please use a different email address.')
        

class EditProfileForm(FlaskForm):
    username = StringField(name="Username", validators=[DataRequired()])
    email = StringField(name="Email", validators=[DataRequired(), Email()])
    user_rights = SelectField(
        name="Права",
        coerce=int,
        choices=[
            (UserRights.basic_rights, 'Базовые права'),
            (UserRights.lid_rights, 'Руководители'),
            (UserRights.admin_rights, 'Администраторы')
        ]
    )
    submit = SubmitField("Submit")


class EditPasswordForm(FlaskForm):
    password = PasswordField("Enter new password", validators=[DataRequired()])
    password_repeat = PasswordField("Repeat password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Submit")


class CreateIssueForm(FlaskForm):
    issue_name = StringField(name="Название задачи", validators=[DataRequired()])
    issue_body = TextAreaField(name="Описание задачи", validators=[DataRequired()])
    date_of_completion = DateTimeLocalField(name="Ожидаемая дата окончания", format="%Y-%m-%dT%H:%M")
    executor = SelectField(name="Исполнитель", coerce=int)
    submit = SubmitField("Create an Issue")


class EditIssueForm(FlaskForm):
    issue_name = StringField(name="Название задачи", validators=[DataRequired()])
    issue_body = TextAreaField(name="Описание задачи", validators=[DataRequired()])
    date_of_completion = DateTimeLocalField(name="Ожидаемая дата окончания", format="%Y-%m-%dT%H:%M")
    executor = SelectField(name="Исполнитель", coerce=int)
    status = SelectField(name="Status", coerce=str, choices=[
        ("Assigned", "Assigned"),
        ("Resolved", "Resolved"),
        ("On Hold", "On Hold"),
        ]
    )
    submit = SubmitField("Edit an Issue")


class TaskFiltersForm(FlaskForm):
    date_filter = DateField(name="Укажите дату", format="%Y-%m-%d", validators=[Optional()])
    status_filter = SelectField(name="Статус", coerce=str, validators=[Optional()], default='None')
    submit = SubmitField("Submit")
