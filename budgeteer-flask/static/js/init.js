(function($){
  $(function(){

    //-------------MATERIALIZE INITIALIZATION FUNCTIONS-------------//
    $(document).ready(function(){

      // Prevents tabs flashing content for a second on document reload
      $('#envelopes, #accounts').removeClass('hide');

      // Initializes tabs indicator on modal open
      $('.modal').modal({
        onOpenEnd: function () {
            $('.modal').find('.tabs').tabs();
          }
      });

      $('.sidenav').sidenav({
        onOpenStart: function() {$('#new-transaction-button').hide()},
        onCloseEnd: function() {$('#new-transaction-button').show()}
      });

      $('.tabs').tabs();

      $('select').formSelect();

      $('.datepicker').datepicker({
        autoClose: true,
        format: 'mm/dd/yyyy'
      });

      // Removes user-added rows in editor when the modal is closed
      $('#editor-modal').modal({
        onCloseEnd: function() { // Callback for Modal close
          $(".new-envelope-row").remove()
        }
      });

      $('.div-toggle').trigger('change');

      $('.button-collapse').sidenav();

    });


    //-------------OTHER FUNCTIONS-------------//


    function data_reload() {
      $.ajax({
        type: "GET",
        url: "/api/transactions",
      }).done(function( o ) {
        $('#transactions-bin').replaceWith(o);
         M.toast({html: 'Reloaded transactions!'})
      });

      $.ajax({
        type: "GET",
        url: "/api/accounts",
      }).done(function( o ) {
        $('#accounts-bin').replaceWith(o);
        M.toast({html: 'Reloaded accounts!'})
      });

      $.ajax({
        type: "GET",
        url: "/api/envelopes",
      }).done(function( o ) {
        $('#envelopes-bin').replaceWith(o);
         M.toast({html: 'Reloaded envelopes!'})
      });

      $.ajax({
        type: "GET",
        url: "/api/total",
      }).done(function( o ) {
        $('#total span').text(o);
         if (o[0] == '-') {
          $('#total span').addClass('negative')
         } else {
          $('#total span').removeClass('negative')
         };
         M.toast({html: 'Reloaded total!'})
      });
    }

    //TOGGLER CODE for transfer tab of transaction creator
    $(document).on('change', '.div-toggle', function() {
      var target = $(this).data('target');
      var show = $("option:selected", this).data('show');
      $(target).children().addClass('hide');
      $(show).removeClass('hide');
    });

    $('#new-expense-form').submit(function(e) {
      e.preventDefault()
      var url = $(this).attr('action');
      var method = $(this).attr('method');

      $.ajax({
        type: method,
        url: url,
        data: $(this).serialize(),
      }).done(function( o ) {
        data_reload();
      });
    });

    //ACCOUNT/ENVELOPE EDITOR code
    $("#new-account-row").click(function() {
      $("#account-editor-bin").append('<li class="row account-row collection-item"><div class="col s1 valign-wrapper account-icon editor-col"><i class="material-icons">account_balance</i></div><div class="col s8 account-name left-align editor-col input-field"><input required id="edit-account-name" class="validate" type="text" name="edit-account-name-' + Math.random() +'"><span class="helper-text" data-error="Account name required"></span></div><div class="col s2 account-balance editor-col input-field"><input required id="edit-balance" class="validate" type="text" name="new-balance" pattern="^[-]?([1-9]{1}[0-9]{0,}(\\.[0-9]{0,2})?|0(\\.[0-9]{0,2})?|\\.[0-9]{1,2})$"><span class="helper-text" data-error="Please enter a numeric value"></span></div><div class="col s1 valign-wrapper delete-account editor-col"><a href="#!" class="delete-account-button"><i class="material-icons red-text">delete_forever</i></a></div></li>');
      //Creates event handler for new account row each time
      $(".delete-account-button").on("click", function() { $(this).closest('.collection-item').remove(); })
    });

    $(".delete-account-button").click(function() {
      $(this).closest('.collection-item').remove();
    });

    $("#new-envelope-row").click(function() {
      $("#envelope-editor-bin").append('<li class="row envelope-row collection-item"><div class="col s1 valign-wrapper envelope-icon editor-col"><i class="material-icons">mail_outline</i></div><div class="col s5 envelope-name left-align editor-col input-field"><input required id="edit-envelope-name" class="validate" type="text" name="new-envelope-name-' + Math.random() + '"><span class="helper-text" data-error="Envelope name required"></span></div><div class="col s2 envelope-budget editor-col input-field"><input required id="edit-envelope-budget" class="validate" type="text" name="new-envelope-budget" pattern="^[-]?([1-9]{1}[0-9]{0,}(\\.[0-9]{0,2})?|0(\\.[0-9]{0,2})?|\\.[0-9]{1,2})$"><span class="helper-text" data-error="Please enter a numeric value"></span></div><div class="col s3 valign-wrapper envelope-balance editor-col"><span class="balance neutral">$0.00</span></div><div class="col s1 valign-wrapper delete-envelope editor-col"><a href="#!" class="delete-envelope-button"><i class="material-icons red-text">delete_forever</i></a></div></li>');
      //Creates event handler for new envelope row each time
      $(".delete-envelope-button").on("click", function() { $(this).closest('.collection-item').remove(); })
    });

    $(".delete-envelope-button").click(function() {
      $(this).closest('.collection-item').remove();
    });

    $("#add-envelope").click(function() {
      var $envelope_selector = $('#envelope-selector-row').find('#envelope_id').clone();
      $('#envelopes-and-amounts').append('<div class="row"><div class="input-field col s6 aclass"><label>Envelope</label></div><div class="input-field col s6 input-field"><input required id="amount" class="validate" type="text" name="amount" pattern="^[-]?([1-9]{1}[0-9]{0,}(\\.[0-9]{0,2})?|0(\\.[0-9]{0,2})?|\\.[0-9]{1,2})$"><label for="amount-">Amount</label><span class="helper-text" data-error="Please enter a numeric value"></span></div></div>');
      $(".aclass").last().prepend($envelope_selector).find("select").last().formSelect();
    });

    $("#remove-envelope").click(function() {
      // add something here eventually
    });

    $("#edit-add-envelope").click(function() {
      var $envelope_selector = $('#edit-envelope-selector-row').find('#edit-envelope_id').clone();
      $('#edit-envelopes-and-amounts').append('<div class="row new-envelope-row"><div class="input-field col s6 aclass"><label>Envelope</label></div><div class="input-field col s6 input-field"><input required id="amount" class="validate" type="text" name="amount" pattern="^[-]?([1-9]{1}[0-9]{0,}(\\.[0-9]{0,2})?|0(\\.[0-9]{0,2})?|\\.[0-9]{1,2})$"><label for="amount">Amount</label><span class="helper-text" data-error="Please enter a numeric value"></span></div></div>');
      $(".aclass").last().prepend($envelope_selector).find("select").last().formSelect();
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
         M.toast({html: 'I am a toast!'})
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
        M.toast({html: 'I am a toast!'})
        location.reload()
      });
    });

    // $('#new-expense, #edit-expense').submit(function(e) {
    //   e.preventDefault()
    //   if (event.target.id == 'new-expense') {
    //     console.log("new expense clicked")
    //     var $inputs = $('#new-expense :input').not($('.datepicker-modal :input')).not(':input[type=button], :input[type=submit], :input[type=reset]');
    //   } else if (event.target.id == 'edit-expense') {
    //     console.log("edit expense clicked")
    //     var $inputs = $('#edit-expense :input').not($('.datepicker-modal :input')).not($('.button-row :input')).not(':input[type=button], :input[type=submit], :input[type=reset]');
    //   }
    //   var fields = {};
    //   var temp = [];
    //   var envelope_ids = [];
    //   var amounts = [];
    //   $inputs.each(function() {
    //       temp.push($(this).val());
    //   });
    //   console.log(temp)
    //   var name = temp.shift();
    //   var note = temp.pop();
    //   var date = temp.pop();
    //   var account_id = temp.pop();
    //   temp.pop();
    //   for (i=0 ; i<temp.length ; i+=3) {
    //     envelope_ids.push(parseInt(temp[i+1]));
    //     amounts.push(parseFloat(temp[i+2]));
    //   };
    //   fields['name'] = name;
    //   fields['note'] = note;
    //   fields['date'] = date;
    //   fields['account_id'] = account_id;
    //   fields['envelope_ids'] = envelope_ids;
    //   fields['amounts'] = amounts;
    //   console.log(fields)

    //   if (event.target.id == 'new-expense') {
    //     $.ajax({
    //       type: "POST",
    //       url: "/new_expense",
    //       data: JSON.stringify(fields),
    //       contentType: 'application/json'
    //     }).done(function( o ) {
    //        location.reload()
    //     });
    //   } else if (event.target.id == 'edit-expense') {
    //     $.ajax({
    //       type: "POST",
    //       url: "/edit_expense",
    //       data: JSON.stringify(fields),
    //       contentType: 'application/json'
    //     }).done(function( o ) {
    //     });
    //   }
    // });

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
      amt = -1 * parseFloat(amt.replace("$",""));
      var to_envelope = null;
      var from_envelope = null;

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
            envelope_ids = [];
            amounts = [];
            $.each(t_data, function(key, t) {
                envelope_ids.push(t['envelope_id']);
                amounts.push(t['amt']);
            });
            amt = amounts[0];
            envelope_id = envelope_ids[0];
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
        $('#edit-transfer_type').formSelect();
        if (type == 1) {
          $('.account-transfer').addClass('hide');
          $('.envelope-transfer').removeClass('hide');
          $('#edit-from_envelope').val(from_envelope);
          $('#edit-from_envelope').formSelect();
          $('#edit-to_envelope').val(to_envelope);
          $('#edit-to_envelope').formSelect();
        } else if (type == 2) {
          $('.envelope-transfer').addClass('hide');
          $('.account-transfer').removeClass('hide');
          $('#edit-to_account').val(to_account);
          $('#edit-to_account').formSelect();
          $('#edit-from_account').val(from_account);
          $('#edit-from_account').formSelect();
        }
        amt = Math.abs(amt);
      } else if (type == 3) {
        income_editor.appendTo('#editor-row');
        $("#edit-transaction").detach();
        $("#edit-transfer").detach();
        amt = amt * -1;
      } else if (type == 4) {
        transaction_editor.appendTo('#editor-row');
        $("#edit-transfer").detach();
        $("#edit-income").detach();
        for (i=1 ; i<envelope_ids.length ; i++) {
          var $envelope_selector = $('#edit-envelope-selector-row').find('#edit-envelope_id').clone();
          $('#edit-envelopes-and-amounts').append('<div class="row new-envelope-row"><div class="input-field col s6 aclass"><label class="no-active">Envelope</label></div><div class="input-field col s6 input-field"><input required id="amount" class="validate" type="text" name="amount" value="'+amounts[i].toFixed(2)+'" pattern="^[-]?([1-9]{1}[0-9]{0,}(\\.[0-9]{0,2})?|0(\\.[0-9]{0,2})?|\\.[0-9]{1,2})$"><label for="amount">Amount</label><span class="helper-text" data-error="Please enter a numeric value"></span></div></div>');
          $(".aclass").last().prepend($envelope_selector).find("select").last().val(envelope_ids[i]).formSelect();
        };
      };

      // update the rest of the general fields
      $("#editor-modal label").addClass("active");
      $(".no-active").removeClass("active");
      $("#edit-amount").val(amt.toFixed(2));
      $("#edit-date").val(date).datepicker({
        autoClose: true,
        format: 'mm/dd/yyyy'
      });
      $("#edit-name").val(name);
      $("#edit-note").val(note);
      $('#edit-envelope_id').val(envelope_id);
      $('#edit-envelope_id').formSelect();
      $('#edit-account_id').val(account_id);
      $('#edit-account_id').formSelect();
      $('#dtid').attr('value', id);
      $('#edit-id').attr('value', id);
      $('#type').attr('value', type);
    });

  }); // end of document ready
})(jQuery); // end of jQuery name space