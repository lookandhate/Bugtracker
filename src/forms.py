from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, MultipleFileField
from wtforms.validators import DataRequired, Length, EqualTo, InputRequired


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
    confirm = PasswordField('Confirm password',
                            validators=[InputRequired(), DataRequired(), Length(min=1, max=20),
                                        EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Join!')


class CreateProject(FlaskForm):
    project_name = StringField('Project name', validators=[DataRequired(), Length(min=1, max=20)])
    short_project_tag = StringField('Short project name,if not specified, then generated automatically',
                                    validators=[Length(max=5)])
    project_description = StringField('Project description', validators=[Length(max=255)])
    submit = SubmitField('Create Project!')


class CreateIssue(FlaskForm):
    summary = StringField('Summary information', validators=[DataRequired(), Length(min=1, max=64)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=1, max=1024)])
    steps_to_reproduce = TextAreaField('Steps to reproduce', validators=[DataRequired(), Length(min=1, max=512)])
    priority = SelectField('Priority of issue')
    state = SelectField('Current State')
    attachments = TextAreaField('Link on cloud with files')
    submit = SubmitField('Create Issue!')


class ChangeProjectProperties(FlaskForm):
    project_name = StringField('Project name', validators=[DataRequired(), Length(min=1, max=20)])
    short_project_tag = StringField('Short project name,if not specified, then generated automatically',
                                    validators=[Length(max=5)])
    project_description = StringField('Project description', validators=[Length(max=255)])
    project_owner = SelectField(coerce=int)
    submit = SubmitField('Save!')
