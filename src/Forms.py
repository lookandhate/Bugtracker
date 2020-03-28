from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')


class ChangeProfileProperties(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired(), Length(min=1, max=20)])
    new_password = PasswordField('New password', validators=[DataRequired(), Length(min=1, max=20)])
    new_password_repeat = PasswordField('New password', validators=[DataRequired(),
                                                                    EqualTo('new_password',
                                                                            message='Passwords must match'),
                                                                    Length(min=1, max=20)])


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=1, max=20)])
    submit = SubmitField('Join!')


class CreateProject(FlaskForm):
    project_name = StringField('Project name', validators=[DataRequired(), Length(min=1, max=20)])
    short_project_tag = StringField('Short project name,if not specified, then generated automatically',
                                    validators=[Length(max=5)])
    project_description = StringField('Project description', validators=[Length(max=255)])
    submit = SubmitField('Create Project!')


class CreateIssue(FlaskForm):
    pass


class ChangeProjectProperties(FlaskForm):
    project_name = StringField('Project name', validators=[DataRequired(), Length(min=1, max=20)])
    short_project_tag = StringField('Short project name,if not specified, then generated automatically',
                                    validators=[Length(max=5)])
    project_description = StringField('Project description', validators=[Length(max=255)])
    project_owner = SelectField(coerce=int)
    submit = SubmitField('Save!')