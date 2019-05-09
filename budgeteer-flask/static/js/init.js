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
        onOpenStart: function() {$('.fixed-action-btn').hide()},
        onCloseEnd: function() {$('.fixed-action-btn').show()}
      });

      $('.tabs').tabs();

      $('select').formSelect();

      $('.datepicker').datepicker({
        autoClose: true,
        format: 'mm/dd/yyyy',
        defaultDate: new Date(),
        setDefaultDate: true,
        container: 'body'
      });

      // Removes user-added rows in editor when the modal is closed
      $('#editor-modal').modal({
        onCloseEnd: function() { // Callback for Modal close
          $(".new-envelope-row").remove()
        }
      });

      // initializes FAB
      $('.fixed-action-btn').floatingActionButton({
        direction: 'left',
        hoverEnabled: false
      });

      $('.div-toggle').trigger('change');

      $('.button-collapse').sidenav();

      $('.tooltipped').tooltip();

      $('.pushpin-demo-nav').each(function() {
        var $this = $(this);
        var $target = $('#' + $(this).attr('data-target'));
        $this.pushpin({
          top: $target.offset().top,
          bottom: $target.offset().top + $target.outerHeight() - $this.height()
        });
      });

      editor_binds()
    });


    //------------- FUNCTIONAL JS -------------//
    window.delete_target;

    // TOGGLER CODE for transfer tab of transaction creator
    $(document).on('change', '.div-toggle', function() {
      var target = $(this).data('target');
      var show = $("option:selected", this).data('show');
      $(target).children().addClass('hide');
      $(target).find('select').removeAttr('required');
      $(show).removeClass('hide').attr('required');
    });

    // Checks whether there are any current envelopes/accounts, and if not, adds a message in
    // the envelope/account editor modals
    function editor_row_check() {
      if ( $('#account-editor-bin').children().length == 1 ) {
        $('#account-editor-bin').append("<div class='row collection-item' id='no-accounts'><h5 class='no-margin'>You don't have any accounts yet!</h5></div>")
      };
      if ( $('#envelope-editor-bin').children().length == 1 ) {
        $('#envelope-editor-bin').append("<div class='row collection-item' id='no-envelopes'><h5 class='no-margin'>You don't have any envelopes yet!</h5></div>")
      };
    };

    function editor_binds() {
      editor_row_check()
      // Adds new envelope row on button click and clears temporary no-envelopes message if there is one
      $("#new-envelope-row").click(function() {
        $("#envelope-editor-bin").append('<li class="row envelope-row collection-item flex"><div class="col s1 valign-wrapper envelope-icon editor-col"><i class="material-icons">mail_outline</i></div><div class="col s4 envelope-name left-align editor-col input-field"><input required class="validate" type="text" name="new-envelope-name"><span class="helper-text" data-error="Envelope name required"></span></div><div class="col s2 envelope-budget editor-col input-field"><input required class="validate" type="text" name="new-envelope-budget" pattern="^[-]?([1-9]{1}[0-9]{0,}(\\.[0-9]{0,2})?|0(\\.[0-9]{0,2})?|\\.[0-9]{1,2})$"><span class="helper-text" data-error="Please enter a numeric value"></span></div><div class="col s3 valign-wrapper envelope-balance editor-col"><span class="balance neutral">$0.00</span></div><div class="col s2 valign-wrapper delete-envelope editor-col"><a href="#!" class="delete-envelope-button"><i class="material-icons red-text">delete_forever</i></a></div></li>');
        $('#no-envelopes').remove()
      });
      // Adds new account row on button click and clears temporary no-accounts message if there is one
      $("#new-account-row").click(function() {
        $("#account-editor-bin").append('<li class="row account-row collection-item flex"><div class="col s1 valign-wrapper account-icon editor-col"><i class="material-icons">account_balance</i></div><div class="col s7 account-name left-align editor-col input-field"><input required class="validate" type="text" name="new-account-name"><span class="helper-text" data-error="Account name required"></span></div><div class="col s2 account-balance editor-col input-field"><input required class="validate" type="text" name="new-account-balance" pattern="^[-]?([1-9]{1}[0-9]{0,}(\\.[0-9]{0,2})?|0(\\.[0-9]{0,2})?|\\.[0-9]{1,2})$"><span class="helper-text" data-error="Please enter a numeric value"></span></div><div class="col s2 valign-wrapper delete-account editor-col"><a href="#!" class="delete-account-button"><i class="material-icons red-text">delete_forever</i></a></div></li>');
        $('#no-accounts').remove()
      });

      // Opens delete warning modal when the delete button is clicked
      $("#envelope-editor-bin").on("click", ".delete-envelope-button", function() {
        window.delete_target = $(this);
        $('#delete-modal p').replaceWith('<p>This action cannot be undone. The balance of this envelope will be added to your unallocated balance.</p>');
        $('#delete-modal').modal('open');
      });

      // Opens delete warning modal when the delete button is clicked
      $("#account-editor-bin").on("click", ".delete-account-button", function() {
        window.delete_target = $(this);
        $('#delete-modal p').replaceWith('<p>This action cannot be undone. The balance of this account will be subtracted from your unallocated balance.</p>');
        $('#delete-modal').modal('open');
      });

      //COLLECTS DATA from account/envelope editor modals and submits it to flask
      $('#account-editor-form, #envelope-editor-form').submit(function(e) {
        e.preventDefault()
        var url = $(this).attr('action');
        var current_url = $(location).attr("href");
        var method = $(this).attr('method');
        $(".modal").modal("close")

        $.ajax({
          type: method,
          url: url,
          data: $(this).serialize(),
        }).done(function( o ) {
          data_reload(current_url);
          M.toast({html: o})
        });
      });
    };

    // If the yes button is clicked in the delete modal, delete the appropriate row,
    // and if it's the last row, add a placeholder HTML bit
    $('#yes').click(function() {
      window.delete_target.closest('.collection-item').remove();
      editor_row_check()
    });

    // Adds envelope row for transaction creator and initializes Material Select
    $("#add-envelope").click(function() {
      var $envelope_selector = $('#envelope-selector-row').find('#envelope_id').clone();
      $('#envelopes-and-amounts').append('<div class="row new-envelope-row"><div class="input-field col s6 aclass"><label>Envelope</label></div><div class="input-field col s6 input-field"><input required id="amount" class="validate" type="text" name="amount" pattern="^[-]?([1-9]{1}[0-9]{0,}(\\.[0-9]{0,2})?|0(\\.[0-9]{0,2})?|\\.[0-9]{1,2})$"><label for="amount-">Amount</label><span class="helper-text" data-error="Please enter a numeric value"></span></div></div>');
      $(".aclass").last().prepend($envelope_selector).find("select").last().formSelect();
    });

    // Removes new envelope row in transaction builder
    $("#remove-envelope").click(function() {
      // add something here eventually
    });

    // Adds envelope row for transaction editor and initializes Material Select
    $("#edit-add-envelope").click(function() {
      var $envelope_selector = $('#edit-envelope-selector-row').find('#edit-envelope_id').clone();
      $('#edit-envelopes-and-amounts').append('<div class="row new-envelope-row"><div class="input-field col s6 aclass"><label>Envelope</label></div><div class="input-field col s6 input-field"><input required id="amount" class="validate" type="text" name="amount" pattern="^[-]?([1-9]{1}[0-9]{0,}(\\.[0-9]{0,2})?|0(\\.[0-9]{0,2})?|\\.[0-9]{1,2})$"><label for="amount">Amount</label><span class="helper-text" data-error="Please enter a numeric value"></span></div></div>');
      $(".aclass").last().prepend($envelope_selector).find("select").last().formSelect();
    });

    // ----------------- FORM SUBMISSION/FILLING JS ------------------- //


    // Retrieves updated data from database and updates the necessary html
    function data_reload(current_url) {
      $.ajax({
        type: "POST",
        url: "/api/data-reload",
        data: JSON.stringify({"url": current_url}),
        contentType: 'application/json'
      }).done(function( o ) {
        $(".modal").modal("close")
        $('#transactions-bin').replaceWith(o['transactions_html']);
        $('#accounts-bin').replaceWith(o['accounts_html']);
        $('#envelopes-bin').replaceWith(o['envelopes_html']);

        $('#total span').text(o['total']);
        if (o['total'][0] == '-') {
          $('#total span').addClass('negative');
        } else {
          $('#total span').removeClass('negative');
        };

        $('#unallocated span').text(o['unallocated']);
        if (o['unallocated'][0] == '-') {
          $('#unallocated span').addClass('negative');
        } else {
          $('#unallocated span').removeClass('negative');
        };

        $('.select-wrapper:has(.account-selector)').replaceWith(o['account_selector_html']);
        $('.select-wrapper:has(.envelope-selector)').replaceWith(o['envelope_selector_html']);
        $('select').formSelect();

        $('#envelope-modal').replaceWith(o['envelope_editor_html']);
        $('#account-modal').replaceWith(o['account_editor_html']);
        $('#envelope-modal').modal();
        $('#account-modal').modal();
        editor_binds()
        console.log("Data successfully reloaded!")
      });
    };

    // Submits form data, closes the modal, clears the form, and reloads the data
    $('#transaction-modal form, #envelope-fill-form').submit(function(e) {
      e.preventDefault()
      var url = $(this).attr('action');
      var current_url = $(location).attr("href");
      var method = $(this).attr('method');
      var id = '#' + $(this).attr('id');
      $(".modal").modal("close")

      $.ajax({
        type: method,
        url: url,
        data: $(this).serialize(),
      }).done(function( o ) {
        $(id + ' .new-envelope-row').remove()
        $(id)[0].reset();
        M.updateTextFields();
        data_reload(current_url);
        M.toast({html: o})
      });
    });

    // Submits form data, closes the modal, clears the form, and reloads the data
    $('#edit-expense-form, #edit-transfer-form, #edit-income-form, #edit-envelope-fill-form').submit(function(e) {
      e.preventDefault()
      var url = $(this).attr('action');
      var current_url = $(location).attr("href");
      var method = $(this).attr('method');
      var id = '#' + $(this).attr('id');
      $(".modal").modal("close")

      $.ajax({
        type: method,
        url: url,
        data: $(this).serialize(),
      }).done(function( o ) {
        $(id)[0].reset();
        M.updateTextFields();
        data_reload(current_url);
        M.toast({html: o})
      });
    });

    // Sends delete ID via form, the reloads data
    $('.deleter-form').submit(function(e) {
      e.preventDefault()
      var url = $(this).attr('action');
      var current_url = $(location).attr("href");
      var method = $(this).attr('method');
      $(".modal").modal("close")

      $.ajax({
        type: method,
        url: url,
        data: $(this).serialize(),
      }).done(function( o ) {
        data_reload(current_url);
        M.toast({html: o})
      });
    });

    //TRANSACTION EDITOR functions and variables
    var transaction_editor = $("#edit-expense").detach()
    var transfer_editor = $("#edit-transfer").detach()
    var income_editor = $("#edit-income").detach()
    var envelope_fill_editor = $("#edit-envelope-fill").detach()

    $("#bin").on('click', '.transaction', function() {
      // gets and format data from html data tags
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
      if (grouping != 0 ) {
        $.ajax({
          async: false,
          type: "GET",
          url: "/api/transaction/" + id + "/group",
        }).done(function( o ) {
          var t_data = o["transactions"];
          // depending on the type, get/format different transaction data
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
          } else if (type == 5) {
            envelope_ids = [];
            amounts = [];
            $.each(t_data, function(key, t) {
                if (t['envelope_id'] != 1) {
                  envelope_ids.push(t['envelope_id']);
                  amounts.push(t['amt'] * -1);
                }
            });
          };
        });
      }

      // Check which editor to show, detatch the others, and update the special fields
      if (type == 0) {
        transaction_editor.appendTo('#editor-row');
        $("#edit-transfer").detach();
        $("#edit-income").detach();
        $("#edit-envelope-fill").detach();
      } else if (type == 1 || type == 2) {
        transfer_editor.appendTo('#editor-row');
        $("#edit-expense").detach();
        $("#edit-income").detach();
        $("#edit-envelope-fill").detach();
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
        $("#edit-expense").detach();
        $("#edit-transfer").detach();
        $("#edit-envelope-fill").detach();
        amt = amt * -1;
      } else if (type == 4) {
        transaction_editor.appendTo('#editor-row');
        $("#edit-transfer").detach();
        $("#edit-income").detach();
        $("#edit-envelope-fill").detach();
        for (i=1 ; i<envelope_ids.length ; i++) {
          var $envelope_selector = $('#edit-envelope-selector-row').find('#edit-envelope_id').clone();
          $('#edit-envelopes-and-amounts').append('<div class="row new-envelope-row"><div class="input-field col s6 aclass"><label>Envelope</label></div><div class="input-field col s6 input-field"><input required id="amount" class="validate" type="text" name="amount" value="'+amounts[i].toFixed(2)+'" pattern="^[-]?([1-9]{1}[0-9]{0,}(\\.[0-9]{0,2})?|0(\\.[0-9]{0,2})?|\\.[0-9]{1,2})$"><label for="amount">Amount</label><span class="helper-text" data-error="Please enter a numeric value"></span></div></div>');
          $(".aclass").last().prepend($envelope_selector).find("select").last().val(envelope_ids[i]).formSelect();
        }
      } else if (type == 5) {
        envelope_fill_editor.appendTo('#editor-row');
        $("#edit-transfer").detach();
        $("#edit-income").detach();
        $("#edit-expense").detach();
        var $inputs = $('#edit-envelope-editor-bin :input[type=text]')
        $inputs.each(function() {
          if (envelope_ids.includes($(this).data("envelope-id"))) {
            $(this).val(amounts[envelope_ids.indexOf($(this).data("envelope-id"))].toFixed(2))
          }
        });
      }

      // update the rest of the general fields
      $("#edit-amount").val(amt.toFixed(2));
      $("#edit-date").val(date).datepicker({
        autoClose: true,
        format: 'mm/dd/yyyy',
        container: 'body'
      });
      var datepicker = document.getElementById('edit-date');
      var instance = M.Datepicker.getInstance(datepicker);
      instance.setDate(new Date(date));
      $("#edit-name").val(name);
      $("#edit-note").val(note);
      $('#edit-envelope_id').val(envelope_id);
      $('#edit-envelope_id').formSelect();
      $('#edit-account_id').val(account_id);
      $('#edit-account_id').formSelect();
      $('#dtid').attr('value', id);
      $('#edit-id').attr('value', id);
      $('#type').attr('value', type);
      M.updateTextFields();
    });

  }); // end of document ready
})(jQuery); // end of jQuery name space