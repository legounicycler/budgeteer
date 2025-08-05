$(document).ready(function(){

     // Initialize Loading spinners
    var $loading = $('#loading-div').hide();

    // Make $loading globally accessible within the Budgeteer namespace
    // This allows other scripts to show or hide the loading spinner as needed
    window.Budgeteer = window.Budgeteer || {};
    Budgeteer.loadingSpinner = $loading;

    //Initialize Loading spinners
    $(document).ajaxStart(function () {
        Budgeteer.loadingSpinner.show();
    }).ajaxStop(function () {
        Budgeteer.loadingSpinner.hide();
     });

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
            const errorUrl = `/error/${jqXHR.status}?errorDesc=${jqXHR.responseText}`;
            window.location.replace(errorUrl);
            }
        }
        }
    });
    
}); // end of document ready