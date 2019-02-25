$(document).ready(function() {
  $("#new_plan").click(function() {
    $("#plan_creator").toggle("fast");
  });
  
  
  
  //Initialization
  $('.datepicker').pickadate({
    selectMonths: true, // Creates a dropdown to control month
    selectYears: 10 // Creates a dropdown of 10 years to control year
  });
  
  $('select').material_select();
  
  $('.carousel').carousel();
  
  $("#plan_creator").hide();
});