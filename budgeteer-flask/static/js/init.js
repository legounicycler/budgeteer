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
    // SPECIAL NOTE: Modified the Materialize.js file to make it work in a modal

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


    var transaction_editor = $("#edit-transaction").detach()
    var transfer_editor = $("#edit-transfer").detach()
    var income_editor = $("#edit-income").detach()

    $(".transaction").on('click',function() {
      // get data from html data tags
      var id = $(this).data('id');
      var name = $(this).data('name')
      var type = $(this).data('type');
      var date = $(this).data('date');
      var envelope_name = $(this).data('envelope_id');
      var account_name = $(this).data('account_id');
      var grouping = $(this).data('grouping');
      var note = $(this).data('note');
      var amt = $(this).data('amt');
      amt = amt.slice(1)
      if (amt[0] == '-') {
        amt = amt.slice(1)
      } else {
        amt = '-' + amt
      }

      // Check which editor to show
      if (type == 0) {
        transaction_editor.appendTo('#editor-row')
        $("#edit-transfer").remove()
        $("#edit-income").remove()
      } else if (type == 1 || type == 2) {
        transfer_editor.appendTo('#editor-row')
        $("#edit-transaction").remove()
        $("#edit-income").remove()
        $('#edit-transfer_type').val(type);
        $('#edit-transfer_type').material_select();
        if (type == 1) {
          $('.account-transfer').addClass('hide');
          $('.envelope-transfer').removeClass('hide')
          $('#edit-to_envelope').val(envelope_name);
          $('#edit-to_envelope').material_select();
        } else if (type == 2) {
          $('.envelope-transfer').addClass('hide');
          $('.account-transfer').removeClass('hide')
          alert(account_name)
          $('#edit-to_account').val(account_name);
          $('#edit-to_account').material_select();
          // var to_envelope_id = $(this).data('envelope_id')
          // var from_envelope_id = $(this).data('from_envelope_id')

        }
      } else if (type == 3) {
        income_editor.appendTo('#editor-row')
        $("#edit-transaction").remove()
        $("#edit-transfer").remove()
      }

      // update field rows
      $("#editor-modal label").addClass("active");
      $(".no-active").removeClass("active");
      $("#edit-amount").val(amt);
      $("#edit-date").val(date);
      $("#edit-name").val(name);
      $("#edit-note").val(note);
      $('#edit-envelope_id').val(envelope_name);
      $('#edit-envelope_id').material_select();
      $('#edit-account_id').val(account_name);
      $('#edit-account_id').material_select();
      $('#dtid').attr('value', id);
    });

  }); // end of document ready
})(jQuery); // end of jQuery name space