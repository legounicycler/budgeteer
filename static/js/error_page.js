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
  
      }); // end of document ready
  
    });
  })(jQuery); // end of jQuery name space