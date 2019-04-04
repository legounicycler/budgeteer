(function($){
  $(function(){

    //-------------MATERIALIZE INITIALIZATION FUNCTIONS-------------//

    // SPECIAL NOTE: Modified the Materialize.js file to make datepicker work in a modal
    $('.button-collapse').sideNav();

    $(document).ready(function(){
      $('.modal').modal();
    });

    $(document).ready(function(){
     $('.tabs').tabs();
    });

    $('select').material_select();

    $('.datepicker').pickadate({
      selectMonths: true, // Creates a dropdown to control month
      selectYears: 10, // Creates a dropdown of 10 years to control year
      onSet: function(ele) { if(ele.select) { this.close(); } },
      format: 'mm/dd/yyyy'
    });



    //-------------OTHER FUNCTIONS-------------//

    //TOGGLER CODE for transfer tab of transaction creator
    $(document).on('change', '.div-toggle', function() {
      var target = $(this).data('target');
      var show = $("option:selected", this).data('show');
      $(target).children().addClass('hide');
      $(show).removeClass('hide');
    });

    $(document).ready(function(){
      $('.div-toggle').trigger('change');
    });



    //ACCOUNT/ENVELOPE EDITOR code
    $("#new-account-row").click(function() {
      $("#account-editor-bin").append('<li class="row account-row collection-item"><div class="col s1 valign-wrapper account-icon editor-col"><i class="material-icons">account_balance</i></div><div class="col s8 account-name left-align editor-col"><input id="edit-account-name" type="text" name="edit-account-name-' + Math.random() + '"></div><div class="col s2 account-balance editor-col"><input id="edit-balance" type="text" name="new-balance"></div><div class="col s1 valign-wrapper delete-account editor-col"><a href="#!" class="delete-account-button"><i class="material-icons red-text">delete_forever</i></a></div></li>');
      //Create event handler for new account row each time
      $(".delete-account-button").on("click", function() { $(this).closest('.collection-item').remove(); })
    });

    $(".delete-account-button").click(function() {
      $(this).closest('.collection-item').remove();
    });

    $("#new-envelope-row").click(function() {
      $("#envelope-editor-bin").append('<li class="row envelope-row collection-item"><div class="col s1 valign-wrapper envelope-icon editor-col"><i class="material-icons">mail_outline</i></div><div class="col s5 envelope-name left-align editor-col"><input id="edit-envelope-name" type="text" name="new-envelope-name-' + Math.random() + '"></div><div class="col s2 envelope-budget editor-col"><input id="edit-envelope-budget" type="text" name="new-envelope-budget"></div><div class="col s3 valign-wrapper envelope-balance editor-col"><span class="balance neutral">$0.00</span></div><div class="col s1 valign-wrapper delete-envelope editor-col"><a href="#!" class="delete-envelope-button"><i class="material-icons red-text">delete_forever</i></a></div></li>');
      //Create event handler for new envelope row each time
      $(".delete-envelope-button").on("click", function() { $(this).closest('.collection-item').remove(); })
    });

    $(".delete-envelope-button").click(function() {
      $(this).closest('.collection-item').remove();
    });

    //COLLECTS DATA from account editor modal and sends it to python as a json
    $('#account-editor-form').submit(function(e) {
      //make sure there exists at least one account at all times
      e.preventDefault()
      // get all the inputs into an array.
      var $inputs = $('#account-editor-form :input').not(':input[type=button], :input[type=submit], :input[type=reset]');
      var accounts = {};
      var accounts_temp = [];
      $inputs.each(function() {
          accounts_temp.push(this.name);
          accounts_temp.push($(this).val());
      });

      for (i=0 ; i<accounts_temp.length ; i+=4) {
        var id = accounts_temp[i].slice(18);
        var name = accounts_temp[i+1];
        var balance = parseFloat(accounts_temp[i+3]);
        accounts[id] = [name, balance];
      }

      $.ajax({
        type: "POST",
        url: "/api/edit-accounts",
        data: JSON.stringify(accounts),
        contentType: 'application/json'
      }).done(function( o ) {
         location.reload()
      });
    });

    //COLLECTS DATA from envelope editor modal and sends it to python as a json
    $('#envelope-editor-form').submit(function(e) {
      //make sure there exists at least one account at all times
      e.preventDefault()
      // get all the inputs into an array.
      var $inputs = $('#envelope-editor-form :input').not(':input[type=button], :input[type=submit], :input[type=reset]');
      var envelopes = {};
      var envelopes_temp = [];
      $inputs.each(function() {
          envelopes_temp.push(this.name);
          envelopes_temp.push($(this).val());
      });

      for (i=0 ; i<envelopes_temp.length ; i+=4) {
        var id = envelopes_temp[i].slice(19);
        var name = envelopes_temp[i+1];
        console.log(name)
        var budget= parseFloat(envelopes_temp[i+3]);
        envelopes[id] = [name, budget];
      }

      $.ajax({
        type: "POST",
        url: "/api/edit-envelopes",
        data: JSON.stringify(envelopes),
        contentType: 'application/json'
      }).done(function( o ) {
         location.reload()
      });
    });



    //TRANSACTION EDITOR functions and variables
    var transaction_editor = $("#edit-transaction").detach()
    var transfer_editor = $("#edit-transfer").detach()
    var income_editor = $("#edit-income").detach()

    $(".transaction").on('click',function() {
      // get and format data from html data tags
      var id = $(this).data('id');
      var name = $(this).data('name');
      var type = $(this).data('type');
      var date = $(this).data('date');
      var envelope_name = $(this).data('envelope_name');
      var envelope_id = $(this).data('envelope_id');
      var account_name = $(this).data('account_name');
      var account_id = $(this).data('account_id');
      var grouping = $(this).data('grouping');
      var note = $(this).data('note');
      var amt = $(this).data('amt');
      amt = -1 * parseFloat(amt.slice(1))
      var to_envelope = null
      var from_envelope = null

      //if it's a grouped transaction, use ajax to get data from all grouped transaction
      if (grouping != 0) {
        $.ajax({
          async: false,
          type: "GET",
          url: "/api/transaction/" + id + "/group",
        }).done(function( o ) {
          var t_data = o["transactions"];
          if (type == 1) {
            var t1 = t_data[0];
            var t2 = t_data[1];
            if (t1["amt"] > 0) {
              to_envelope = t1["envelope_id"];
              from_envelope = t2["envelope_id"];
            } else {
              to_envelope = t2["envelope_id"];
              from_envelope = t1["envelope_id"];
            }
          } else if (type == 2) {
            var t1 = t_data[0];
            var t2 = t_data[1];
            if (t1["amt"] > 0) {
              to_account = t1["account_id"];
              from_account = t2["account_id"];
            } else {
              to_account = t2["account_id"];
              from_account = t1["account_id"];
            }
          } else if (type == 4) {
            console.log("add functionality for split transactions")
          }
        });
      }

      // Check which editor to show, detatch the others, and update the special fields
      if (type == 0) {
        transaction_editor.appendTo('#editor-row');
        $("#edit-transfer").detach();
        $("#edit-income").detach();
      } else if (type == 1 || type == 2) {
        transfer_editor.appendTo('#editor-row');
        $("#edit-transaction").detach();
        $("#edit-income").detach();
        $('#edit-transfer_type').val(type);
        $('#edit-transfer_type').material_select();
        if (type == 1) {
          $('.account-transfer').addClass('hide');
          $('.envelope-transfer').removeClass('hide');
          $('#edit-from_envelope').val(from_envelope);
          $('#edit-from_envelope').material_select();
          $('#edit-to_envelope').val(to_envelope);
          $('#edit-to_envelope').material_select();
        } else if (type == 2) {
          $('.envelope-transfer').addClass('hide');
          $('.account-transfer').removeClass('hide');
          $('#edit-to_account').val(to_account);
          $('#edit-to_account').material_select();
          $('#edit-from_account').val(from_account);
          $('#edit-from_account').material_select();
        }
        amt = Math.abs(amt);
      } else if (type == 3) {
        income_editor.appendTo('#editor-row');
        $("#edit-transaction").detach();
        $("#edit-transfer").detach();
        amt = amt * -1;
      }

      // update the rest of the general fields
      $("#editor-modal label").addClass("active");
      $(".no-active").removeClass("active");
      $("#edit-amount").val(amt.toFixed(2));
      $("#edit-date").val(date);
      $("#edit-name").val(name);
      $("#edit-note").val(note);
      $('#edit-envelope_id').val(envelope_id);
      $('#edit-envelope_id').material_select();
      $('#edit-account_id').val(account_id);
      $('#edit-account_id').material_select();
      $('#dtid').attr('value', id);
      $('#edit-id').attr('value', id);
      $('#type').attr('value', type);
    });

  }); // end of document ready
})(jQuery); // end of jQuery name space