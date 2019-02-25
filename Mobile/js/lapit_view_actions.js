$(document).ready(function() {
  $("#new_action").click(function() {
    $("#action_creator").toggle("fast");
  });
  
  
  
  //Initialization
  $('.datepicker').pickadate({
    selectMonths: true, // Creates a dropdown to control month
    selectYears: 10 // Creates a dropdown of 10 years to control year
  });
  
  $('select').material_select();
  
  $('.carousel').carousel();
  
  $("#action_creator").hide();
});