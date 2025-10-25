from flask_wtf import FlaskForm
from wtforms import validators, StringField, PasswordField, EmailField, SelectField, SelectMultipleField, TextAreaField, SearchField, HiddenField, SubmitField
from wtforms.validators import Optional, ValidationError
import wtforms.validators as wt_validators
from typing import Optional as TypingOptional
from flask_wtf.file import FileField, FileAllowed
from datetime import datetime
from database import TType

# region ---------------CUSTOM FIELDS---------------

class AmtStringField(StringField):
    """StringField that validates/converts float-like strings to int.

    Behavior:
    - Keeps the raw string during other validators so regex/length validators still work.
    - Appends an internal validator that runs last; it converts field.data to int or raises ValidationError.
    - If allow_empty=True, empty input becomes None.
    """
    def __init__(self, label=None, validators=None, allow_empty: TypingOptional[bool]=None, message: TypingOptional[str]=None, **kwargs):
        
        # 1. Set the error message
        self.message = message or 'Error'

        # 2. Add the default validators for amount fields
        vlist = [
            wt_validators.Regexp(r'^\$?\d+(?:\.\d{1,2})?$', message="Invalid number format"),
            wt_validators.Length(max=19, message="Number too large")
        ]

        # 3. Preserve any user validators
        if validators:
            vlist.extend(list(validators))

        # 4. Set allow_empty based on presence of Optional() if not explicitly provided
        self._has_optional = any(isinstance(v, Optional) for v in vlist)
        # If allow_empty not explicitly provided, infer from presence of Optional()
        if allow_empty is None:
            self.allow_empty = self._has_optional
        else:
            self.allow_empty = allow_empty

        # 5. Append the internal converter as the LAST validator
        vlist.append(self._convert_to_int)

        # 6. Initialize the parent StringField with the complete validator list
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
    def __init__(self, label=None, validators=None, allow_empty: TypingOptional[bool]=None, message: TypingOptional[str]=None, **kwargs):
        
        # 1. Set the error message
        self.message = message or 'Error'
        
        # 2. Add the default date format validator
        vlist = [
           wt_validators.Regexp(r'^\d{2}/\d{2}/\d{4}$', message="Use MM/DD/YYYY")
        ]

        # 3. Preserve any user validators
        if validators:
            vlist.extend(list(validators))

        # 4. Set allow_empty based on presence of Optional() if not explicitly provided
        self._has_optional = any(isinstance(v, Optional) for v in vlist)
        if allow_empty is None:
            self.allow_empty = self._has_optional
        else:
            self.allow_empty = allow_empty
        
        # 5. Append the internal date converter as the LAST validator
        vlist.append(self._convert_to_date) # type: ignore[assignment]

        # 6. Initialize the parent StringField with the complete validator list
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

    def _convert_to_date(self, form, field): #TODO: Re-examine this function after GPT5mini reworked it
        data = field.data
        if data is None or (isinstance(data, str) and data.strip() == ''):
            if self.allow_empty:
                field.data = None
                return
            raise ValidationError(self.message)
        try:
            field.data = datetime.strptime(str(data).strip(), '%m/%d/%Y')
        except (ValueError, TypeError):
            raise ValidationError(self.message)

# NOTE: Untested
class IdSelectField(SelectField):
    """SelectField that preserves the raw string for earlier validators then
    converts the final value to an int in a trailing validator.

    Behavior:
      - No submitted value -> self.data = None
      - Single submitted value -> self.data = raw string for other validators,
        then converted to int by the trailing validator.
    """
    def __init__(self, label=None, validators=None, message: TypingOptional[str] = None, **kwargs):
        self.message = message or 'Invalid id; value must be an integer'
        vlist = list(validators) if validators else []
        # Detect Optional() presence so empty inputs remain acceptable
        self._has_optional = any(isinstance(v, Optional) for v in vlist)
        # Append converter as the LAST validator so other validators see the raw string
        vlist.append(self._convert_to_int)
        super().__init__(label, validators=vlist, **kwargs)

    def pre_validate(self, form):
        """
        Skip WTForms' choices validation when choices is not provided server-side.
        If choices are present, defer to the normal SelectField behavior.
        """
        if getattr(self, 'choices', None) is None:
            return
        return super().pre_validate(form)

    def process_formdata(self, valuelist):
        # Preserve the raw string for other validators; normalize empty -> None when appropriate
        if not valuelist:
            self.data = None
            return
        raw = valuelist[0]
        if isinstance(raw, str) and raw.strip() == '':
            if self._has_optional:
                self.data = None
            else:
                self.data = raw
            return
        self.data = raw

    def _convert_to_int(self, form, field):
        data = field.data
        if data is None or (isinstance(data, str) and str(data).strip() == ''):
            if self._has_optional:
                field.data = None
                return
            raise ValidationError(self.message)
        try:
            field.data = int(str(data).strip())
        except (ValueError, TypeError):
            raise ValidationError(self.message)

class IdSelectMultipleField(SelectMultipleField):
    """SelectMultipleField that keeps raw string values for other validators,
    then converts them to a list[int] as the last validation step.

    Behavior:
      - No submitted values -> self.data = None
      - Single submitted value -> self.data = ['raw_string']
      - Multiple submitted values -> self.data = ['a','b','c']
    The conversion to ints happens in the _convert_to_ints validator appended
    last so any other validators (e.g. Optional(), custom validators expecting
    raw strings) run first.
    """
    def __init__(self, label=None, validators=None, message: TypingOptional[str] = None, **kwargs):
        self.message = message or 'Invalid id list; values must be integers'
        vlist = list(validators) if validators else []
        # Detect Optional() presence so empty inputs remain acceptable
        self._has_optional = any(isinstance(v, Optional) for v in vlist)
        # Append converter as the LAST validator
        vlist.append(self._convert_to_ints)
        super().__init__(label, validators=vlist, **kwargs)

    def pre_validate(self, form):
        """
        Skip WTForms' choices validation when choices is not provided server-side.
        (Which it isn't because materialize is generating the choices dynamically, so we can't pre-supply them in the form definitions)
        If choices are present, defer to the normal SelectMultipleField behavior.
        """
        if getattr(self, 'choices', None) is None:
            return
        return super().pre_validate(form)

    def process_formdata(self, valuelist):
        # Normalize incoming submission into None or a list of raw strings.
        # Leave conversion to ints to the validator so other validators see raw strings.
        if not valuelist:
            self.data = None
            return

        # Keep all non-empty, stripped string values
        parts = [str(v).strip() for v in valuelist if v is not None and str(v).strip() != '']
        if not parts:
            self.data = None
            return

        self.data = parts

    def _convert_to_ints(self, form, field):
        data = field.data
        # If empty and Optional() present, let Optional short-circuit (data stays None)
        if data is None:
            if self._has_optional:
                field.data = None
                return
            raise ValidationError(self.message)

        # Accept a single string (defensive) or a list of strings
        if isinstance(data, str):
            tokens = [data.strip()] if data.strip() != '' else []
        elif isinstance(data, (list, tuple)):
            tokens = [str(x).strip() for x in data if x is not None and str(x).strip() != '']
        else:
            raise ValidationError(self.message)

        if not tokens:
            if self._has_optional:
                field.data = None
                return
            raise ValidationError(self.message)

        out = []
        for t in tokens:
            try:
                out.append(int(t))
            except (ValueError, TypeError):
                raise ValidationError(self.message)
        field.data = out

class TTypeSelectMultipleField(SelectMultipleField):
    """SelectMultipleField that keeps raw string values for other validators,
    then converts them to a list[int] as the last validation step.

    Behavior:
      - No submitted values -> self.data = None
      - Single submitted value -> self.data = ['raw_string']
      - Multiple submitted values -> self.data = ['a','b','c']
    The conversion to ints happens in the _convert_to_ints validator appended
    last so any other validators (e.g. Optional(), custom validators expecting
    raw strings) run first.
    """
    def __init__(self, label=None, validators=None, message: TypingOptional[str] = None, **kwargs):
        self.message = message or 'Invalid transaction type; submitted value must be an integer corresponding to a valid transaction type'
        vlist = list(validators) if validators else []
        # Detect Optional() presence so empty inputs remain acceptable
        self._has_optional = any(isinstance(v, Optional) for v in vlist)
        # Append converter as the LAST validator
        vlist.append(self._convert_to_ints)
        super().__init__(label, validators=vlist, **kwargs)

    def pre_validate(self, form):
        """
        Skip WTForms' choices validation when choices is not provided server-side.
        (Which it isn't because materialize is generating the choices dynamically, so we can't pre-supply them in the form definitions)
        If choices are present, defer to the normal SelectMultipleField behavior.
        """
        if getattr(self, 'choices', None) is None:
            return
        return super().pre_validate(form)

    def process_formdata(self, valuelist):
        # Normalize incoming submission into None or a list of raw strings.
        # Leave conversion to ints to the validator so other validators see raw strings.
        if not valuelist:
            self.data = None
            return

        # Keep all non-empty, stripped string values
        parts = [str(v).strip() for v in valuelist if v is not None and str(v).strip() != '']
        if not parts:
            self.data = None
            return

        self.data = parts

    def _convert_to_ints(self, form, field):
        data = field.data
        # If empty and Optional() present, let Optional short-circuit (data stays None)
        if data is None:
            if self._has_optional:
                field.data = None
                return
            raise ValidationError(self.message)

        # Accept a single string (defensive) or a list of strings
        if isinstance(data, str):
            tokens = [data.strip()] if data.strip() != '' else []
        elif isinstance(data, (list, tuple)):
            tokens = [str(x).strip() for x in data if x is not None and str(x).strip() != '']
        else:
            raise ValidationError(self.message)

        if not tokens:
            if self._has_optional:
                field.data = None
                return
            raise ValidationError(self.message)

        out = []
        for t in tokens:
            try:
                out.append(TType.from_int(int(t)))
            except (ValueError, TypeError):
                raise ValidationError(self.message)
        field.data = out


# endregion ---------------CUSTOM FIELDS---------------

# region ---------------FORMS--------------- 

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
        [Optional()],
        render_kw={"placeholder": "$0.00", "tabindex": "-1", "class": "special-input blue-grey-text white t-search-input validate"}
    )

    search_amt_max = AmtStringField(
        "Max. Amt",
        [Optional()],
        render_kw={"placeholder": "$0.00", "tabindex": "-1", "class": "special-input blue-grey-text white t-search-input validate"}
    )

    search_date_min = DateStringField(
        "Min. Date",
        [Optional()],
        allow_empty=True,
        render_kw={"placeholder": "MM/DD/YYYY", "tabindex": "-1", "class": "datepicker blue-grey-text white t-search-input validate", "pattern": r"^((0|1)\d{1})/((0|1|2|3)\d{1})/((19|20)\d{2})$"}
    )

    search_date_max = DateStringField(
        "Max. Date",
        [Optional()],
        allow_empty=True,
        render_kw={"placeholder": "MM/DD/YYYY", "tabindex": "-1", "class": "datepicker blue-grey-text white t-search-input validate", "pattern": r"^((0|1)\d{1})/((0|1|2|3)\d{1})/((19|20)\d{2})$"}
    )

    # NOTE: This field is not placed into the template with jinja, but rather a select element is directly given the id
    # This is because materialize generates new input elements for selects 
    search_envelope_ids = IdSelectMultipleField(
        "Envelope IDs",
        [Optional()]
    )

    # NOTE: This field is not placed into the template with jinja, but rather a select element is directly given the id
    # This is because materialize generates new input elements for selects 
    search_account_ids = IdSelectMultipleField(
        "Account IDs",
        [Optional()]
    )

    # NOTE: This field is not placed into the template with jinja, but rather a select element is directly given the id
    # This is because materialize generates new input elements for selects 
    search_transaction_types = TTypeSelectMultipleField(
        "Transaction Types",
        [Optional()]
    )


    def validate(self):
        """Run standard validators then enforce cross-field constraints
        (min <= max for amounts and dates). Attach errors to both fields
        when constraint fails.
        """
        rv = super().validate()
        if not rv:
            return False

        ok = True

        # Amounts: values are converted to integer cents by AmtStringField
        a_min = self.search_amt_min.data
        a_max = self.search_amt_max.data
        if a_min is not None and a_max is not None:
            if a_min > a_max:
                error_msg = 'min amt > max amt'
                self.search_amt_min.errors.append(error_msg) # type: ignore
                self.search_amt_max.errors.append(error_msg) # type: ignore
                ok = False

        # Dates: values are converted to datetime by DateStringField
        d_min = self.search_date_min.data
        d_max = self.search_date_max.data
        if d_min is not None and d_max is not None:
            if d_min > d_max:
                error_msg = "min date > max date"
                self.search_date_min.errors.append(error_msg) # type: ignore
                self.search_date_max.errors.append(error_msg) # type: ignore
                ok = False

        return ok

# endregion ---------------FORMS---------------