(function($){
  $(function(){

    $('.button-collapse').sideNav();

    $(document).ready(function(){
    $('.modal').modal();
  });

    $(document).ready(function(){
    $('.tabs').tabs();
  });

    $('.datepicker').pickadate({
    selectMonths: true, // Creates a dropdown to control month
    selectYears: 10 // Creates a dropdown of 10 years to control year
  });

    $('select').material_select();

    $(document).on('change', '.div-toggle', function() {
    var target = $(this).data('target');
    var show = $("option:selected", this).data('show');
    $(target).children().addClass('hide');
    $(show).removeClass('hide');
    });
    $(document).ready(function(){
      $('.div-toggle').trigger('change');
    });

  }); // end of document ready
})(jQuery); // end of jQuery name space