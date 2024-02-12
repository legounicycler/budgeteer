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
          $.ajax({
            type: method,
            url: url,
            data: $(this).serialize(),
          }).done(function( o ) {
            if (o.login_success) {
              window.location.href= "home";
            } else {
              M.toast({html: o.message});
            }
          });
        });
  
  
        // AJAX request for account creation form
        $('#register-form').submit(function(e) {
          e.preventDefault()
          var url = $(this).attr('action');
          var method = $(this).attr('method');
          $.ajax({
            type: method,
            url: url,
            data: $(this).serialize(),
          }).done(function( o ) {
            M.toast({html: o.message})
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
            grecaptcha.execute(sitekey, {action: 'submit'}).then(function(token) {
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
            });
          });
        });

        // Display the toasts that have been added with flask's flash function
        $("#flash-toasts").children().each(function() {
          console.log("TOAST");
          M.toast({html: $(this).html()});
          $(this).remove();
        });

      }); // end of document ready

    });
})(jQuery); // end of jQuery name space