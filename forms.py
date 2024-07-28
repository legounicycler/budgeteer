from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, validators, SelectField

class LoginForm(FlaskForm):
    email = EmailField("Email", [validators.InputRequired(), validators.Email()], render_kw={"autocomplete": "username"})
    password = PasswordField("Password", [validators.InputRequired(), validators.Length(min=8, max=32, message="Password must be between 8 and 32 characters long")], render_kw={"autocomplete": "current-password"})

class RegisterForm(FlaskForm):
    new_first_name = StringField("First Name", [validators.InputRequired(), validators.Length(min=2, max=50)], render_kw={"autocomplete": "name"})
    new_last_name = StringField("Last Name", [validators.InputRequired(), validators.Length(min=2, max=50)], render_kw={"autocomplete": "family-name"})
    new_email = EmailField("Email", [validators.InputRequired(), validators.Email()], render_kw={"autocomplete": "username"})
    new_password = PasswordField("Password", [validators.InputRequired(), validators.EqualTo('confirm_password', message='Passwords must match'), validators.Length(min=8, max=32, message="Password must be between 8 and 32 characters long")], render_kw={"placeholder": "Between 8 and 32 characters", "autocomplete": "new-password"})
    confirm_password = PasswordField("Confirm Password", [validators.InputRequired(), validators.EqualTo('new_password', message='Passwords must match'), validators.Length(min=8, max=32, message="Password must be between 8 and 32 characters long")], render_kw={"placeholder": "Between 8 and 32 characters", "autocomplete": "new-password"})

class ForgotPasswordForm(FlaskForm):
    reset_email = EmailField("Email", [validators.InputRequired(), validators.Email()], render_kw={"autocomplete": "username"})

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField("New Password", [validators.InputRequired(), validators.EqualTo('confirm_password', message='Passwords must match'), validators.Length(min=8, max=32, message="Password must be between 8 and 32 characters long")], render_kw={"placeholder": "Between 8 and 32 characters", "autocomplete": "new-password"})
    confirm_password = PasswordField("Confirm Password", [validators.InputRequired(), validators.EqualTo('new_password', message='Passwords must match'), validators.Length(min=8, max=32, message="Password must be between 8 and 32 characters long")], render_kw={"placeholder": "Between 8 and 32 characters", "autocomplete": "new-password"})

# ----- TRANSACTION BUILDER FORMS ----- #
class NewExpenseForm(FlaskForm):
    name = StringField("Name", [validators.InputRequired(), validators.Length(min=1, max=300)], render_kw={"autocomplete": "name"})
    # envelope = SelectField("Envelope", [validators.InputRequired(), validators.Length(min=1, max=128)], render_kw={"autocomplete": "off"})
    # amount = StringField("Amount", [validators.InputRequired(), validators.Length(min=1, max=128)], render_kw={"autocomplete": "off"})
    # account = SelectField("Account", [validators.InputRequired(), validators.Length(min=1, max=5)], render_kw={"autocomplete": "off"})
    # date = StringField("Date", [validators.InputRequired(), validators.Length(min=1, max=128)], render_kw={"autocomplete": "off"})
    # note = StringField("Note", [validators.Length(min=1, max=300)], render_kw={"autocomplete": "off"})
    # schedule = StringField("Schedule", [validators.Length(min=1, max=128)], render_kw={"autocomplete": "off"})

class NewTransferForm(FlaskForm):
    name = StringField("Name", [validators.InputRequired(), validators.Length(min=1, max=300)], render_kw={"autocomplete": "name"})
    # envelope = SelectField("Envelope", [validators.InputRequired(), validators.Length(min=1, max=128)], render_kw={"autocomplete": "off"})
    # amount = StringField("Amount", [validators.InputRequired(), validators.Length(min=1, max=128)], render_kw={"autocomplete": "off"})
    # account = SelectField("Account", [validators.InputRequired(), validators.Length(min=1, max=5)], render_kw={"autocomplete": "off"})
    # date = StringField("Date", [validators.InputRequired(), validators.Length(min=1, max=128)], render_kw={"autocomplete": "off"})
    # note = StringField("Note", [validators.Length(min=1, max=300)], render_kw={"autocomplete": "off"})
    # schedule = StringField("Schedule", [validators.Length(min=1, max=128)], render_kw={"autocomplete": "off"})

class NewIncomeForm(FlaskForm):
    name = StringField("Name", [validators.InputRequired(), validators.Length(min=1, max=300)], render_kw={"autocomplete": "name"})
    # account = SelectField("Account", [validators.InputRequired(), validators.Length(min=1, max=5)], render_kw={"autocomplete": "off"})
    # date = StringField("Date", [validators.InputRequired(), validators.Length(min=1, max=128)], render_kw={"autocomplete": "off"})
    # amount = StringField("Amount", [validators.InputRequired(), validators.Length(min=1, max=128)], render_kw={"autocomplete": "off"})
    # note = StringField("Note", [validators.Length(min=1, max=300)], render_kw={"autocomplete": "off"})
    # schedule = StringField("Schedule", [validators.Length(min=1, max=128)], render_kw={"autocomplete": "off"})