// This js file is used in the reset_password.html template

(function($){
  $(function(){

  $(document).ready(function(){

      // AJAX request for login form
      $('#password-reset-form').submit(function(e) {
        e.preventDefault()
        var url = $(this).attr('action');
        var method = $(this).attr('method');
        var sitekey = $(this).data('sitekey');
        $form = $(this);
        Budgeteer.loadingSpinner.show();
        grecaptcha.ready(function() {
          grecaptcha.execute(sitekey, {action: 'submit'}).then(
            function(token) {
              $.ajax({
                type: method,
                url: url,
                data: $form.serialize() + "&recaptchaToken=" + token,
              }).done(function( o ) {
                if (o.success) {
                  window.location.href = "../login";
                } else {
                  if (o.errors) {displayFieldErrors(o.errors);}
                  // M.toast({html: o.message});
                }
              });
          }).catch( function(error) {
            Budgeteer.loadingSpinner.hide();
            M.toast({html: "Error: Unknown ReCaptcha error!"})
          });
        });
      });

      // Display the toasts that have been added with flask's flash function
      $("#flash-toasts").children().each(function() {
        M.toast({html: $(this).html(), displayLength: Infinity});
        $(this).remove();
      });

    }); // end of document ready

  });
})(jQuery); // end of jQuery name space