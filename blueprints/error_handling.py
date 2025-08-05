"""
errors.py
This file configures the error handling routes for the flask application
It also processes the form data from the bug report form found on the error page and on the home page.
"""

#Flask imports
from flask import Blueprint, request, current_app, render_template, jsonify
from flask_login import login_required
from flask_mail import Message

#Library imports
import traceback, os
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

#Custom imports
from blueprints.auth import generate_uuid, get_uuid_from_cookie, check_confirmed
from forms import BugReportForm
from exceptions import InvalidFileSizeError
from textLogging import log_write

error_handling_bp = Blueprint('bug_report', __name__)

# Error handler for HTTP exceptions (for ajax requests)
@error_handling_bp.route('/error/<int:error_code>')
def error_page(error_code):
    error_desc = request.args.get('errorDesc') # Fetch the errorDesc query parameter from the ajax request
    return render_template("error_page.html", message=f"Error {error_code}: {error_desc}"), error_code

@error_handling_bp.errorhandler(404)
def not_found(e):
    return render_template("error_page.html", message=f"404 Error: The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."), 404

# Error handler for HTTP exceptions
@error_handling_bp.errorhandler(HTTPException)
def handle_exception(e):
    log_write(f'HTTP ERROR: {e}', "EventLog.txt")
    log_write(f'\n{traceback.format_exc()}', "EventLog.txt")
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # If error happens in an ajax request, return a response with the error message rather than rendering the error_page template
    #    This is because the ajax request will redirect via javascript to the /error route below which renders the template
    if is_ajax:
      response = jsonify({'error_message': e.description})
      response.status_code = e.code
      return response
    return render_template('error_page.html', message=f"Error {e.code}: {e.description}", bug_report_form = BugReportForm()), e.code

@error_handling_bp.route('/bug-report', methods=['POST'])
@login_required
@check_confirmed
def bug_report():
  try:
    form = BugReportForm()
    name = form.bug_reporter_name.data
    email = form.bug_reporter_email.data
    desc = form.bug_description.data
    screenshot = form.screenshot.data
    uuid = get_uuid_from_cookie() #TODO: Test this with a non-logged in client
    bug_report_id = generate_uuid()
    timestamp = request.form.get('timestamp')

    if not form.validate():
      return jsonify({'success': False, 'error': form.errors})

    if screenshot:
      allowed_file_size(screenshot)
      screenshot.filename = secure_filename(screenshot.filename)
      screenshot.save(os.path.join(current_app.config['UPLOAD_FOLDER'], screenshot.filename))
    
    send_bug_report_email_developer(uuid, name, email, desc, bug_report_id, timestamp, screenshot)  # Send bug report email to the developer
    send_bug_report_email_user(name, email, bug_report_id) # Send confirmation email to the user
    
    return jsonify({'success': True,'toasts': ["Thank you! Your bug report has been submitted!"]})
  except Exception as e:
    log_write(f'BUG REPORT ERROR: {e}', "EventLog.txt")
    log_write(f'\n{traceback.format_exc()}', "EventLog.txt")
    return jsonify({'success': False, "error": str(e)})

def send_bug_report_email_developer(uuid, name, email, desc, bug_report_id, timestamp, screenshot):
  msg = Message(f'Budgeteer: Bug Report from {email}', sender=current_app.config["MAIL_USERNAME"], recipients=[current_app.config["MAIL_USERNAME"]])
  if screenshot:
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], screenshot.filename)
    with current_app.open_resource(file_path) as fp:
      msg.attach(screenshot.filename, "image/png", fp.read())
    os.remove(file_path)
  msg.html = render_template("emails/bug_report_developer.html", uuid=uuid, name=name, email=email, desc=desc, bug_report_id=bug_report_id, timestamp=timestamp)
  current_app.mail.send(msg)

def send_bug_report_email_user(name, email, bug_report_id):
  msg = Message('Budgeteer: Your Bug Report Has Been Received', sender=current_app.config["MAIL_USERNAME"], recipients=[email])
  msg.html = render_template("emails/bug_report_user.html", name=name, email=email, bug_report_id=bug_report_id)
  current_app.mail.send(msg)

def allowed_file_size(file):
  MAX_FILE_SIZE = 1024*1024*10 # 10Mb
  file_data = file.read()
  file_size = len(file_data) # in bytes
  file.seek(0) # Reset the file pointer to the beginning of the file so it can be saved properly
  if file_size >= MAX_FILE_SIZE:
      raise InvalidFileSizeError(f"The file you uploaded is too large! ({round(file_size/(1024*1024), 2)}Mb). Please upload a file smaller than {round(MAX_FILE_SIZE/(1024*1024), 0)}Mb.")