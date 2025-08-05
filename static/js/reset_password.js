(function($){
  $(function(){

  $(document).ready(function(){

    $.ajaxSetup({
      // Default timeout for AJAX requests (15 seconds)
      timeout: 15000,

      // Global error handler
      error: function(jqXHR, textStatus) {
        if (textStatus === 'timeout') {
          // TODO: Handle timeout errors by aborting the request
        } else {
          // Redirect to error page with error code and errorDesc
          if (jqXHR.responseJSON) {
            // Display the more verbose error message returned from the flask error handler stored in the responseJSON.error_message
            const errorUrl = `/error/${jqXHR.status}?errorDesc=${jqXHR.responseJSON.error_message}`;
            window.location.replace(errorUrl);
          } else {
            // If the responseJSON is not available, fall back to the less verbose responseText
            const errorUrl = `/error/${jqXHR.status}?errorDesc=${jqHXR.responseText}`;
            window.location.replace(errorUrl);
          }
        }
      }
    });

    //Initialize Loading spinners
    var $loading = $('#loading-div').hide();
    $(document)
      .ajaxStart(function () {
        $loading.show();
      })
      .ajaxStop(function () {
        $loading.hide();
      });

      // AJAX request for login form
      $('#password-reset-form').submit(function(e) {
        e.preventDefault()
        var url = $(this).attr('action');
        var method = $(this).attr('method');
        var sitekey = $(this).data('sitekey');
        $form = $(this);
        $loading.show();
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
            $loading.hide();
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