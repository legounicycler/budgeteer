(function($){
    $(function(){

        //-------------MATERIALIZE INITIALIZATION FUNCTIONS-------------//
    $(document).ready(function(){

        //Initialize Loading spinners
        var $loading = $('#loading-div').hide();
        $(document)
          .ajaxStart(function () {
            $loading.show();
          })
          .ajaxStop(function () {
            $loading.hide();
          });

        // Initialize forgot password modal
        $('.modal').modal();
  
        // AJAX request for login form
        $('#login-form').submit(function(e) {
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
                  if (o.login_success) {
                    window.location.href= "home";
                  } else {
                    M.toast({html: o.message});
                  }
                });
            }).catch( function(error) {
              $loading.hide();
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
          $loading.show();
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
                    M.toast({html: o.message});
                  }
                });
            }).catch( function(error) {
              $loading.hide();
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
                    $("#reset-email").removeClass("valid").addClass("invalid");
                    $("#forgot-password-email-error").attr("data-error", o.message).removeClass("hide");
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
          M.toast({html: $(this).html()});
          $(this).remove();
        });

      }); // end of document ready

    });
})(jQuery); // end of jQuery name space