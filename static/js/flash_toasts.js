// This file is used in the layout.html, reset_password.html, and login.html templates
// Display the flashed messages s that have been added with flask's flash function as materialize toasts

$(document).ready(function(){

    $("#flash-toasts").children().each(function() {
      M.toast({html: $(this).html()});
      $(this).remove();
    });

});