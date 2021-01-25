(function($){
  $(function(){

    //-------------MATERIALIZE INITIALIZATION FUNCTIONS-------------//
    $(document).ready(function(){

      // Prevent tabs flashing content for a second on document reload
      $('#envelopes, #accounts').removeClass('hide');

      $('.modal').modal({onOpenEnd: $(this).find('.tabs').tabs()});

      $('#transaction-modal').modal({
        onOpenEnd: function () {
          $('#transaction-modal').find('.tabs').tabs();
          var tab_index = M.Tabs.init(document.getElementById('type-tabs')).index;
          if (tab_index == 0) {
            $('#new-expense-form').find('input').first().select();
          } else if (tab_index == 1) {
            $('#new-transfer-form').find('input').first().select();
          } else if (tab_index == 2) {
            $('#new-income-form').find('input').first().select();
          }
        }
      })

      // Initialize sidenav
      $('.sidenav').sidenav({
        onOpenStart: function() {$('.fixed-action-btn').hide()},
        onCloseEnd: function() {$('.fixed-action-btn').show()}
      });

      // Initialize all materialize tabs
      $('.tabs').tabs();

      // Initialize all materializeselects
      $('select').formSelect({dropdownOptions: {container: 'body'}});

      // Initialize all materialize datapickers
      $('.datepicker').datepicker({
        autoClose: true,
        format: 'mm/dd/yyyy',
        defaultDate: new Date(),
        setDefaultDate: true,
        container: 'body'
      });

      // Initialize the editor modal
      $('#editor-modal').modal({
        onCloseEnd: function() {
          // Removes user-added rows in editor when the modal is closed
          $(".new-envelope-row").remove()
        }
      });

      // Initialize FAB
      $('.fixed-action-btn').floatingActionButton({
        direction: 'left',
        hoverEnabled: false
      });

      // Hide/show scheduler div
      $('.scheduler').click(function() {
        if (!$(this).siblings().is(':disabled')) {
          if($(this).siblings().is(':checked')) {
            $(this).parent().parent().parent().parent().siblings('.schedule-content').hide()
          } else {
            $(this).parent().parent().parent().parent().siblings('.schedule-content').show()
          }
        }
      });

      // Initialize toggler for transfer editor
      $('.div-toggle').trigger('change');

      // Initialize materialize tooltips
      $('.tooltipped').tooltip();

      // Editor modal setup
      editor_binds()
      transaction_editor = $("#edit-expense").detach();
      transfer_editor = $("#edit-transfer").detach();
      income_editor = $("#edit-income").detach();
      envelope_fill_editor = $("#edit-envelope-fill").detach();

      // Calculate budget bar color/area etc.
      budget_bars()

      // Initialize the multidelete button
      $('#multi-delete-submit').click(function() {
        $('#multi-delete-form').submit();
      });

      // Loading spinners
      var $loading = $('#loading-div-div').hide();
      $(document)
        .ajaxStart(function () {
          $loading.show();
        })
        .ajaxStop(function () {
          $loading.hide();
        });

      // AJAX request to load envelope transactions
      $(document).on('click', '.envelope-link', function() {
        var url = $(this).data('url');
        var envelope_id = $(this).data("envelope-id");
        current_page = "envelope/".concat(envelope_id);
        $.ajax({
          type: "post",
          url: url,
          data: JSON.stringify({"envelope_id": envelope_id}),
          contentType: 'application/json'
        }).done(function( o ) {
          $('#transactions-bin').replaceWith(o['transactions_html']);
          $('#page-total').text(o['page_total']);
          $('#current-view').text(o['envelope_name']);
        });
      });

      // AJAX request to load account transactions
      $(document).on('click', '.account-link', function() {
        var url = $(this).data('url');
        var account_id = $(this).data("account-id");
        current_page = "account/".concat(account_id);
        $.ajax({
          type: "post",
          url: url,
          data: JSON.stringify({"account_id": account_id}),
          contentType: 'application/json'
        }).done(function( o ) {
          $('#transactions-bin').replaceWith(o['transactions_html']);
          $('#page-total').text(o['page_total']);
          $('#current-view').text(o['account_name']);
          //Show the reconcile balance
          $('.reconcile-row').removeClass('gone');
          $('.transaction-amount').removeClass('valign-wrapper')
          $('.balance-row').addClass('balance-row-adjust');
        });
      });

    }); // end of document ready


    //------------- FUNCTIONAL JS -------------//

    //TRANSACTION TYPES
    const BASIC_TRANSACTION = 0;
    const ENVELOPE_TRANSFER = 1;
    const ACCOUNT_TRANSFER = 2;
    const INCOME = 3;
    const SPLIT_TRANSACTION = 4;
    const ENVELOPE_FILL = 5;

    var transaction_editor;
    var transfer_editor;
    var income_editor;
    var envelope_fill_editor;
    var current_page = "";

    var none_checked = true;
    var delete_target;

    // Establish arrays of envelope blances etc. for envelope filler
    var envelope_fill_balances_array = [];
    var envelope_balances = [];
    var unallocated_balance = parseFloat($('#unallocated-balance').text().replace("$","")).toFixed(2);
    $('#envelopes-bin .scroller').children().each( function() {
      envelope_balances.push(parseFloat($(this).data('envelope-balance').replace("$","")));
    });

    // Formats a number into a string with a $ and - if necessary
    function balance_format(number) {
      if (number < 0) {
        text = '-$' + Math.abs(number).toFixed(2)
      } else {
        text = '$' + number.toFixed(2)
      }
      return text;
    }

    // Adds/removes negative class based on number
    $.fn.negative_check = function(number) {
      if (number < 0) {
        this.addClass('negative');
      } else {
        this.removeClass('negative');
      };
    }

    // Sums a 2 numbers
    function getSum(total, num) {
      return total + num;
    }

    // Calculates/sets color & width of budget bars in envelope pane
    function budget_bars() {
      $('.envelope-row').each(function() {
        balance = parseFloat($(this).parent().data('envelope-balance').replace("$", ""));
        budget = parseFloat($(this).parent().data('envelope-budget').replace("$", ""));
        $budget_measure = $(this).find('.budget-measure');
        percentage = (balance / budget) * 100;
        if (percentage > 100) {
          percentage = 100;
        } else if (percentage < -100) {
          percentage = -100;
        }
        if (percentage >= 0) {
          $budget_measure.width(percentage + '%');
          $budget_measure.css("background-color","#108010");
          $budget_measure.css("float","left");
        } else {
          $budget_measure.width((-1*percentage) + '%');
          $budget_measure.css("background-color","#d50707");
          $budget_measure.css("float","right");
        }
      });
    }

    // Checks for any current envelopes/accounts. If no, adds a message in editor modal
    function editor_row_check() {
      if ( $('#account-editor-bin').children().length == 1 ) {
        $('#account-editor-bin').append("<div class='row collection-item' id='no-accounts'><h5 class='no-margin no-message'>You don't have any accounts yet!</h5></div>")
      };
      if ( $('#envelope-editor-bin').children().length == 1 ) {
        $('#envelope-editor-bin').append("<div class='row collection-item' id='no-envelopes'><h5 class='no-margin no-message'>You don't have any envelopes yet!</h5></div>")
      };
    };

    // Various event binds in the transaction/account/envelope editors
    function editor_binds() {
      editor_row_check()
      // Adds new envelope row on button click and clears temporary no-envelopes message if there is one
      $("#new-envelope-row").click(function() {
        $("#envelope-editor-bin").append('<li class="row edit-envelope-row collection-item flex"><div class="col m1 hide-on-small-only valign-wrapper envelope-icon editor-col"><i class="material-icons">mail_outline</i></div><div class="col s6 m4 envelope-name left-align editor-col input-field"><input required class="validate" type="text" name="new-envelope-name"><span class="helper-text" data-error="Envelope name required"></span></div><div class="col s5 m2 envelope-budget editor-col input-field"><input required class="validate" type="number" step=".01" name="new-envelope-budget" pattern="^[-]?([1-9]{1}[0-9]{0,}(\\.[0-9]{0,2})?|0(\\.[0-9]{0,2})?|\\.[0-9]{1,2})$"><span class="helper-text" data-error="Must be numeric"></span></div><div class="col m3 hide-on-small-only valign-wrapper envelope-balance editor-col"><span class="balance neutral">$0.00</span></div><div class="col s1 m2 valign-wrapper delete-envelope editor-col"><a href="#!" class="delete-envelope-button"><i class="material-icons red-text">delete_forever</i></a></div></li>');
        $('#no-envelopes').remove();
      });

      // Adds new account row on button click and clears temporary no-accounts message if there is one
      $("#new-account-row").click(function() {
        $("#account-editor-bin").append('<li class="row account-row collection-item flex"><div class="col m1 hide-on-small-only valign-wrapper account-icon editor-col"><i class="material-icons">account_balance</i></div><div class="col s7 m6 account-name left-align editor-col input-field"><input required class="validate" type="text" name="new-account-name"><span class="helper-text" data-error="Account name required"></span></div><div class="col s4 m3 account-balance editor-col input-field"><input required class="validate" type="number" step=".01" name="new-account-balance" pattern="^[-]?([1-9]{1}[0-9]{0,}(\\.[0-9]{0,2})?|0(\\.[0-9]{0,2})?|\\.[0-9]{1,2})$"><span class="helper-text" data-error="Must be numeric"></span></div><div class="col s1 m2 valign-wrapper delete-account editor-col"><a href="#!" class="delete-account-button"><i class="material-icons red-text">delete_forever</i></a></div></li>');
        $('#no-accounts').remove();
      });

      // Opens delete warning modal when the envelope delete button is clicked
      $("#envelope-editor-bin").on("click", ".delete-envelope-button", function() {
        delete_target = $(this);
        $('#delete-modal p').replaceWith('<p>This action cannot be undone. The balance of this envelope will be added to your unallocated balance.</p>');
        $('#delete-modal').modal('open');
      });

      // Opens delete warning modal when the account delete button is clicked
      $("#account-editor-bin").on("click", ".delete-account-button", function() {
        delete_target = $(this);
        $('#delete-modal p').replaceWith('<p>This action cannot be undone. The balance of this account will be subtracted from your unallocated balance.</p>');
        $('#delete-modal').modal('open');
      });

      //COLLECTS DATA from account/envelope editor modals and submits it to flask
      $('#account-editor-form, #envelope-editor-form').submit(function(e) {
        e.preventDefault()
        var url = $(this).attr('action');
        var method = $(this).attr('method');
        $(".modal").modal("close")

        $.ajax({
          type: method,
          url: url,
          data: $(this).serialize(),
        }).done(function( o ) {
          data_reload(current_page);
          M.toast({html: o})
        });
      });

    }; //End of editor bind

    // Toggler code for transfer tab of transaction creator/editor
    $(document).on('change', '.div-toggle', function() {
      var target = $(this).data('target');
      var show = $("option:selected", this).data('show');
      $(target).children().addClass('hide');
      $(show).removeClass('hide');
      $(target).find('select').removeAttr('required');
      $(show).find('select').attr('required', true);
    });

    // Envelope filler math n' stuff
    $('#envelope-fill-form').on("change", 'input[name="fill-amount"]', function() {
      var $span = $(this).parent().siblings(".envelope-balance").children()
      var index = $(this).parent().parent().index() - 1
      var total_fill = 0;
      var old_balance = envelope_balances[index];
      if ($(this).is(':valid')) {
        new_balance = Math.round((old_balance + parseFloat($(this).val()))*100) / 100;
      } else {
        new_balance = old_balance;
      }
      $span.text(balance_format(new_balance)).negative_check(new_balance);
      $('#envelope-fill-form .envelope-budget input').each(function() {
        if (!isNaN(parseFloat($(this).val()))) {
          total_fill = total_fill + parseFloat($(this).val());
        }
      });
      $('#fill-total').text(balance_format(total_fill)).negative_check(total_fill);
      var new_unallocated_balance = unallocated_balance - total_fill;
      $('#unallocated-balance-envelope-filler').text(balance_format(new_unallocated_balance)).negative_check(new_unallocated_balance);
    });

    // Envelope fill editor math n' stuff
    $('#edit-envelope-fill-form').on("change", 'input[name="fill-amount"]', function() {
      var $span = $(this).parent().siblings(".envelope-balance").children()
      var index = $(this).parent().parent().index() - 1
      var total_fill = 0;
      var old_balance = envelope_balances[index];
      if ($(this).is(':valid')) {
        new_balance = Math.round((old_balance + (parseFloat($(this).val()))-envelope_fill_balances_array[index])*100) / 100;
      } else {
        new_balance = old_balance;
      }
      $span.text(balance_format(new_balance)).negative_check(new_balance)
      $('#edit-envelope-fill-form .envelope-budget input').each(function() {
        if (!isNaN(parseFloat($(this).val()))) {
          total_fill = total_fill + parseFloat($(this).val());
        }
      });
      var original_fill = envelope_fill_balances_array.reduce(getSum)
      $('#edit-fill-total').text(balance_format(total_fill)).negative_check(total_fill);
      var new_unallocated_balance = unallocated_balance - (total_fill - original_fill)
      $('#edit-unallocated-balance-envelope-filler').text(balance_format(new_unallocated_balance)).negative_check(new_unallocated_balance);
    });

    // If the yes button is clicked in the delete modal, delete the appropriate row
    $('#yes').click(function() {
      delete_target.closest('.collection-item').remove();
      editor_row_check()
    });

    // Adds envelope row for transaction creator and initializes Material Select
    $("#add-envelope").click(function() {
      var $envelope_selector = $('#envelope-selector-row').find('select[name="envelope_id"]').clone();
      $('#envelopes-and-amounts').append('<div class="row new-envelope-row flex"><div class="input-field col s6 addedEnvelope"><label>Envelope</label></div><div class="input-field col s5 input-field"><input id="amount" required class="validate" type="number" step=".01" name="amount" pattern="^[-]?([1-9]{1}[0-9]{0,}(\\.[0-9]{0,2})?|0(\\.[0-9]{0,2})?|\\.[0-9]{1,2})$"><label for="amount-">Amount</label><span class="helper-text" data-error="Please enter a numeric value"></span></div><div class="col s1 valign-wrapper remove-envelope-button-col"><a href="#!" class="remove-envelope-button"><i class="material-icons grey-text">delete</i></a></div></div>');
      $(".addedEnvelope").last().prepend($envelope_selector).find("select").last().formSelect({dropdownOptions: {container: 'body'}});
    });

    // Adds envelope row for transaction editor and initializes Material Select
    $("#edit-add-envelope").click(function() {
      var $envelope_selector = $('#edit-envelope-selector-row').find('select[name="envelope_id"]').clone();
      $('#edit-envelopes-and-amounts').append('<div class="row new-envelope-row flex"><div class="input-field col s6 addedEnvelope"><label>Envelope</label></div><div class="input-field col s5 input-field"><input id="amount" required class="validate" type="number" step=".01" name="amount" pattern="^[-]?([1-9]{1}[0-9]{0,}(\\.[0-9]{0,2})?|0(\\.[0-9]{0,2})?|\\.[0-9]{1,2})$"><label for="amount">Amount</label><span class="helper-text" data-error="Please enter a numeric value"></span></div><div class="col s1 valign-wrapper remove-envelope-button-col"><a href="#!" class="remove-envelope-button"><i class="material-icons grey-text">delete</i></a></div></div>');
      $(".addedEnvelope").last().prepend($envelope_selector).find("select").last().formSelect({dropdownOptions: {container: 'body'}});
    });

    // Removes new envelope row in transaction builder
    $("#envelopes-and-amounts, #edit-envelopes-and-amounts").on('click','.remove-envelope-button', function() {
      $(this).closest('.new-envelope-row').remove()
    });

    // Load more transactions button
    $('#bin').on('click', '#load-more', function() {
      $.ajax({
        type: 'POST',
        url: '/api/load-more',
        data: JSON.stringify({"offset": parseInt($(this).attr('data-offset')), "current_page": current_page}),
        contentType: 'application/json'
      }).done(function( o ) {
        $('#load-more').before(o['transactions'])
        if (o['limit']) {
          $('#load-more').remove()
        } else {
          $('#load-more').attr('data-offset', o['offset'])
        }

        //If loading more transactions on the accounts page, show the reconcile balances
        if (current_page.includes("account")) {
          //Show the reconcile balance
          $('.reconcile-row').removeClass('gone');
          $('.transaction-amount').removeClass('valign-wrapper')
          $('.balance-row').addClass('balance-row-adjust');
        }
      });
    });

    // MULTIDELETE CODE
    $('#bin').on('mouseenter', '.transaction-date', function() {
      if (none_checked) {
        $(this).find('.date-bucket').hide();
        $(this).find('.checkbox-bucket').show();
      }
    });

    $('#bin').on('mouseleave', '.transaction-date', function() {
      if (none_checked) {
        $(".date-bucket").show();
        $(this).find('.checkbox-bucket').hide();
      }
    });

    $('#bin').on('click', '.delete-boxes', function() {
      none_checked = true;
      $('.delete-boxes').each(function() {
        if (this.checked) {
          none_checked = false;
        }
      });
      if (this.checked) {
        $(this).closest('.collection-item').addClass('checked-background');
      } else {
        $(this).closest('.collection-item').removeClass('checked-background');
      }
      if (none_checked) {
        $('.checkbox-bucket, #multi-delete-submit').hide();
        $('.date-bucket').show();
      } else {
        $('.checkbox-bucket, #multi-delete-submit').show();
        $('.date-bucket').hide();
      }
    });

    var longpress = 800;
    var start;
    var timer;
    $('#bin').on( 'touchstart', '.transaction', function( e ) {
      $this = $(this);
      start = new Date().getTime();
      start_y = event.touches[0].clientY;
      y = start_y;
      timer = setTimeout(function(){
        if (Math.abs(start_y - y) < 30) {
          $this.parent().find('.delete-boxes').click();
          $(this).bind("contextmenu", function(e) {
            e.preventDefault();
          });
        } else {
          clearTimeout(timer);
        }
      }, longpress)
    }).on( 'mouseleave', '.transaction', function( e ) {
      start = 0;
      clearTimeout(timer);
    }).on( 'touchend', '.transaction', function( e ) {
      if ( new Date().getTime() < ( start + longpress ) && Math.abs(start_y - y) < 30 ) {
        $this = $(this)
        clearTimeout(timer);
        if (!none_checked) {
          e.preventDefault();
          $this.siblings().find('.delete-boxes').click()
        }
      } else {
        start = 0;
        clearTimeout(timer);
      }
    }).on( 'touchmove', '.transaction', function() {
      y = event.touches[0].clientY;
    }).on( 'click', '.transaction', function() {
      $this = $(this)
      t_editor_modal_open($this);
      $('#editor-modal').modal('open');
    }); //END OF MULTIDELETE CODE

    // Sends date from datepicker and frequency from select to schedule_toggle()
    $(document).on('change', '.schedule-select', function() {
      schedule_toggle($(this))
    }).on('change', '.datepicker', function() {
      //CLEAN THIS UP
      $schedule_select = $(this).parent().parent().parent().find('.schedule-select');
      schedule_toggle($schedule_select)
    });

    // Sets the example schedule text based on selected date
    function schedule_toggle(e) {
      const months = ["Jan", "Feb", "Mar","Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      const weekday = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
      var nextdate;
      var nextmonth;
      var nextyear;
      var getDaysInMonth = function(month,year) {
        return new Date(year, month+1, 0).getDate();
      };
      var option = e.val()
      $message = e.parent().parent().siblings().children();
      var date_string = e.parent().parent().parent().siblings().find('.datepicker').val();
      var date = new Date(date_string);
      for (i = 0; i < 2; i++) {
        if (option == 'daily') {
          nextdate = date.getDate() + 1;
          date.setDate(nextdate);
        } else if (option == 'weekly') {
          nextdate = date.getDate() + 7;
          date.setDate(nextdate);
        } else if (option == 'biweekly') {
          nextdate = date.getDate() + 14;
          date.setDate(nextdate);
        } else if (option == 'monthly') {
          nextmonth = date.getMonth() + 1;
          // special case for if nextmonth has less days than current month
          if (date.getDate() > getDaysInMonth(nextmonth,date.getFullYear())) {
            date.setDate(getDaysInMonth(nextmonth,date.getFullYear()))
            date.setMonth(nextmonth)
          } else {
            date.setMonth(nextmonth)
          }
        } else if (option == 'endofmonth') {
          if (date.getDate() == getDaysInMonth(date.getMonth(),date.getYear())) {
            // if current date is already the last day in the month, add another month
            date = new Date(date.getFullYear(), date.getMonth() + 2, 0)
          } else {
            date = new Date(date.getFullYear(), date.getMonth() + 1, 0);
          }
        } else if (option == 'semianually') {
          nextmonth = date.getMonth() + 6;
          // special case for if nextmonth has less days than current month
          if (date.getDate() > getDaysInMonth(nextmonth,date.getFullYear())) {
            date.setDate(getDaysInMonth(nextmonth,date.getFullYear()))
            date.setMonth(nextmonth)
          } else {
            date.setMonth(nextmonth)
          }
        } else if (option == 'anually') {
          nextyear = date.getFullYear() + 1;
          // special case for if nextmonth has less days than current month
          // *only occurs if scheduled on Feb 29th of a leap year*
          if (date.getDate() > getDaysInMonth(date.getMonth(),nextyear)) {
            date.setDate(getDaysInMonth(date.getMonth(),nextyear))
            date.setYear(nextyear)
          } else {
            date.setYear(nextyear)
          }
        };
        if (i == 0) {
          var nextdate_string1 = months[date.getMonth()] + " " + date.getDate() + ', ' + date.getFullYear();
        } else {
          var nextdate_string2 = months[date.getMonth()] + " " + date.getDate() + ', ' + date.getFullYear();
        }
      };
      $message.html("Scheduled for: " + nextdate_string1 + ", " + nextdate_string2 + ", etc...");
    };

    // ----------------- FORM SUBMISSION/FILLING JS ------------------- //


    // Retrieves updated data from database and updates the necessary html
    function data_reload(current_page) {
      $.ajax({
        type: "POST",
        url: "/api/data-reload",
        data: JSON.stringify({"current_page": current_page}),
        contentType: 'application/json'
      }).done(function( o ) {
        $('#load-more').remove()
        $('#transactions-bin').replaceWith(o['transactions_html']);
        $('#accounts-bin').replaceWith(o['accounts_html']);
        $('#envelopes-bin').replaceWith(o['envelopes_html']);

        //Update selects in transaction editor
        transaction_editor.appendTo('#editor-row');
        $('.select-wrapper:has(.account-selector) select').html(o['account_selector_html']);
        $('.select-wrapper:has(.envelope-selector) select').html(o['envelope_selector_html']);
        $('select').formSelect({dropdownOptions: {container: 'body'}});
        transaction_editor.detach();

        //Update selects in transfer editor
        transfer_editor.appendTo('#editor-row');
        $('.select-wrapper:has(.account-selector) select').html(o['account_selector_html']);
        $('.select-wrapper:has(.envelope-selector) select').html(o['envelope_selector_html']);
        $('#envelope-transfer-edit select').first().attr('name', 'from_envelope');
        $('#envelope-transfer-edit select').last().attr('name', 'to_envelope');
        $('#account-transfer-edit select').first().attr('name', 'from_account');
        $('#account-transfer-edit select').last().attr('name', 'to_account');
        $('select').formSelect({dropdownOptions: {container: 'body'}});
        transfer_editor.detach();

        //Update selects in the income editor
        income_editor.appendTo('#editor-row');
        $('.select-wrapper:has(.account-selector) select').html(o['account_selector_html']);
        $('.select-wrapper:has(.envelope-selector) select').html(o['envelope_selector_html']);
        $('select').formSelect({dropdownOptions: {container: 'body'}});
        income_editor.detach()

        $('#envelope-modal').replaceWith(o['envelope_editor_html']);
        $('#account-modal').replaceWith(o['account_editor_html']);
        $('#envelope-modal, #account-modal').modal();
        $('.datepicker').datepicker('setDate', new Date());
        $('input[name="date"]').val((new Date()).toLocaleDateString("en-US", {day: '2-digit', month: '2-digit', year: 'numeric'}));
        $('#total span').text(o['total']);
        if (o['total'][0] == '-') {
          $('#total span').addClass('negative');
        } else {
          $('#total span').removeClass('negative');
        };
        $('#unallocated span, #unallocated-balance-envelope-filler').text(o['unallocated']);
        if (o['unallocated'][0] == '-') {
          $('#unallocated span, #unallocated-balance-envelope-filler').addClass('negative');
        } else {
          $('#unallocated span, #unallocated-balance-envelope-filler').removeClass('negative');
        };

        envelope_fill_editor.appendTo('#editor-row'); //Has to be added back to DOM before replacing HTML
        $('.envelope-fill-editor-bin').replaceWith(o['envelope_fill_editor_rows_html']);
        $('#fill-total').text("$0.00").removeClass("negative")

        editor_binds()

        unallocated_balance = parseFloat($('#unallocated-balance').text().replace("$","")).toFixed(2);
        envelope_balances = []
        $('#envelopes-bin .scroller').children().each( function() {
          envelope_balances.push(parseFloat($(this).data('envelope-balance').replace("$","")));
        });
        envelope_fill_balances_array = [];

        budget_bars()
        none_checked = true

        // Hides scheduled tabs in modals and resets the message value
        $('.schedule-content').hide();
        $('.schedule-select').each(function() { schedule_toggle($(this)) });

        M.updateTextFields();
        $('select').formSelect({dropdownOptions: {container: 'body'}});
        $('#page-total').text(o['page_total'])

        //If you are on the accounts page, show the reconcile balances
        ////THIS MIGHT NOT BE NECSSARY HERE BUT IT WAS ADDED IN CAUTION. TEST THIS
        if (current_page.includes("account")) {
          //Show the reconcile balance
          $('.reconcile-row').removeClass('gone');
          $('.transaction-amount').removeClass('valign-wrapper')
          $('.balance-row').addClass('balance-row-adjust');
        }

        console.log("Page data reloaded!")
      });
    };

    // Submits form data, closes the modal, clears the form, and reloads the data
    $('#transaction-modal form, #edit-expense-form, #edit-transfer-form, #edit-income-form, #envelope-fill-form, #edit-envelope-fill-form').submit(function(e) {
      e.preventDefault()
      var url = $(this).attr('action');
      var method = $(this).attr('method');
      var id = '#' + $(this).attr('id');

      $.ajax({
        type: method,
        url: url,
        data: $(this).serialize(),
      }).done(function( o ) {
        $('.modal').modal("close")
        //Removes the new-envelope-row(s) from split transactions in the specific form so that the next time you open
        //the editor modal, they're not still there, while keeping the new-envelope-rows in the transaction creator modal
        $(id + ' .new-envelope-row').remove() //Only used on #new-expense-form
        $(id)[0].reset();
        data_reload(current_page);
        M.toast({html: o['message']})
        if (o['sched_t_submitted'] == true) { // If the returned schedule message exists, toast it
          M.toast({html: o['sched_message']})
        }
      });
    });

    // Sends delete ID(s) via form, then reloads data
    $('.deleter-form, #multi-delete-form').submit(function(e) {
      e.preventDefault()
      var url = $(this).attr('action');
      var method = $(this).attr('method');
      var parent_modal_id = '#' + $(this).parents('.modal').attr('id');

      $.ajax({
        type: method,
        url: url,
        data: $(this).serialize(),
      }).done(function( o ) {
        $(".modal").modal("close");
        //Removes the new-envelope-row(s) from split transactions in the specific modal so that the next time you open
        //the editor modal, they're not still there, while keeping the new-envelope-rows in the transaction creator modal
        $(parent_modal_id + ' .new-envelope-row').remove();
        data_reload(current_page);
        M.toast({html: o})
      });
    });

    // Opens transaction editor modal
    function t_editor_modal_open(e) {
      // gets and formats data from html data tags
      var id = e.data('id');
      var name = e.data('name');
      var type = e.data('type');
      var date = e.data('date');
      var envelope_name = e.data('envelope_name');
      var envelope_id = e.data('envelope_id');
      var account_name = e.data('account_name');
      var account_id = e.data('account_id');
      var grouping = e.data('grouping');
      var note = e.data('note');
      var amt = -1 * parseFloat(e.data('amt').replace("$",""));
      var to_envelope = null;
      var from_envelope = null;
      var schedule = e.data('schedule');
      var status = e.data('status');
      var checkbox_id;

      //if it's a grouped transaction, use ajax to get data from all grouped transaction
      if (grouping != null) {
        $.ajax({
          async: false,
          type: "GET",
          url: "/api/transaction/" + id + "/group",
        }).done(function( o ) {
          var t_data = o["transactions"];

          // depending on the type, get/format different transaction data
          if (type == ENVELOPE_TRANSFER) {
            var t1 = t_data[0];
            var t2 = t_data[1];
            if (t1["amt"] > 0) {
              to_envelope = t2["envelope_id"];
              from_envelope = t1["envelope_id"];
            } else {
              to_envelope = t1["envelope_id"];
              from_envelope = t2["envelope_id"];
            }
          } else if (type == ACCOUNT_TRANSFER) {
            var t1 = t_data[0];
            var t2 = t_data[1];
            if (t1["amt"] > 0) {
              to_account = t2["account_id"];
              from_account = t1["account_id"];
            } else {
              to_account = t1["account_id"];
              from_account = t2["account_id"];
            }
          } else if (type == SPLIT_TRANSACTION) {
            envelope_ids = [];
            amounts = [];
            $.each(t_data, function(key, t) {
                envelope_ids.push(t['envelope_id']);
                amounts.push(t['amt']);
            });
            amt = amounts[0];
            envelope_id = envelope_ids[0];
          } else if (type == ENVELOPE_FILL) {
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

      // Check which editor to show, detatch the others, update the special fields, and define checkbox_id
      if (type == BASIC_TRANSACTION) {
        transaction_editor.appendTo('#editor-row');
        $("#edit-transfer").detach();
        $("#edit-income").detach();
        $("#edit-envelope-fill").detach();
        checkbox_id = '#edit-expense-schedule';
      } else if (type == ENVELOPE_TRANSFER || type == ACCOUNT_TRANSFER) {
        transfer_editor.appendTo('#editor-row');
        $("#edit-expense").detach();
        $("#edit-income").detach();
        $("#edit-envelope-fill").detach();
        // FIll in the amount field
        $('#edit-transfer_type').val(type).formSelect({dropdownOptions: {container: 'body'}});
        amt = Math.abs(amt);
        if (type == ENVELOPE_TRANSFER) {
          $('#account-transfer-edit').addClass('hide');
          $('#envelope-transfer-edit').removeClass('hide');
          $('#account-transfer-edit').find('select').removeAttr('required');
          $('#envelope-transfer-edit').find('select').attr('required', true);
          $('#edit-from_envelope').val(from_envelope).formSelect({dropdownOptions: {container: 'body'}});
          $('#edit-to_envelope').val(to_envelope).formSelect({dropdownOptions: {container: 'body'}});
        } else if (type == ACCOUNT_TRANSFER) {
          $('#envelope-transfer-edit').addClass('hide');
          $('#account-transfer-edit').removeClass('hide');
          $('#envelope-transfer-edit').find('select').removeAttr('required');
          $('#account-transfer-edit').find('select').attr('required', true);
          $('#edit-to_account').val(to_account).formSelect({dropdownOptions: {container: 'body'}});
          $('#edit-from_account').val(from_account).formSelect({dropdownOptions: {container: 'body'}});
        }
        checkbox_id = '#edit-transfer-schedule'
      } else if (type == INCOME) {
        income_editor.appendTo('#editor-row');
        $("#edit-expense").detach();
        $("#edit-transfer").detach();
        $("#edit-envelope-fill").detach();
        amt = amt * -1;
        checkbox_id = '#edit-income-schedule'
      } else if (type == SPLIT_TRANSACTION) {
        transaction_editor.appendTo('#editor-row');
        $("#edit-transfer").detach();
        $("#edit-income").detach();
        $("#edit-envelope-fill").detach();
        for (i=1 ; i<envelope_ids.length ; i++) {
          var $envelope_selector = $('#edit-envelope-selector-row').find('select[name="envelope_id"]').clone();
          $('#edit-envelopes-and-amounts').append('<div class="row new-envelope-row flex"><div class="input-field col s6 addedEnvelope"><label>Envelope</label></div><div class="input-field col s5 input-field"><input required id="amount" class="validate" type="number" step=".01" name="amount" value="'+amounts[i].toFixed(2)+'" pattern="^[-]?([1-9]{1}[0-9]{0,}(\\.[0-9]{0,2})?|0(\\.[0-9]{0,2})?|\\.[0-9]{1,2})$"><label for="amount">Amount</label><span class="helper-text" data-error="Please enter a numeric value"></span></div><div class="col s1 valign-wrapper remove-envelope-button-col"><a href="#!" class="remove-envelope-button"><i class="material-icons grey-text">delete</i></a></div></div>');
          $(".addedEnvelope").last().prepend($envelope_selector).find("select").last().val(envelope_ids[i]).formSelect({dropdownOptions: {container: 'body'}});
        }
        checkbox_id = '#edit-expense-schedule'
      } else if (type == ENVELOPE_FILL) {
        envelope_fill_editor.appendTo('#editor-row');
        $("#edit-transfer").detach();
        $("#edit-income").detach();
        $("#edit-expense").detach();
        // Fills input fields
        var $inputs = $('#edit-envelope-fill-form .envelope-fill-editor-bin :input[type=number]');
        envelope_fill_balances_array = [];
        $inputs.each(function(index) {
          // this code exists so that if you change a value, close the editor,
          // then reopen it, the envelope balances will always be correct
          var $span = $(this).parent().siblings(".envelope-balance").children();
          $span.text(balance_format(envelope_balances[index])).negative_check(envelope_balances[index]);
          // Fills input fields and creates envelope_fill_balances_array for data processing
          if (envelope_ids.includes($(this).data("envelope-id"))) {
            $(this).val(amounts[envelope_ids.indexOf($(this).data("envelope-id"))].toFixed(2));
            envelope_fill_balances_array.push(parseFloat(amounts[envelope_ids.indexOf($(this).data("envelope-id"))]));
          } else {
            envelope_fill_balances_array.push(0.00)
          }
        });
        if (envelope_fill_balances_array.length == 0) { //if you've deleted all the envelopes this prevents it from crashing
          envelope_fill_balances_array.push(0.00)
        }
        $('#edit-fill-total').text(balance_format(envelope_fill_balances_array.reduce(getSum))).negative_check(parseFloat(envelope_fill_balances_array.reduce(getSum)));
        $('#edit-unallocated-balance-envelope-filler').text(balance_format(parseFloat(unallocated_balance))).negative_check(unallocated_balance)
        checkbox_id = '#edit-envelope-fill-schedule'
      }

      // update the rest of the common fields
      $("#edit-amount").val(amt.toFixed(2));
      $("#edit-date").val(date).datepicker({
        autoClose: true,
        format: 'mm/dd/yyyy',
        container: 'body'
      });
      $('#edit-date').datepicker('setDate', new Date(date));
      $("#edit-name").val(name);
      $("#edit-note").val(note);
      $('#edit-envelope_id').val(envelope_id).formSelect({dropdownOptions: {container: 'body'}});
      $('#edit-account_id').val(account_id).formSelect({dropdownOptions: {container: 'body'}});
      $('#dtid').attr('value', id);
      $('#edit-id').attr('value', id);
      $('#type').attr('value', type); //Possibly change this to a less confusing ID

      //Logic for whether or not schedule checkbox/info shows or is disabled
      if (schedule == 'None') {
        // set to default (disabled)
        if ($(checkbox_id).is(':checked')) {
          // Uncheck box if it is checked
          $(checkbox_id).siblings().click()
        }
        $(checkbox_id).attr('disabled', 'disabled')
        $(checkbox_id).siblings().addClass('checkbox-disabled')
      } else {
        // Make sure checkbox is not disabled
        $(checkbox_id).removeAttr('disabled')
        $(checkbox_id).siblings().removeClass('checkbox-disabled')
        // update scheduled values and show the section
        $('#edit-schedule').val(schedule).formSelect({dropdownOptions: {container: 'body'}});
        schedule_toggle($('#edit-schedule'));
        $checkbox = ($('#' + $('#edit-schedule').data('checkbox-id')));
        if (!($checkbox.is(':checked'))) {
          $checkbox.siblings().click()
        }
      }
      M.updateTextFields();
    }; // End of t_editor_modal_open

  });
})(jQuery); // end of jQuery name space