// This js file is used in the login.html template

(function($){
    $(function(){

    $(document).ready(function(){

        // Initialize forgot password modal
        $('.modal').modal();
  
        // AJAX request for login form
        $('#login-form').submit(function(e) {
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
                  if (o.login_success) {
                    window.location.href= "home";
                  } else {
                    if (o.confirmed == false) {
                      window.location.href="unconfirmed";
                    } else {
                      if (o.errors) {displayFieldErrors(o.errors);}
                      M.toast({html: o.message});
                    }
                  }
                });
            }).catch( function(error) {
              Budgeteer.loadingSpinner.hide();
              M.toast({html: "Error: Unknown ReCaptcha error!"})
            });
          });
        });
  
  
        // AJAX request for account creation form
        $('#register-form').submit(function(e) {
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
                  if (o.register_success) {
                    $("#login-card-close").click();
                    setTimeout(()=>{},100);
                    $form[0].reset();
                    M.toast({html: o.message});
                  } else {
                    if (o.errors) {displayFieldErrors(o.errors);}
                    M.toast({html: o.message});
                  }
                });
            }).catch( function(error) {
              Budgeteer.loadingSpinner.hide();
              M.toast({html: "Error: Unknown ReCaptcha error!"})
            });
          });
        });

        // AJAX request for account creation form
        $('#forgot-password-form').submit(function(e) {
          e.preventDefault()
          var url = $(this).attr('action');
          var method = $(this).attr('method');
          var sitekey = $(this).data('sitekey');
          $form = $(this);
          grecaptcha.ready(function() {
            grecaptcha.execute(sitekey, {action: 'submit'}).then(
              function(token) {
                $.ajax({
                  type: method,
                  url: url,
                  data: $form.serialize() + "&recaptchaToken=" + token,
                }).done(function( o ) {
                  if (o.success) {
                    M.toast({html: o.message});
                    $('#forgot-password-modal').modal('close');
                    $form.trigger("reset");
                  } else {
                    if (o.message) {M.toast({html: o.message});}
                    if (o.errors) {displayFieldErrors(o.errors);}
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
          M.toast({html: $(this).html()});
          $(this).remove();
        });

      }); // end of document ready

    });
})(jQuery); // end of jQuery name space