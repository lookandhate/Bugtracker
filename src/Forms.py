from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, BooleanField, SubmitField, F
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Join!')


class CreateProject(FlaskForm):
    project_name = StringField('Project name', validators=[DataRequired()])
    project_members = StringField('Type new project members with ; as separator')
    submit = SubmitField('Create Project!')


class CreateIssue(FlaskForm):
    pass
