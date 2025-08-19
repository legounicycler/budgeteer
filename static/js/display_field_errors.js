// Common function used across multiple files (init.js, login.js, reset_password.js, error_page.js) (any top level template page that has a form)
// This function displays field errors in the form by updating the helper text next to each field

function displayFieldErrors(errors) {
    // Display errors for each field
    Object.keys(errors).forEach(function (fieldName) {
        var errorMessages = errors[fieldName];
        var fieldId = '#' + fieldName;
        var errorContainer = $(fieldId).siblings('.helper-text');

        // Display the first error for each field
        if (errorMessages.length > 0) {
            $(fieldId).removeClass('valid').addClass('invalid');
            errorContainer.text(errorMessages[0]);
        }
    });
}