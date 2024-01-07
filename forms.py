from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, validators

class LoginForm(FlaskForm):
    email = EmailField("Email", [validators.InputRequired(), validators.Length(min=5, max=50)])
    password = PasswordField("Password", [validators.InputRequired(), validators.Length(min=8, max=32, message="Password must be between 8 and 32 characters long")])
    submit = SubmitField('Log In')

class RegisterForm(FlaskForm):
    new_first_name = StringField("First Name", [validators.InputRequired(), validators.Length(min=2, max=30)])
    new_last_name = StringField("Last Name", [validators.InputRequired(), validators.Length(min=2, max=30)])
    new_email = EmailField("Email", [validators.InputRequired(), validators.Length(min=5, max=50)])
    new_password = PasswordField("Password", [validators.InputRequired(), validators.Length(min=8, max=32, message="Password must be between 8 and 32 characters long")])
    confirm_password = PasswordField("Confirm Password", [validators.InputRequired(), validators.EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Register')