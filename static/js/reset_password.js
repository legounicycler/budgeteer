(function($){
    $(function(){

        //-------------MATERIALIZE INITIALIZATION FUNCTIONS-------------//
    $(document).ready(function(){

        // Display the toasts that have been added with flask's flash function
        $("#flash-toasts").children().each(function() {
          M.toast({html: $(this).html(), displayLength: Infinity});
          $(this).remove();
        });

      }); // end of document ready

    });
})(jQuery); // end of jQuery name space