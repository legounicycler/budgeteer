// Common function used across multiple files (init.js, login.js, reset_password.js, error_page.js) (any top level template page that has a form)
// This function displays field errors in the form by updating the helper text next to each field

// function clearFieldErrors($form) {
//   $form.find('.helper-text').each(function(){
//     // Preserve the helper element's data-error attribute (template default).
//     $(this).removeAttr('server-error');
//   });
//   $form.find('.invalid').removeClass('invalid');
// }

function displayFieldErrors(errors) {
  console.log("errors", errors);
  Object.keys(errors).forEach(function (fieldName) {
    var msgs = errors[fieldName];
    var msg = msgs[0]; //Only display the first error message (there will be multiple if multiple validators fail at once)
    var $field = $('#' + fieldName);
    var $helper = $field.siblings('.helper-text');
    $helper.attr('data-server-error', msg);
    $field.addClass("invalid").removeClass("valid");
  });
}