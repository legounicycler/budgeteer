from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, validators, SelectField, TextAreaField, HiddenField, SearchField
from wtforms.validators import Optional, ValidationError
from flask_wtf.file import FileField, FileAllowed
from datetime import datetime


class AmtStringField(StringField):
    """StringField that validates/converts float-like strings to int.

    Behavior:
    - Keeps the raw string during other validators so regex/length validators still work.
    - Appends an internal validator that runs last; it converts field.data to int or raises ValidationError.
    - If allow_empty=True, empty input becomes None.
    """
    def __init__(self, label=None, validators=None, allow_empty: bool=None, message: str=None, **kwargs):
        self.message = message or 'Field must be a number'
        # Preserve user validators order; append internal converter last
        vlist = list(validators) if validators else []
        self._has_optional = any(isinstance(v, Optional) for v in vlist)
        # If allow_empty not explicitly provided, infer from presence of Optional()
        if allow_empty is None:
            self.allow_empty = self._has_optional
        else:
            self.allow_empty = allow_empty
        vlist.append(self._convert_to_int)
        super().__init__(label, validators=vlist, **kwargs)

    def process_formdata(self, valuelist):
        # Normalize empty input to None when Optional() (or allow_empty) is set.
        if not valuelist:
            self.data = None
            return
        raw = valuelist[0]
        if isinstance(raw, str) and raw.strip() == '':
            if self.allow_empty:
                self.data = None
            else:
                # keep the raw empty string so later validators can produce the correct error
                self.data = raw
            return
        self.data = raw

    def _convert_to_int(self, form, field):
        data = field.data
        if data is None or (isinstance(data, str) and data.strip() == ''):
            if self.allow_empty:
                field.data = None
                return
            raise ValidationError(self.message)
        try:
            field.data = int(round(float(data.strip()) * 100))
        except Exception:
            raise ValidationError(self.message)

class DateStringField(StringField):
    """StringField that validates/converts date-like strings to datetime.

    - If allow_empty=True, empty input becomes None.
    - On invalid date input, raises wtforms.ValidationError during validation.
    - On valid input, field.data is set to datetime.
    """
    def __init__(self, label=None, validators=None, allow_empty: bool=None, message: str=None, **kwargs):
        self.message = message or 'Field must be a valid date'
        # Preserve user validators order; append internal converter last
        vlist = list(validators) if validators else []
        self._has_optional = any(isinstance(v, Optional) for v in vlist)
        # If allow_empty not explicitly provided, infer from presence of Optional()
        if allow_empty is None:
            self.allow_empty = self._has_optional
        else:
            self.allow_empty = allow_empty
        vlist.append(self._convert_to_date)
        super().__init__(label, validators=vlist, **kwargs)

    def process_formdata(self, valuelist):
        # Normalize empty input to None when Optional() (or allow_empty) is set.
        if not valuelist:
            self.data = None
            return
        raw = valuelist[0]
        if isinstance(raw, str) and raw.strip() == '':
            if self.allow_empty:
                self.data = None
            else:
                # keep the raw empty string so later validators can produce the correct error
                self.data = raw
            return
        self.data = raw

    def _convert_to_date(self, form, field):
        data = self.data
        if data is None or (isinstance(data, str) and data.strip() == ''):
            if self.allow_empty:
                field.data = None
                return
            raise ValidationError(self.message)
        try:
            self.data = datetime.strptime(str(data).strip(), '%m/%d/%Y')
        except (ValueError, TypeError):
            self.data = None

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

class BugReportForm(FlaskForm):
    bug_reporter_name = StringField("Name", [validators.InputRequired(), validators.Length(min=1, max=300)], render_kw={"autocomplete": "name"})
    bug_reporter_email = EmailField("Email", [validators.InputRequired(), validators.Email()], render_kw={"autocomplete": "email"})
    bug_description = TextAreaField("Description", [validators.InputRequired(), validators.Length(min=1, max=10000)], render_kw={"autocomplete": "description"})
    screenshot = FileField("Screenshot", validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp'], 'Must be image file')], render_kw={"accept": ".jpg,.jpeg,.png,.gif,.bmp,.tiff,.webp"})
    screenshot_filepath = StringField("File Path", validators=[Optional()]) #Technically this field is optional because it doesn't contain the actual file, but rather it's just a placeholder text

class TransactionSearchForm(FlaskForm):
    """Form for transaction searching on dashboard.

    The envelope/account multi-selects remain as raw <select multiple> elements in the template
    (populated dynamically). Their selected values are copied into the hidden fields below prior
    to submit via front-end JS so we can still validate backend without enumerating choices.
    """
    search_term = SearchField(
        "Search",
        [Optional(), validators.Length(max=300)],
        render_kw={"placeholder": "Search", "autocomplete": "off"}
    )
    search_amt_min = AmtStringField(
        "Min. Amt",
        [Optional(), validators.Regexp(r'^\$?\d+(?:\.\d{1,2})?$', message="Invalid min amount")],
        render_kw={"placeholder": "$0.00", "tabindex": "-1", "class": "special-input blue-grey-text white t-search-input validate"}
    )
    search_amt_max = AmtStringField(
        "Max. Amt",
        [Optional(), validators.Regexp(r'^\$?\d+(?:\.\d{1,2})?$', message="Invalid max amount")],
        render_kw={"placeholder": "$0.00", "tabindex": "-1", "class": "special-input blue-grey-text white t-search-input validate"}
    )
    search_date_min = DateStringField(
        "Min. Date",
        [Optional(), validators.Regexp(r'^\d{2}/\d{2}/\d{4}$', message="Use MM/DD/YYYY")],
        allow_empty=True,
        render_kw={"placeholder": "MM/DD/YYYY", "tabindex": "-1", "class": "datepicker blue-grey-text white t-search-input validate", "pattern": r"^((0|1)\d{1})/((0|1|2|3)\d{1})/((19|20)\d{2})$"}
    )
    search_date_max = DateStringField(
        "Max. Date",
        [Optional(), validators.Regexp(r'^\d{2}/\d{2}/\d{4}$', message="Use MM/DD/YYYY")],
        allow_empty=True,
        render_kw={"placeholder": "MM/DD/YYYY", "tabindex": "-1", "class": "datepicker blue-grey-text white t-search-input validate", "pattern": r"^((0|1)\d{1})/((0|1|2|3)\d{1})/((19|20)\d{2})$"}
    )