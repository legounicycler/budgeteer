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
  
      //Initialize Loading spinners
      var $loading = $('#loading-div').hide();
      $(document)
        .ajaxStart(function () {
          $loading.show();
        })
        .ajaxStop(function () {
          $loading.hide();
        });
  
        $("#bug-report-modal").modal();

        // AJAX request for bug submit form
        $('#bug-report-form').submit(function(e) {
            e.preventDefault();
            var url = $(this).attr('action');
            var method = $(this).attr('method');
            var $form = $(this);
            var $parentModal = $("#bug-report-modal");
            var formData = new FormData(this);
            formData.append('timestamp', gen_timestamp());
            $.ajax({
                type: method,
                url: url,
                cache: false,
                contentType: false,
                processData: false,
                data: formData
            }).done(function( o ) {
                if (o.success) {
                    $parentModal.modal("close");
                    $form[0].reset(); //Clears the data from the form fields
                } else {
                    if (o.errors) {displayFieldErrors(o.errors);}
                }
                o['toasts'].forEach((toast) => M.toast({html: toast})); //Display toasts
            });
        });
  
      }); // end of document ready
  
    });
  })(jQuery); // end of jQuery name space