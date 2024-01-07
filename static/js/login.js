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
            if (o['login_success']) {
              window.location.href= "home";
            } else {
              M.toast({html: o['message']});
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
            if (o.login_success) {
              window.location.href= "home";
            } else {
              M.toast({html: o.message})
            }
          });
        });

        $("#no-account").click(function(){
            $("#login-card").animate({height: $("#login-card .card-reveal").outerHeight()+100}, 500);
        });

        $("#login-card-close").click(function(){
            $("#login-card").animate({height: $("#login-card .card-content").outerHeight()}, 500);
        });

      }); // end of document ready

    });
})(jQuery); // end of jQuery name space