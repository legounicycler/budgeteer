from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, validators

class LoginForm(FlaskForm):
    email = EmailField("Email", [validators.InputRequired(), validators.Length(min=5, max=320)], render_kw={"autocomplete": "username"})
    password = PasswordField("Password", [validators.InputRequired(), validators.Length(min=8, max=32, message="Password must be between 8 and 32 characters long")], render_kw={"autocomplete": "current-password"})

class RegisterForm(FlaskForm):
    new_first_name = StringField("First Name", [validators.InputRequired(), validators.Length(min=2, max=50)], render_kw={"autocomplete": "name"})
    new_last_name = StringField("Last Name", [validators.InputRequired(), validators.Length(min=2, max=50)], render_kw={"autocomplete": "family-name"})
    new_email = EmailField("Email", [validators.InputRequired(), validators.Length(min=5, max=320)], render_kw={"autocomplete": "username"})
    new_password = PasswordField("Password", [validators.InputRequired(), validators.EqualTo('confirm_password', message='Passwords must match'), validators.Length(min=8, max=32, message="Password must be between 8 and 32 characters long")], render_kw={"placeholder": "Between 8 and 32 characters", "autocomplete": "new-password"})
    confirm_password = PasswordField("Confirm Password", [validators.InputRequired(), validators.EqualTo('new_password', message='Passwords must match')], render_kw={"placeholder": "Between 8 and 32 characters", "autocomplete": "new-password"})

class ForgotPasswordForm(FlaskForm):
    email = EmailField("Email", [validators.InputRequired(), validators.Length(min=5, max=320)], render_kw={"autocomplete": "username"})

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField("New Password", [validators.InputRequired(), validators.EqualTo('confirm_password', message='Passwords must match'), validators.Length(min=8, max=32, message="Password must be between 8 and 32 characters long")], render_kw={"placeholder": "Between 8 and 32 characters", "autocomplete": "new-password"})
    confirm_password = PasswordField("Confirm Password", [validators.InputRequired(), validators.EqualTo('new_password', message='Passwords must match')], render_kw={"placeholder": "Between 8 and 32 characters", "autocomplete": "new-password"})