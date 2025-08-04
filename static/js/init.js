// This file is used in the layout.html template

(function($){
  $(function(){

    // ----Declare global variables----

    //Static HTML variables
    var new_edit_envelope_row_html;
    var new_edit_account_row_html;
    var t_editor_new_env_row_html;

    const LEFT_ARROW = 37;
    const UP_ARROW = 38;
    const RIGHT_ARROW = 39;
    const DOWN_ARROW = 40;
    const ENTER = 13;
    const ESCAPE = 27;

    //Transaction types
    const BASIC_TRANSACTION = 0;
    const ENVELOPE_TRANSFER = 1;
    const ACCOUNT_TRANSFER = 2;
    const INCOME = 3;
    const SPLIT_TRANSACTION = 4;
    const ENVELOPE_FILL = 5;
    const ENVELOPE_DELETE = 6;
    const ACCOUNT_DELETE = 7;
    const ACCOUNT_ADJUST = 8;

    // Objects for various transaction editors
    var expense_editor;
    var transfer_editor;
    var income_editor;
    var envelope_fill_editor;
    var envelope_restore;
    var account_restore;
    var account_adjust;

    // Some other variables
    var current_page = "All Transactions";   //Used to determine which transactions to reload on a data reload (also used in transactions.html to properly color transaction amount)
    var none_checked = true; // Used to determine whether to show the date or checkbox in the transaction bin


    //-------------MATERIALIZE INITIALIZATION FUNCTIONS-------------//
    $(document).ready(function(){

      //Set up the simplebar scroll bars
      $('.scroller').each(function(index,el) {
        new SimpleBar(el);
      });

      // Prevent content from flashing content for a second on document load
      $('#envelopes, #accounts, #bin').removeClass('hide');
      
      $('#envelope-modal, #account-modal, #editor-modal, #envelope-fill-modal').modal();

      $('#delete-modal').modal({
        dismissible: false,
        onCloseEnd: function() {$("#yes").unbind()}
      })

      $('#transaction-modal').modal({
        onOpenEnd: function () {
          tab_index = $('#type-tabs').tabs().index;
          if (tab_index == 0) {
            $('#new-expense-form input[name="name"]').eq().select();
          } else if (tab_index == 1) {
            $('#new-transfer-form input[name="name"]').eq().select();
          } else if (tab_index == 2) {
            $('#new-income-form input[name="name"]').eq().select();
          }
        },
        onCloseStart: function() {
          $('#transaction-modal .select-dropdown').dropdown('close')
        }
      });

      // Initialize the editor modal
      $('#editor-modal').modal({
        onCloseStart: function() {
          $('#editor-modal').find('.select-dropdown').dropdown('close')
        },
        onCloseEnd: function() {
          // Removes user-added rows in editor when the modal is closed
          $(".new-envelope-row").remove()
        }
      });

      // Makes escape button ONLY close a select located in a modal (but all the select bodies are actually in the fullscreen wrapper)
      $("#fullscreen-wrapper").on("keydown", ".dropdown-content li", function(e) {
        if (e.key == "Escape") e.stopPropagation();
      });

      $('body').keydown(function(e){
        if(e.key == "Escape" && M.Modal._modalsOpen == 0){
          // Clear all transaction selection checkboxes on ESCAPE KEY (if you're not hitting escape to close a modal)
          $('.t-delete-checkbox:checked').click();
          none_checked = true;
        } else if (e.key == "t" && M.Modal._modalsOpen == 0) {
          // TODO: When the searchbar is added, this will probably need to change to be more specific since valid keypresses in the searchbar are not within a modal 
          $("#transaction-modal").modal("open"); 
        } else if (e.key == "e" && M.Modal._modalsOpen == 0) {
          // TODO: When the searchbar is added, this will probably need to change to be more specific since valid keypresses in the searchbar are not within a modal 
          $("#envelope-fill-modal").modal("open");
        }
      });

      $("#multi-select-clear").click(function() {
        // Clear all transaction selection checkboxes
        $('.t-delete-checkbox:checked').click();
        none_checked = true;
      });

      // Initialize sidenav
      $('.sidenav').sidenav({
        onOpenStart: function() {$('.fixed-action-btn').hide()},
        onCloseEnd: function() {$('.fixed-action-btn').show()}
      });

      // Initialize all materialize tabs
      $('.tabs').tabs();

      // Initialize all materializeselects
      $('select').formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});

      // Initialize all materialize datapickers
      $('.datepicker').datepicker({
        autoClose: true,
        format: 'mm/dd/yyyy',
        defaultDate: new Date(),
        setDefaultDate: true,
        container: 'body',
        onClose: function() {
          this.el.focus();
        }
      });

      // Adds arrowkey functionality to datepicker
      $(".datepicker-modal").keydown(function(e) {
        if (e.shiftKey && (e.key == "ArrowLeft")) {
          $(this).find(".month-prev").click();
          $(this).find("table button").last("button").focus();
        }
        else if (e.shiftKey && (e.key == "ArrowRight")) {
          $(this).find(".month-next").click();
          $(this).find("table button").first("button").focus();
        }
        else if (e.key == "ArrowLeft") {
          if (!$(document.activeElement).hasClass("month-prev")) $.tabPrev();
        }
        else if (e.key == "ArrowRight") {
          if (!$(document.activeElement).hasClass("datepicker-done")) $.tabNext();
        }
        else if (e.key == "ArrowDown") {
          var focused = document.activeElement;
          //If the focused element is one of the date buttons
          if ($(focused).hasClass("datepicker-day-button")) {
            //If an element in the last row is focused, focus the "month-next" button
            if ($(this).find(".datepicker-row").last().find(focused).length == 1) {
              $(this).find(".datepicker-cancel").focus();
            }
            // If the element is not in the first row of the table, move to the appropriate element in the previous row
            else {
              var day = parseInt($(focused).data("day"));
              var newDay = day + 7;
              var maxDay = parseInt($(this).find(".datepicker-day-button").last().data("day"));
              if (newDay > maxDay) {
                $(this).find(".datepicker-day-button").last().focus();
              } else {
                $(this).find(".datepicker-day-button[data-day='" + newDay.toString() + "']").focus();
              }
            }
          } else {
            if ($(this).find(".datepicker-controls").find(focused).length == 1) {
              //If a button in the datepicker title row is focused, focus the first day button
              $(this).find(".datepicker-day-button").first().focus();
            }
            else if ($(focused).hasClass("datepicker-cancel")) {
              //If the "cancel" button is focused, move focus to the last day button
              $.tabNext();
            } else if ($(focused).hasClass("datepicker-done")) {
              //If the "OK" button is focused, do nothing
              return;
            }
          }
        }
        else if (e.key == "ArrowUp") {
          var focused = document.activeElement;
          //If the focused element is one of the date buttons
          if ($(focused).hasClass("datepicker-day-button")) {
            //If an element in the first row is focused, focus the "month-next" button
            if ($(this).find(".datepicker-row").first().find(focused).length == 1) {
              $(this).find(".month-next").focus();
            }
            // If the element is not in the first row of the table, move to the appropriate element in the previous row
            else {
              var day = parseInt($(focused).data("day"));
              var newDay = day - 7;
              if (newDay < 1) {
                $(this).find(".datepicker-day-button").first().focus();
              } else {
                $(this).find(".datepicker-day-button[data-day='" + newDay.toString() + "']").focus();
              }
            }
          } else {
            if ($(this).find(".datepicker-controls").find(focused).length == 1) {
              //If a button in the datepicker title row is selected, do nothing
              return;
            }
            else if ($(focused).hasClass("datepicker-cancel")) {
              //If the "cancel" button is focused, move focus to the last day button
              $(this).find("td button").last().focus();
            } else if ($(focused).hasClass("datepicker-done")) {
              //If the "OK" button is focused, move focus to the "cancel" button
              $.tabPrev();
            }
          }
        }
        else if (e.key == "Escape") {
          e.stopPropagation(); // Don't close the parent modal
          $(this).modal("close"); //Only close the datepicker modal
          $(".modal.open").find(".datepicker").focus(); //Refocus the datepicker from the parent modal (this will break if there's ever two datepickers)
          // Also not quite sure why you need to refocus if the datepickers have an onClose() function that should focus it. Might have to do with the stopPropagation
        }
      });

      // When schedule checkbox is focused, open it on ENTER
      $('input[name="scheduled"]').keydown(function(e) {
        if (e.key == "Enter") {
          e.preventDefault();
          $(this).next().click();
        }
      })

      // Initialize FAB
      $('.fixed-action-btn').floatingActionButton({
        direction: 'left',
        hoverEnabled: false
      });

      // Hide/show scheduler div
      $('.scheduler').click(function() {
        if (!$(this).siblings().is(':disabled')) {
          if($(this).siblings().is(':checked')) {
            $(this).closest("form").find('.schedule-content').hide();
          } else {
            $(this).closest("form").find('.schedule-content').show();
          }
        }
      });

      // Initialize toggler for transfer editor
      $('.div-toggle').trigger('change');

      // Initialize materialize tooltips
      $('.tooltipped').tooltip();

      // Editor modal setup
      envelope_and_account_editor_binds();
      editor_row_check(); //If there are no envelopes or accounts, ensure the message shows in the relevant editor
      expense_editor = $("#edit-expense").detach();
      transfer_editor = $("#edit-transfer").detach();
      income_editor = $("#edit-income").detach();
      envelope_fill_editor = $("#edit-envelope-fill").detach();
      envelope_restore = $("#edit-envelope-delete").detach();
      account_restore = $("#edit-account-delete").detach();
      account_adjust = $("#edit-account-adjust").detach()

      // Calculate budget bar color/area etc.
      budget_bars()

      // AJAX request to load all transactions
      $(document).on('click', '#total', function() {
        var url = $(this).data('url');
        current_page = "All Transactions";
        $.ajax({
          type: "post",
          url: url,
          data: JSON.stringify({"timestamp": gen_timestamp()}),
          contentType: 'application/json'
        }).done(function( o ) {
          if (o['error']) { M.toast({html: o['error']}); return; }
          $('#transactions-bin').replaceWith(o['transactions_html']);
          if ($("#transactions-scroller").length !== 0) { new SimpleBar($("#transactions-scroller")[0]) } //Re-initialize the transactions-scroller if the envelope has transactions
          $('#page-total').text(o['page_total']);
          $('#current-view').text(o['page_title']);
          refresh_reconcile()
        });
      });

      // AJAX request to load envelope transactions
      $(document).on('click', '.envelope-link', function() {
        var url = $(this).data('url');
        var envelope_id = $(this).data("envelope-id");
        current_page = "envelope/".concat(envelope_id);
        $.ajax({
          type: "post",
          url: url,
          data: JSON.stringify({"envelope_id": envelope_id, "timestamp": gen_timestamp()}),
          contentType: 'application/json'
        }).done(function( o ) {
          if (o['error']) { M.toast({html: o['error']}); return; }
          $('#transactions-bin').replaceWith(o['transactions_html']);
          if ($("#transactions-scroller").length !== 0) { new SimpleBar($("#transactions-scroller")[0]) } //Re-initialize the transactions-scroller if the envelope has transactions
          $('#page-total').text(o['page_total']);
          $('#current-view').text(o['envelope_name']);
          refresh_reconcile()
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
          data: JSON.stringify({"account_id": account_id, "timestamp": gen_timestamp()}),
          contentType: 'application/json'
        }).done(function( o ) {
          if (o['error']) { M.toast({html: o['error']}); return; }
          $('#transactions-bin').replaceWith(o['transactions_html']);
          if ($("#transactions-scroller").length !== 0) { new SimpleBar($("#transactions-scroller")[0]) } //Re-initialize the transactions-scroller if the account has transactions
          $('#page-total').text(o['page_total']);
          $('#current-view').text(o['account_name']);
          refresh_reconcile()
        });
      });

      // Load the contents of the static HTML files into global variables
      const csrf_token = $("#csrf-token").val();
      $.ajax({
        type: 'POST',
        url: '/api/load-static-html',
        headers: {
          'X-CSRFToken': csrf_token
        }
      }).done( function(o) {
        if (o['error']) { M.toast({html: o['error']}); return; }
        new_edit_envelope_row_html = o['edit_envelope_row'];
        new_edit_account_row_html = o['edit_account_row'];
        t_editor_new_env_row_html = o['t_editor_new_env_row'];
      });

      // Refresh the reconcile balances
      refresh_reconcile();

    $("body").on("input", ".special-input", function() {
      $span =  $(this).parent().siblings(".amount-col").find("span");
      try {
        num = math.evaluate($(this).val());
        if (!isNaN(num)) {
          num = Math.round(num * 100) / 100; //Round to 2 decimal places
          if ($(this).hasClass("negate-input")) {
            num = num * -1;
          }
          $span.text(balance_format(num)).negative_check(num);
          $(this).removeClass("invalid").addClass("valid");
        } else {
          $span.text("$...").removeClass('negative').addClass('neutral');
          $(this).removeClass("valid");
        }
      } catch (error) {
        $span.text("$...").removeClass('negative').addClass('neutral').removeClass("valid");
        $(this).removeClass("valid").addClass("invalid");
      }
    }).on("change",".special-input", function() {
      try {
        num = math.evaluate($(this).val());
        if (!isNaN(num)) {
          num = Math.round(num * 100) / 100; //Round to 2 decimal places
          $(this).val((Math.round(num * 100) / 100).toFixed(2));
        } else {
          $span.text("$...").removeClass('negative').addClass('neutral').removeClass("valid");
          $(this).removeClass("valid");
        }
      } catch (error) {
        return;
      }
    });

    $("#settings, #about").click(function() {
      M.toast({html: "Coming soon!"})
    });

    }); // end of document ready


    //------------- FUNCTIONAL JS -------------//
    function refresh_reconcile() {
      var page_total = text_to_num($("#page-total").text());
      var reconcile_balance = page_total;
      var pending_transactions = [];
      $("#transactions-bin .transaction-row").each(function() {
        if ($(this).hasClass("pending")) {
          //Add any pending transactions to an array to deal with after this loop
          pending_transactions.push($(this));
        } else {
          $balance = $(this).find(".balance");
          $reconcile_span = $(this).find(".reconcile-span");
          var amt = text_to_num($balance.text());
          if ($balance.hasClass("neutral")) {
            $reconcile_span.text(balance_format(reconcile_balance))
          } else {
            $reconcile_span.text(balance_format(reconcile_balance))
            reconcile_balance = reconcile_balance - amt
          }
        }
      });

      // If there are pending transactions, update their reconcile balances in reverse order
      var pending_reconcile_balance = page_total;
      pending_transactions.reverse().forEach(function($transaction_row) {
        $balance = $transaction_row.find(".balance");
        $reconcile_span = $transaction_row.find(".reconcile-span");
        var amt = text_to_num($balance.text());
        if ($balance.hasClass("neutral")) {
          $reconcile_span.text(balance_format(pending_reconcile_balance))
        } else {
          pending_reconcile_balance = pending_reconcile_balance + amt
          $reconcile_span.text(balance_format(pending_reconcile_balance))
        }
      });
      
    }

    // Formats a number into a string with a "$" and "-" if necessary
    function balance_format(number) {
      if (number < 0) {
        text = '-$' + Math.abs(number).toFixed(2)
      } else {
        text = '$' + number.toFixed(2)
      }
      return text;
    }

    function text_to_num(txt) {
      num = parseFloat(txt.replace("$","")) //Remove the "$" character
      return num
    }

    // Adds/removes negative class based on number
    $.fn.negative_check = function(number) {
      if (number < 0) {
        this.addClass('negative');
        this.removeClass('neutral');
      } else if (number == 0) {
        this.removeClass('negative');
        this.addClass('neutral');
      } else {
        this.removeClass('neutral');
        this.removeClass('negative');
      };
    }

    // Calculates/sets color & width of budget bars in envelope pane
    function budget_bars() {
      $('.envelope-row').each(function() {
        balance = parseFloat($(this).parent().data('envelope-balance'));
        budget = parseFloat($(this).parent().data('envelope-budget'));
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
    // This is called upon initialization and re-called on each data_reload
    function envelope_and_account_editor_binds() {

      // Bind for button in the envelope editor modal
      $("#new-envelope-row").click(function() {

        // 1. Determine the new display order for the envelope (defaults to displaying last)
        var e_disp_orders = [];
        $("#envelope-editor-bin").find('input[name="envelope-order"], input[name="new-envelope-order"]').each(function() {
          e_disp_orders.push(parseInt($(this).attr('value')));
        });
        if (e_disp_orders.length == 0) {
          new_e_disp_order = 0;
        } else {
          var new_e_disp_order = Math.max(...e_disp_orders) + 1;
        }

        // 2. Add the new envelope row
        $("#envelope-editor-bin").append(new_edit_envelope_row_html);

        // 3. Update the display order value
        $("#new-envelope-row").find('input[name="new-envelope-order"]').attr("value", new_e_disp_order);
        $("#new-envelope-row").removeAttr("id"); //

        // 4. Clears temporary no-envelopes message if there is one
        $('#no-envelopes').remove(); 
      });

      // Bind for the button in the account editor modal
      $("#new-account-row").click(function() {

        // 1. Determine the new display order for the account (defaults to displaying last)
        var a_disp_orders = [];
        $("#account-editor-bin").find('input[name="account-order"], input[name="new-account-order"]').each(function() {
          a_disp_orders.push(parseInt($(this).attr('value')));
        });
        if (a_disp_orders.length == 0) {
          new_a_disp_order = 0;
        } else {
          var new_a_disp_order = Math.max(...a_disp_orders) + 1;
        }

        // 2. Add the new account row
        $("#account-editor-bin").append(new_edit_account_row_html);

        // 3. Update the display order value
        $("#new-account-row").find('input[name="new-account-order"]').attr("value", new_a_disp_order);
        $("#new-account-row").removeAttr("id"); //

        // 4. Clears temporary no-accounts message if there is one
        $('#no-accounts').remove(); 
      });

      // Makes the envelopes in the envelope editor modal sortable
      $('#envelope-editor-bin').sortable({
        handle: ".sort-icon",
        containment: "parent",
        dropOnEmpty: true,
        start: function(e, ui) {
          $(ui.item).addClass("active-drag");
          // Fix to enable sorting drag for first and last positions
          // https://stackoverflow.com/questions/57733176/first-and-last-sortable-items-dont-consistently-move-out-of-the-way-in-jquery-u
          var sort = $(this).sortable('instance');
          ui.placeholder.height(ui.helper.height());
          sort.containment[3] += ui.helper.height() * 1.5 - sort.offset.click.top;
          sort.containment[1] -= sort.offset.click.top;
        },
        helper: function(e, row) {
            row.children().each(function() {
              $(this).width($(this).width());
            });
            return row;
        },
        stop: function(event, ui) {
          $(ui.item).removeClass("active-drag");
         // JQuery UI will place a fixed "width" style on the columns of the reordered element, which means that resizing
          // the page means columns don't dynamically resize, so this is the fix.
          $(ui.item).removeAttr("style");
          $(ui.item).children().removeAttr("style");
        },
        items: "li:not(.unsortable)"
      });

      // Makes the envelopes in the editor sortable
      $('#transactions-scroller').sortable({
        handle: ".checkbox-special",
        containment: "parent",
        dropOnEmpty: true,
        start: function(e, ui) {
          $(ui.item).addClass("active-drag");
          // Fix to enable sorting drag for first and last positions
          // https://stackoverflow.com/questions/57733176/first-and-last-sortable-items-dont-consistently-move-out-of-the-way-in-jquery-u
          var sort = $(this).sortable('instance');
          ui.placeholder.height(ui.helper.height());
          sort.containment[3] += ui.helper.height() * 1.5 - sort.offset.click.top;
          sort.containment[1] -= sort.offset.click.top;
        },
        helper: function(e, row) {
            row.children().each(function() {
              $(this).width($(this).width());
            });
            return row;
        },
        stop: function(event, ui) {
          $(ui.item).removeClass("active-drag");
          // JQuery UI will place a fixed "width" style on the columns of the reordered element, which means that resizing
          // the page means columns don't dynamically resize, so this is the fix.
          $(ui.item).removeAttr("style");
          $(ui.item).children().removeAttr("style");
        },
          items: "li:not(.unsortable)"
      });

      // Makes the accounts in the editor sortable
      $('#account-editor-bin').sortable({
        handle: ".sort-icon",
        containment: "parent",
        dropOnEmpty: true,
        start: function(e, ui) {
          $(ui.item).addClass("active-drag");
          // Fix to enable sorting drag for first and last positions
          // https://stackoverflow.com/questions/57733176/first-and-last-sortable-items-dont-consistently-move-out-of-the-way-in-jquery-u
          var sort = $(this).sortable('instance');
          ui.placeholder.height(ui.helper.height());
          sort.containment[3] += ui.helper.height() * 1.5 - sort.offset.click.top;
          sort.containment[1] -= sort.offset.click.top;
        },
        helper: function(e, row) {
            row.children().each(function() {
              $(this).width($(this).width());
            });
            return row;
        },
        stop: function(event, ui) {
          $(ui.item).removeClass("active-drag");
          // JQuery UI will place a fixed "width" style on the columns of the reordered element, which means that resizing
          // the page means columns don't dynamically resize, so this is the fix.
          $(ui.item).removeAttr("style");
          $(ui.item).children().removeAttr("style");
        },
        items: "li:not(.unsortable)"
      });

      // Opens delete warning modal when the envelope delete button in the envelope editor modal is clicked
      $("#envelope-editor-bin").on("click", ".delete-envelope-button", function() {
        var msg = "The balance of this envelope will be added to your unallocated balance."
        $this = $(this);
        deleteModal(msg, function() {
          $this.closest('.collection-item').remove();
          editor_row_check();
          $("#yes").unbind("click"); // ALWAYS discard the click event applied by the deleteModal() function
        });
      });

      // Opens delete warning modal when the account delete button in the account editor modal is clicked
      $("#account-editor-bin").on("click", ".delete-account-button", function() {
        var msg = "The balance of this account will be subtracted from your unallocated balance."
        $this = $(this);
        deleteModal(msg, function() {
          $this.closest('.collection-item').remove();
          editor_row_check();
          $("#yes").unbind("click"); // ALWAYS discard the click event applied by the deleteModal() function
        });
      });

      //Collects data from account/envelope editor modals and submits it to flask
      $('#account-editor-form, #envelope-editor-form').submit(function(e) {
        e.preventDefault();
        var url = $(this).attr('action');
        var method = $(this).attr('method');

        // Update the account-order input values to reflect new order
        if ($(this).attr('id') == 'account-editor-form') {
          var i = 0;
          $("#account-editor-bin").find('input[name="account-order"], input[name="new-account-order"]').each(function() {
            $(this).attr("value", i);
            i++;
          })
        }
        // Update the envelope-order input values to reflect new order
        if ($(this).attr('id') == 'envelope-editor-form') {
          var i = 0;
          $("#envelope-editor-bin").find('input[name="envelope-order"], input[name="new-envelope-order"]').each(function() {
            $(this).attr("value", i);
            i++;
          })
        }
        
        $(".modal").modal("close");

        $.ajax({
          type: method,
          url: url,
          data: $(this).serialize() + "&timestamp=" + gen_timestamp() //Append a timestamp to the serialized form data
        }).done(function( o ) {
          if (o['error']) { M.toast({html: o['error']}); return; }
          data_reload(current_page);
          o['toasts'].forEach((toast) => M.toast({html: toast})); //Display toasts
        });
      });

      // Envelope budget math n' stuff
      $('#envelope-editor-form').on("input", '.special-input-envelope-editor', function() {
        var index = $(this).parent().parent().index()-1; //The index of the envelope you are filling
        var skip;

        // 1. Attempt to evaluate the expression in the input and update the envelope total span accordingly
        try {
          num = Math.round(math.evaluate($(this).val())*100)/100;
          if (!isNaN(num)) {
            $(this).removeClass("invalid").addClass("valid");
            skip = false; //Include this number when calculating the budget total
          } else {
            $(this).removeClass("valid").removeClass("invalid");
            skip = true; // DO NOT include this number when calculating the fill total
          }
        } catch (error) {
          $(this).removeClass("valid").addClass("invalid");
          skip = true; // DO NOT include this number when calculating the fill total
        }

        // 2. Iterate over the input fields to calculate the fill total
        var budget_total = 0;
        $('#envelope-editor-form .special-input-envelope-editor').each(function(i) {
          if (i == index) { //If parsing the input that you are currently focused on
            if (!skip) {
              budget_total = budget_total +  num; //Add the result of the parsed expression in the input to the budget total
            }
          } else {
            if (!isNaN(parseFloat($(this).val()))) { //If the input is not empty
              budget_total = budget_total + parseFloat($(this).val()); //Add the value of the input field to the budget total
            }
          }
        });

        // 3. Update the budget total span
        $('#budget-total').text(balance_format(budget_total))
      }).on("change", ".special-input-envelope-editor", function() {
        try {
          num = math.evaluate($(this).val());
          if (!isNaN(num)) {
            $(this).val((Math.round(num * 100) / 100).toFixed(2)); //Replace the input text with the result of the parsed expression
          }
        } catch (error) {
          return;
        }
      });

      $('#account-editor-form').on('change', '.special-input-account-editor', function() {
        try {
          num = math.evaluate($(this).val());
          if (!isNaN(num)) {
            $(this).val((Math.round(num * 100) / 100).toFixed(2)); //Replace the input text with the result of the parsed expression
          }
        } catch (error) {
          return;
        }
      });

    }; //End of editor bind

    // If the "yes" button is clicked in the delete modal, execute the confirmFunction
    function deleteModal(msg, confirmFunction) {
      $('#delete-modal p').replaceWith('<p>' + msg + '</p>');
      $('#delete-modal').modal('open');
      $('#yes').click(confirmFunction);
    }

    // Hide/show the transaction checkbox or date AND hide/show the multidelete buttons
    function multideleteToggleCheck() {
      none_checked = true;
      $('.t-delete-checkbox').each(function() {
        if (this.checked) none_checked = false;
      });
      if (none_checked) {
        $('.checkbox-bucket, #multi-select-col').hide();
        $('.date-bucket').show();
      } else {
        $('.checkbox-bucket, #multi-select-col').show();
        $('.date-bucket').hide();
      }
    }

    // Check/uncheck a transaction checkbox and highlihght the .transaction-row background accordingly
    $.fn.setCheckbox = function(checked) {
      if (checked) {
        $(this).prop("checked", true);
        $(this).closest('.transaction-row').addClass('checked-background');
      } else {
        $(this).prop("checked", false);
        $(this).closest('.transaction-row').removeClass('checked-background');
      }
    }

    // Initialize the multidelete button to open the confirmation modal, then submit the form
    $('#multi-delete-submit').click(function() {
      var msg = "Once these transactions are deleted, they're gone forever!"
      deleteModal(msg, function() {
        $('#multi-delete-form').submit();
      })
    });

    // When clicking on a transaction, open the transaction editor modal
    // When hovering over the date, show the multidelete buttons
    var lastChecked = null; // Used for shift selection
    $('#bin').on('click', '.transaction', function(e) {
      t_editor_modal_open($(this));
    }).on('mouseenter', '.transaction-date', function() {
      if (none_checked) {
        $(this).find('.date-bucket').hide();
        $(this).find('.checkbox-bucket').show();
      }
    }).on('mouseleave', '.transaction-date', function() {
      if (none_checked) {
        $(".date-bucket").show();
        $(this).find('.checkbox-bucket').hide();
      }
    }).on("click", ".t-delete-checkbox", function(e) {
      var $checkboxes = $(".t-delete-checkbox");
      var $checkboxes_toupdate = null;
      // 1. Determine the last checkbox which was checked
      if (!lastChecked) {
          lastChecked = this;
      }

      // 2. Determine which checkboxes to update
      if (e.shiftKey) {
        var start = $checkboxes.index(this);
        var end = $checkboxes.index(lastChecked);
        $checkboxes_toupdate = $checkboxes.slice(Math.min(start,end), Math.max(start,end)+1);
      } else {
        $checkboxes_toupdate = $(this);
        lastChecked = this;
      }

      // 3. Update the checkboxes
      $checkboxes_toupdate.setCheckbox(lastChecked.checked);

      // 4. Hide or show the multidelete buttons and checkboxes as needed
      multideleteToggleCheck();
    });


    // ----- Code for touch-selecting transactions -----
    var start_time; // System time in ms when a touchevent starts
    var longPressTimer; // Timer for determining if a touchevent is a longpress
    var longpressAmt = 400; // Duration in ms for a touchevent to be considered a longpress
    var isDragSelecting = false; // Is the user selecting transactions by dragging during a longpress (synonomous with isLongPressing)
    var isDragSelectScrolling = false; // Is the screen programatically scrolling during a drag selection (i.e.when your finger is near the top or bottom of the scroller area)
    var isSwipeScrolling; // Is the user swiping the screen to scroll through transactions (not during a longpress when they are drag selecting)
    var $scroller; // JQuery object of the transactions scroller
    var $allTRows; // JQuery object of all .transaction-row elements
    var $allCheckboxes; // JQuery object of all .t-delete-checkbox elements
    var originalStates = null; // Stores the original checked state of the checkboxes
    var initialTargetIsChecked = null; // Used for drag selection, stores the initial state of the checkbox for the first transaction you longpressed
    var startingTargetIndex = null; // Used for drag selection, stores the index of the first transaction you longpressed
    var lastChangedTargetIndex = null; // Used for drag selection, stores the index of the last transaction whose state was changed (prevents skipping transactions on quick drags)
    var intTopHandler = null; // Timer used for drag select scrolling
    var intBottomHandler = null; // Timer used for drag select scrolling
    function clearInetervals() {
      clearInterval(intTopHandler);
      clearInterval(intBottomHandler);
    }

    $("#bin").on('touchstart', '.transaction-row', function(e) {
      // Set up variables for touch events
      originalStates = [];
      $allTRows = $('.transaction-row'); 
      $allCheckboxes = $('.t-delete-checkbox');
      $scroller = $('#transactions-scroller .simplebar-content-wrapper'); // Store the JQuery object for the transactions scroller since it's not ready on document ready
      $allCheckboxes.each(function() {originalStates.push(this.checked)}); // Store the original state of the checkboxes
      $tRow = $(this).addClass('disable-select'); // Keeps the user from selecting/highlighting the text during a longpress
      startingTargetIndex = $allTRows.index($tRow);
      start_time = new Date().getTime();
      start_y = e.touches[0].clientY;
      start_x = e.touches[0].clientX;
      y = start_y;

      // Start the timer to determine if you're trying to select a transaction (longpress)
      longPressTimer = setTimeout(function(){
        if (!isSwipeScrolling) {
          
          // You are longpressing
          isDragSelecting = true;

          // Select the transaction you longpressed and update the variables related to multiselection
          $tRow.find('.t-delete-checkbox').click();
          lastChangedTargetIndex = startingTargetIndex;
          initialTargetIsChecked = $tRow.find(".t-delete-checkbox")[0].checked;
          $(window).bind("contextmenu", function(e) {e.preventDefault();} ); //Disable the context menu
        } else {
          clearTimeout(longPressTimer); //Disable the timer
        }
      }, longpressAmt)
    }).on('touchmove', '.transaction-row', function(e) {
      // 1. Update the y coordinate of your touch (declared in touchstart)
      y = e.touches[0].clientY;
      
      // 2. If your finger has moved more than 30px since the start of the touch event (and you're not in a longpress), you are swpipe scrolling
      if (Math.abs(start_y - y) > 30 && !isDragSelecting) {
        isSwipeScrolling = true;
      }
      
      if (isDragSelecting) {
        // 3. Toggle the transaction selection
        function toggleTransactionSelection(direction) {
          e.preventDefault(); //Prevents scrolling on longpress moves
          var $tRow = $(document.elementFromPoint(start_x,y)).closest(".transaction-row"); //Determine which transaction you're touching
          var currentTargetIndex = $allTRows.index($tRow); // Get the index of the transaction you're touching
          if (currentTargetIndex > -1) { //If you are actually touching a transaction, get the index you're touching and toggle the checkboxes with that method
            if (currentTargetIndex > lastChangedTargetIndex) { // Downward drag
              if (currentTargetIndex > startingTargetIndex) { // Downward drag from initially selected transaction
                // Set states of the checkboxes to the initial state at touchstart for all checkboxes between the last changed target and the new target
                $allCheckboxes.slice(lastChangedTargetIndex, currentTargetIndex+1).setCheckbox(initialTargetIsChecked);
              } else { // Downward drag after upward drag
                $allCheckboxes.slice(lastChangedTargetIndex, currentTargetIndex).each(function(i,e) {
                  $(e).setCheckbox(originalStates[i+lastChangedTargetIndex]); // Reset the checkbox states to their original state at touchstart
                });
              }
            }
            else if (currentTargetIndex < lastChangedTargetIndex) { // Upward drag
              if (currentTargetIndex < startingTargetIndex) { // Upward drag from initially selected transaction
                // Set states of the checkboxes to the initial state at touchstart for all checkboxes between the last changed target and the new target
                $allCheckboxes.slice(currentTargetIndex, lastChangedTargetIndex).setCheckbox(initialTargetIsChecked);
              } else { // Upward drag after downward drag
                $allCheckboxes.slice(currentTargetIndex+1, lastChangedTargetIndex+1).each(function(i,e) {
                  $(e).setCheckbox(originalStates[i+lastChangedTargetIndex]); // Reset the checkbox states to their original state at touchstart
                });
              }
            }
            if (currentTargetIndex > -1) {
              lastChangedTargetIndex = currentTargetIndex; // Keep track of which transaction's checkbox was last changed
            }
          } else { // If you aren't touching a transaction (i.e. you're above/below the scroller viewport) toggle the transaction(s) above/below your touch
            if (direction > 0) { // If scrolling UPWARD at top of the page
              //Get transaction above lastChangedTargetIndex (if there is one above it)
              if (lastChangedTargetIndex > 0) {
                var newTargetIndex = lastChangedTargetIndex - 1;
                var $newTarget = $($allTRows)[newTargetIndex];
                var topOfTarget = $newTarget.getBoundingClientRect().top; // Get the position of the top of the target
                var topOfScroller = $scroller[0].getBoundingClientRect().top; // Get the position of the top of the scroller
                if (topOfTarget < topOfScroller) { // If the target is below the top of the scroller, toggle it
                  if (newTargetIndex < startingTargetIndex) { // Upward drag from initially selected transaction
                    // Set states of the checkboxes to the initial state at touchstart for all checkboxes between the last changed target and the new target
                    $allCheckboxes.slice(newTargetIndex, lastChangedTargetIndex).setCheckbox(initialTargetIsChecked);
                  } else { // Upward drag after downward drag
                    $allCheckboxes.slice(newTargetIndex+1, lastChangedTargetIndex+1).each(function(i,e) {
                      $(e).setCheckbox(originalStates[i+lastChangedTargetIndex]); // Reset the checkbox states to their original state at touchstart
                    });
                  }
                }
                lastChangedTargetIndex = newTargetIndex;
              }
            } else if (direction < 0) { // If scrolling DOWNWARD at bottom of the page
              //Get transaction below lastChangedTargetIndex (if there is one below it)
              if (lastChangedTargetIndex < $allTRows.length-1) {
                var newTargetIndex = lastChangedTargetIndex + 1;
                var $newTarget = $($allTRows)[newTargetIndex];
                var bottomOfTarget = $newTarget.getBoundingClientRect().bottom; // Get the position of the bottom of thetransaction
                var bottomOfScroller = $scroller[0].getBoundingClientRect().bottom; // Get the position of the bottom of the scroller
                if (bottomOfTarget > bottomOfScroller) { // If the bottom of the transaction is above the bottom of the scroller, toggle it
                  if (newTargetIndex > startingTargetIndex) { // Downward drag from initially selected transaction
                    // Set states of the checkboxes to the initial state at touchstart for all checkboxes between the last changed target and the new target
                    $allCheckboxes.slice(lastChangedTargetIndex, newTargetIndex+1).setCheckbox(initialTargetIsChecked);
                  } else { // Downward drag after upward drag
                    $allCheckboxes.slice(lastChangedTargetIndex, newTargetIndex).each(function(i,e) {
                      $(e).setCheckbox(originalStates[i+lastChangedTargetIndex]); // Reset the checkbox states to their original state at touchstart
                    });
                  }
                }
                lastChangedTargetIndex = newTargetIndex;
              }
            }
          }
        }
        toggleTransactionSelection(0);

        // 4. Handle drag select scrolling
        isDragSelectScrolling = false;

        // 4.1 Determine if you're drag select scrolling DOWNWARD (i.e. your mouse is toward the bottom of the screen while you're drag selecting)
        if (y/window.innerHeight * 100 > 97) {
          isDragSelectScrolling = true;
          clearInetervals();
          intBottomHandler= setInterval(function(){
            var currentScrollTop = $scroller.scrollTop();
            $scroller.scrollTop(currentScrollTop + 2);
            toggleTransactionSelection(-1);
          },5);
        }

        // 4.2 Determine if you're drag select scrolling UPWARD (i.e. your mouse is toward the top of the scroller area while you're drag selecting)
        if ($scroller[0].getBoundingClientRect().top/y * 100 > 95 ) {
          isDragSelectScrolling = true;
          clearInetervals();
          intTopHandler= setInterval(function(){
            var currentScrollTop = $scroller.scrollTop();
            $scroller.scrollTop(currentScrollTop - 2);
            toggleTransactionSelection(1);
          },5);
        }

        // 4.3 If you're not drag select scrolling, clear the interval
        if (!isDragSelectScrolling) clearInetervals();
      }
    }).on('touchend', '.transaction-row', function(e) {
      // 0. Prevent click events or mouse events from firing (unless you're swiping, because by default they don't fire when you swipe)
      if (!isSwipeScrolling) {
        e.preventDefault();
      }
      // 1. Set all scrolling/selecting variables to false and clear timers
      isDragSelecting = false;
      isDragSelectScrolling = false;
      isSwipeScrolling = false;
      clearTimeout(longPressTimer);
      clearInetervals();

      // 2. Handle "touching" the transaction
      if ( new Date().getTime() < ( start_time + longpressAmt ) && Math.abs(start_y - y) < 30 ) { // If your touch was NOT a longpress
        // If you are in a multiselection (i.e. checkboxes are showing), toggle the checkbox, otherwise open the editor modal
        if (!none_checked) {
          $(this).find('.t-delete-checkbox').click();
        } else {
          $(this).children('.transaction').click();
        }
      } else { // If your touch WAS a longpress
        originalStates = null;
        multideleteToggleCheck();
        setTimeout(function() {$(window).unbind("contextmenu")}, 100); //Re-enable the context menu (only relevant when you switch from mobile inspection to normal inspection on Chrome)
      }

      // 3. Re-enable selecting/highlighting the text and open the editor modal
      $(this).removeClass('disable-select');
    });

    // Toggler code for transfer tab of transaction creator/editor
    $(document).on('change', '.div-toggle', function() {
      var target = $(this).data('target');
      var show = $("option:selected", this).data('show');
      $(target).children().addClass('hide');
      $(show).removeClass('hide');
      $selects = $(target).find('select').removeAttr('required'); // Remove the required attribute
      $selects.siblings(".select-dropdown").removeClass("invalid"); // Remove the invalid class from the dropdown
      $selects.parent().siblings(".helper-text").text(""); // Clear the error message
      $(target).find('select').removeAttr('required');
      $(show).find('select').attr('required', true);
    });

    // Envelope fill math n' stuff
    $('#envelope-fill-form').on("input", ".special-fill-input", function() {
      var $envelopeBalanceSpan = $(this).parent().siblings(".envelope-balance-col").find(".balance");
      var skip;
      var $currentInput = $(this);
      var original_balance = parseFloat($(this).data("original-balance"));

      // 1. Attempt to evaluate the expression in the input and update the envelope total span accordingly
      try {
        num = Math.round(math.evaluate($(this).val())*100)/100;
        if (!isNaN(num)) {
          $envelopeBalanceSpan.text(balance_format(original_balance + num)).negative_check(original_balance + num);
          $(this).removeClass("invalid").addClass("valid");
          skip = false; //Include this number when calculating the fill total
        } else {
          $envelopeBalanceSpan.text(balance_format(original_balance)).negative_check(original_balance);
          $(this).removeClass("valid").removeClass("invalid");
          skip = true; // DO NOT include this number when calculating the fill total
        }
      } catch (error) {
        $envelopeBalanceSpan.text(balance_format(original_balance)).negative_check(original_balance);
        $(this).removeClass("valid").addClass("invalid");
        skip = true; // DO NOT include this number when calculating the fill total
      }

      // 2. Iterate over the input fields to calculate the fill total
      fill_total = 0;
      $('#envelope-fill-form .special-fill-input').each(function(i) {
        if ($(this).is($currentInput)) { //If parsing the input that you are currently focused on
          if (!skip) {
            fill_total = fill_total + num; //Add the result of the parsed expression in the input to the fill total
          }
        } else {
          if (!isNaN(parseFloat($(this).val()))) { //If the input is not empty
            fill_total = fill_total + parseFloat($(this).val()); //Add the value of the input field to the fill total
          }
        }
      });

      // 3. Update the fill total span and the unallocated balance span
      unallocated_balance = parseFloat($('#unallocated-balance').data('amt'));
      $('#unallocated-balance-envelope-filler').text(balance_format(unallocated_balance - fill_total)).negative_check(unallocated_balance - fill_total);
      $('#fill-total').text(balance_format(fill_total)).negative_check(fill_total);
    }).on("change", ".special-fill-input", function() {
      try {
        num = math.evaluate($(this).val());
        if (!isNaN(num)) {
          $(this).val((Math.round(num * 100) / 100).toFixed(2)); //Replace the input text with the result of the parsed expression
        }
      } catch (error) {
        return;
      }
    });

    // Envelope fill editor math n' stuff
    $('#edit-envelope-fill-form').on("input",  ".special-fill-input", function() {
      var $envelopeBalanceSpan = $(this).parent().siblings(".envelope-balance-col").find(".balance");
      var original_fill_total =  parseFloat($('#edit-fill-total').data("original-fill-total"));
      var $currentInput = $(this);
      var prefill_balance = parseFloat($(this).data("prefill-balance"));
      var skip;

      // 1. Attempt to evaluate the expression in the input and update the envelope total span accordingly
      try {
        num = Math.round(math.evaluate($(this).val())*100)/100;
        if (!isNaN(num)) {
          $envelopeBalanceSpan.text(balance_format(prefill_balance + num)).negative_check(prefill_balance + num);
          $(this).removeClass("invalid").addClass("valid");
          skip = false; //Include this number when calculating the fill total
        } else {
          $envelopeBalanceSpan.text(balance_format(prefill_balance)).negative_check(prefill_balance);
          $(this).removeClass("valid").removeClass("invalid");
          skip = true; // DO NOT include this number when calculating the fill total
        }
      } catch (error) {
        $envelopeBalanceSpan.text(balance_format(prefill_balance)).negative_check(prefill_balance);
        $(this).removeClass("valid").addClass("invalid");
        skip = true; // DO NOT include this number when calculating the fill total
      }

      // 2. Iterate over the input fields to calculate the fill total
      fill_total = 0;
      $('#edit-envelope-fill-form .special-fill-input').each(function() {
        if ($(this).is($currentInput)) { //If parsing the input that you are currently focused on
          if (!skip) {
            fill_total = fill_total + num; //Add the result of the parsed expression in the input to the fill total
          }
        } else {
          if (!isNaN(parseFloat($(this).val()))) { //If the input is not empty
            fill_total = fill_total + parseFloat($(this).val()); //Add the value of the input field to the fill total
          }
        }
      });

      // 3. Update the fill total span and the unallocated balance span
      unallocated_balance = parseFloat($('#unallocated-balance').text().replace("$","")).toFixed(2);
      $('#edit-unallocated-balance-envelope-filler').text(balance_format(unallocated_balance - (fill_total-original_fill_total))).negative_check(unallocated_balance - (fill_total-original_fill_total));
      $('#edit-fill-total').text(balance_format(fill_total)).negative_check(fill_total);
    }).on("change", ".special-fill-input", function() {
      try {
        num = math.evaluate($(this).val());
        if (!isNaN(num)) {
          $(this).val((Math.round(num * 100) / 100).toFixed(2)); //Replace the input text with the result of the parsed expression
        }
      } catch (error) {
        return;
      }
    });

    // Adds envelope row for transaction creator and initializes Material Select
    $("#add-envelope").click(function() { 
      //Make a clone of the envelope select
      var $envelope_selector = $('#envelope-selector-row').find('select[name="envelope_id"]').clone();
      //Ensure that only the first option for "choose an envelope" has the select attribute
      $envelope_selector.find('option').each(function(){$(this).removeAttr('selected')});
      $envelope_selector.find('option').first().attr('selected','selected');
      //Add the envelope row without the select in it yet
      $('#envelopes-and-amounts').append(t_editor_new_env_row_html);
      //Add the select to the row, then initialize the select
      $(".addedEnvelope").last().prepend($envelope_selector).find("select").last().formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
    });

    // Adds envelope row for transaction editor and initializes Material Select
    $("#edit-add-envelope").click(function() {
      var $envelope_selector = $('#edit-envelope-selector-row').find('select[name="envelope_id"]').clone();
      $('#edit-envelopes-and-amounts').append(t_editor_new_env_row_html);
      $(".addedEnvelope").last().prepend($envelope_selector).find("select").last().formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
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
        if (o['error']) { M.toast({html: o['error']}); return; }
        $('#load-more').before(o['transactions'])
        if (o['limit']) {
          $('#load-more').remove()
        } else {
          $('#load-more').attr('data-offset', o['offset'])
        }
        refresh_reconcile()
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
    $('#bin').on( 'touchstart', '.transaction-row', function( e ) {
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
    }).on( 'mouseleave', '.transaction-row', function( e ) {
      start = 0;
      clearTimeout(timer);
    }).on( 'touchend', '.transaction-row', function( e ) {
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
      update_schedule_msg($(this));
    }).on('change', '.datepicker', function() {
      update_schedule_msg($(this).closest('form').find('.schedule-select'));
    });

    // Sets the example schedule text based on selected date and frequency
    function update_schedule_msg(schedule_select) {
      const months = ["Jan", "Feb", "Mar","Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      // const weekday = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
      var nextdate;
      var nextmonth;
      var nextyear;
      var getDaysInMonth = function(month,year) {
        return new Date(year, month+1, 0).getDate();
      };
      var option = schedule_select.val();
      $message = schedule_select.closest(".schedule-content").find(".schedule-message");
      var date_string = schedule_select.closest("form").find('.datepicker').val();
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
    function data_reload(current_page, should_reload_transactions_bin=true) {
      return $.ajax({
        type: "POST",
        url: "/api/data-reload",
        data: JSON.stringify({"current_page": current_page, "timestamp": gen_timestamp(), "should_reload_transactions_bin": should_reload_transactions_bin}),
        contentType: 'application/json'
      }).done(function( o ) {
        if (o['error']) { M.toast({html: o['error']}); return; }
        // 1. Reload the HTML
        $('#page-total').text(o['page_total']);
        $('#accounts-bin').replaceWith(o['accounts_html']);
        $('#envelopes-bin').replaceWith(o['envelopes_html']);
        $('#envelope-modal').replaceWith(o['envelope_editor_html']);
        $('#account-modal').replaceWith(o['account_editor_html']);
        $('#envelope-modal, #account-modal').modal();
        if (should_reload_transactions_bin) {
          $('#load-more').remove();
          $('#transactions-bin').replaceWith(o['transactions_html']);
          refresh_reconcile();
        }

        // 2. Update the total text
        $('#total span').text(balance_format(o['total'])).negative_check(o['total']);

        // 3. Update the unallocated balance text/data
        $('#unallocated span, #unallocated-balance-envelope-filler').attr('data-amt', o['unallocated']).data('amt', o['unallocated']).text(balance_format(o['unallocated'])).negative_check(o['unallocated']);

        // 4.1 Update selects in transaction editor
        expense_editor.appendTo('#editor-row');
        $('.select-wrapper:has(.account-selector) select').html(o['account_selector_html']);
        $('.select-wrapper:has(.envelope-selector) select').html(o['envelope_selector_html']);
        expense_editor.detach();

        // 4.2 Update selects in transfer editor
        transfer_editor.appendTo('#editor-row');
        $('.select-wrapper:has(.account-selector) select').html(o['account_selector_html']);
        $('.select-wrapper:has(.envelope-selector) select').html(o['envelope_selector_html']);
        $('#envelope-transfer-edit select').first().attr('name', 'from_envelope');
        $('#envelope-transfer-edit select').last().attr('name', 'to_envelope');
        $('#account-transfer-edit select').first().attr('name', 'from_account');
        $('#account-transfer-edit select').last().attr('name', 'to_account');
        transfer_editor.detach();

        // 4.3 Update selects in the income editor
        income_editor.appendTo('#editor-row');
        $('.select-wrapper:has(.account-selector) select').html(o['account_selector_html']);
        $('.select-wrapper:has(.envelope-selector) select').html(o['envelope_selector_html']);
        income_editor.detach()

        // 4.4 Re-initialize all selects
        $('select').formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});

        // 5. Update the envelope fill editor
        envelope_fill_editor.appendTo('#editor-row');
        $('.envelope-fill-editor-bin').replaceWith(o['envelope_fill_editor_rows_html']);
        $('#fill-total').text("$0.00").removeClass("negative");
        envelope_fill_editor.detach();

        //6. Re-enable the simplebar scrollers
        $('.scroller').each(function(index,el) {
          new SimpleBar(el);
        });

        // 7. Update the datepickers 
        $('.datepicker').datepicker('setDate', new Date());
        $('input[name="date"]').val((new Date()).toLocaleDateString("en-US", {day: '2-digit', month: '2-digit', year: 'numeric'}));

        // 8. Other functions
        budget_bars(); // Update the envelope budget bars
        envelope_and_account_editor_binds(); // Various event binds for the envelope/account editor modals
        editor_row_check(); //If there are no envelopes or accounts, ensure the message shows in the envelope/account editor
        M.updateTextFields(); //Ensure that text input labels don't overlap with filled text
      });
    };

    // Submits transaction EDITOR form data, closes the modal, clears the form, and reloads the data
    $('#edit-expense-form, #edit-transfer-form, #edit-income-form, #envelope-fill-form, #edit-envelope-fill-form, #edit-envelope-delete-form, #edit-account-delete-form, #edit-account-adjust-form').submit(function(e) {
      e.preventDefault()
      var url = $(this).attr('action');
      var method = $(this).attr('method');
      var $form = $(this);
      var $parentModal = $(this).closest('.modal');
      $.ajax({
        type: method,
        url: url,
        data: $(this).serialize() + "&timestamp=" + gen_timestamp() //Append a timestamp to the serialized form data
      }).done(function( o ) {
        if (o['error']) { M.toast({html: o['error']}); return; }
        $parentModal.modal("close");
        //Removes the new-envelope-row(s) from split transactions in the specific form so that the next time you open
        //the editor modal, they're not still there, while keeping the new-envelope-rows in the transaction creator modal
        $form.find('.new-envelope-row').remove(); //Only used on #new-expense-form
        $form[0].reset(); //Clears the data from the form fields
        data_reload(current_page);
        o['toasts'].forEach((toast) => M.toast({html: toast})); //Display toasts
      });
    });

    // --- Transaction creator form keybinds --- //
    // Ctrl+Enter submits and clears some
    // Ctrl+Shift+Enter submits and clears all
    $('#transaction-modal form').keydown(function(e) {
      if ((e.ctrlKey) && e.key === "Enter") {
        if ($(this)[0].checkValidity()) {
          if (!e.shiftKey) {
              e.preventDefault();
              $(this).data('remain-open', 1)
              $(this).trigger('submit');
          } else {
              e.preventDefault();
              $(this).data('remain-open', 2)
              $(this).trigger('submit');
          }
        }
      }
    });
    
    // Ctrl+Alt+Arrow toggles between tabs in transaction creator
    $("#transaction-modal").keydown(function(e) {
      if (e.ctrlKey && e.altKey && e.key == "ArrowLeft") {
        // Switch one tab to the left
        var tabs = M.Tabs.getInstance($('#type-tabs'));
        var tab_index = tabs.index;
        if (tab_index > 0) {
          $tab = $("#type-tabs").children(".tab").eq(tab_index - 1); // Get the next tab (<li> element)
          id = $tab.children("a").attr("href").substring(1); // The name of the id which the tab switches to
          $("#type-tabs").tabs("select", id); // Change to the next tab
          $("#" + id).find('form input[name="name"]').select(); // Select the name field
        }
      } else if (e.ctrlKey && e.altKey && e.key == "ArrowRight") {
        // Switch one tab to the right
        var tabs = M.Tabs.getInstance($('#type-tabs'));
        var tab_index = tabs.index;
        if (tab_index < 2) {
          $tab = $("#type-tabs").children(".tab").eq(tab_index + 1); // Get the next tab (<li> element)
          id = $tab.children("a").attr("href").substring(1); // The name of the id which the tab switches to
          $("#type-tabs").tabs("select", id); // Change to the next tab
          $("#" + id).find('form input[name="name"]').select(); // Select the name field
        }
      }
    });

    // Clear the "required" error message on the amount inputs in the transaction creator/editor modal when you start typing
    $("#transaction-modal input, #editor-modal input").on("invalid", function() {
      if ($(this).hasClass("special-input")) {
        $(this).siblings("span").removeClass("hidden"); // For special inputs (inline math), remove the hidden class to display the error message
      }
      $(this).addClass("invalid").removeClass("valid");
    }).on("input", function(e) {
      $(e.target).removeClass("invalid"); // As soon as you fill in the empty name input, remove the invalid class
      if ($(this).hasClass("special-input")) {
        $(this).siblings("span").addClass("hidden"); // For special inputs (inline math), add the hidden class to hide the error message
      }
    });

    // If you attempt to submit a form in the transaction creator/editor modal without selecting an envelope/account, display an error message
    $("#transaction-modal select, #editor-modal select").on("invalid", function() {
      $(this).siblings(".select-dropdown").addClass("invalid").removeClass("valid"); // Add invalid class to the select dropdown
      $(this).parent().siblings(".helper-text").text("Required"); // Show the error message for the select dropdown
    });

    // When you make a selection in the select dropdown, remove the invalid class and clear the error message
    $("#transaction-modal, #editor-modal").on("change", ".select-wrapper", function() {
      $(this).children(".select-dropdown").removeClass("invalid");
      $(this).siblings(".helper-text").text("");
    });

    // Submits transaction CREATOR form data, closes the modal, clears the form, and reloads the data
    $('#transaction-modal form').submit(function(e) {
      e.preventDefault()
      var url = $(this).attr('action');
      var method = $(this).attr('method');
      var remain_open = $(this).data('remain-open');
      var selected_date = $(this).find('input[name="date"]').val();
      var $form = $(this);
      var $envelope_selectors = $(this).find('.envelope-selector');
      var $account_selectors = $(this).find('.account-selector');
      var selected_envelopes = [];
      var selected_accounts = [];
      $envelope_selectors.each(function() {
        selected_envelopes.push($(this).val());
      });
      $account_selectors.each(function() {
        selected_accounts.push($(this).val());
      });

      $.ajax({
        type: method,
        url: url,
        data: $(this).serialize() + "&timestamp=" + gen_timestamp() //Append a timestamp to the serialized form data
      }).done(function( o ) {
        if (o['success']) {
          if (remain_open == 1) { // RESET NAME FIELD, STAY OPEN
            // If the form was submitted with the submit and new button
            $('#transaction-modal form').data('remain-open',0) //Reset the remain-open attribute
            data_reload(current_page).then( function () {

              //Clear the transaction name field
              $form.find('input[name="name"]').val("").select().removeClass('valid');

              //Remove the valid class from the amount
              $form.find('input[name="amount"]').removeClass('valid');

              //Fill the date field
              $form.find('input[name="date"]').val(selected_date);
              $form.find('.datepicker').datepicker('setDate', new Date(selected_date));

              //Select the previously selected envelopes and their respective dropdowns
              $envelope_selectors.each(function(index) {
                $(this).find('option[value=' + selected_envelopes[index] + ']').attr('selected', 'selected');
                $(this).formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
              });
              //Select the previously selected account in its dropdown
              $account_selectors.each(function(index) {
                $(this).find('option[value=' + selected_accounts[index] + ']').attr('selected', 'selected');
                $(this).formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
              });

            });
          }
          else if (remain_open == 2) { // RESET ALL FIELDS, STAY OPEN
            $('#transaction-modal form').data('remain-open',0) //Reset the remain-open attribute
            $form.find(".new-envelope-row").remove(); //Only used on #new-expense-form
            $form[0].reset(); //Clear the data from the form fields
            data_reload(current_page).then( function () {
              $form.find(".schedule-content").hide();
              update_schedule_msg($form.find('.schedule-select')); //Reset the scheduled message
              $form.find('input[name="name"]').select();
            });
          }
          else { // RESET ALL FIELDS AND CLOSE
            // If the form was submitted with the standard submit button or enter
            $('#transaction-modal').modal("close")
            $form.find(".new-envelope-row").remove() //Only used on #new-expense-form
            $form[0].reset(); //Clear the data from the form fields
            $form.find(".amount-span").text("$0.00").removeClass("negative").addClass("neutral");
            data_reload(current_page).then( function () {
              $form.find(".schedule-content").hide();
              update_schedule_msg($form.find('.schedule-select')); //Reset the scheduled message
            });
          }
        } else {
          if (o.errors) {displayFieldErrors(o.errors);}
        }
        if (o['toasts']) { o['toasts'].forEach((toast) => M.toast({html: toast})); } //Display toasts
      });
    });

    //Check the form validity, change the remain-open attribute to '1', then submit the form
    $('.submit-and-new').click(function(event) {
      if (event.ctrlKey) {
        $(this).closest("form").data("remain-open",2);
      } else {
        $(this).closest("form").data("remain-open",1);
      }
    });

    //Check the form validity, change the remain-open attribute to '1', then submit the form
    $('.standard-submit').click(function() {
        $(this).closest("form").data("remain-open",0);
    });

    // Delete a transaction from 
    $('.deleter-form').submit(function(e) {
      e.preventDefault();
      var url = $(this).attr('action');
      var method = $(this).attr('method');
      var $parentModal = $(this).closest('.modal');
      var dtid = $("#dtid").val();
      var ttype = $("#ttype").val();

      $.ajax({
        type: method,
        url: url,
        data: $(this).serialize() + "&timestamp=" + gen_timestamp() //Append a timestamp to the serialized form data
      }).done(function( o ) {
        if (o['error']) { M.toast({html: o['error']}); return; }
        $parentModal.modal("close");
        $parentModal.find(".new-envelope-row").remove(); //Removes the new-envelope-row(s) from split transactions
        should_reload_transactions_bin = false; //Typically when deleting a transaction, you don't need to refresh every transaction in the displayl bin, because the reconcile balances will be updated after the data_reload, and that's all that typically needs changing
        if (ttype == ENVELOPE_DELETE || ttype == ACCOUNT_DELETE) {
          should_reload_transactions_bin = true; // If you delete an envelope or account, reload the transactions bin to refresh the strikethrough displays of the transaction envelope/account
        }
          data_reload(current_page, should_reload_transactions_bin).then(function() {
          $(`.transaction[data-id='${dtid}']`).parent().animate({height: "0px"}, 250).promise().done(function() {
            $(`.transaction[data-id='${dtid}']`).parent().remove();
            $(".date-bucket").show();
            $('.checkbox-bucket').hide();
            refresh_reconcile();
            o['toasts'].forEach((toast) => M.toast({html: toast})); //Display toasts
          })
        });
      });
    });

    $("#multi-delete-form").submit(function(e) {
      e.preventDefault();
      var url = $(this).attr('action');
      var method = $(this).attr('method');

      $.ajax({
        type: method,
        url: url,
        data: $(this).serialize() + "&timestamp=" + gen_timestamp() //Append a timestamp to the serialized form data
      }).done(function( o ) {
        if (o['error']) { M.toast({html: o['error']}); return; }
        $("#multi-select-col").hide();
        none_checked = true;
        data_reload(current_page, false).then(function() {

          // 1. Update the data offset
          num_deleted = $(".t-delete-checkbox:checked").length
          original_offset = $("#load-more").attr('data-offset');
          $("#load-more").attr('data-offset', parseInt(original_offset) - num_deleted);

          // 2. Remove the deleted transactions rows
          $(".t-delete-checkbox:checked").closest(".transaction-row").animate({height: "0px"}, 250).promise().done(function() {
            $(".t-delete-checkbox:checked").closest(".transaction-row").remove();
            $(".date-bucket").show();
            $('.checkbox-bucket').hide();
            refresh_reconcile();
            o['toasts'].forEach((toast) => M.toast({html: toast})); //Display toasts
          });

        });
      });
    });

    // Opens transaction editor modal
    function t_editor_modal_open(e) {
      // gets and formats data from html data tags
      var id = e.data('id');
      var name = e.data('name');
      var type = e.data('type');
      var date = e.data('date');
      var envelope_id = e.data('envelope_id');
      var account_id = e.data('account_id');
      var grouping = e.data('grouping');
      var note = e.data('note');
      var amt = -1 * parseFloat(e.data('amt'));
      var to_envelope = null;
      var from_envelope = null;
      var schedule = e.data('schedule');
      var pending = e.data('pending');
      // var envelope_name = e.data('envelope_name'); // PLACEHOLDER: NOT USED IN THE FORM, JUST FOR DISPLAYING IN .transaction
      // var account_name = e.data('account_name');   // PLACEHOLDER: NOT USED IN THE FORM, JUST FOR DISPLAYING IN .transaction
      // var status = e.data('status');               // PLACEHOLDER: UNUSED DATABASE FIELD
      var $checkbox_input;

      //if it's a grouped transaction, use ajax to get data from all grouped transaction
      if (grouping != null) {
        $.ajax({
          async: false,
          type: "GET",
          url: "/api/transaction/" + id + "/group",
        }).done(function( o ) {
          if (o['error']) { M.toast({html: o['error']}); return; }
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

      // Check which editor to show, detatch the others, update the special fields, and define $checkbox_input
      if (type == BASIC_TRANSACTION ) {
        expense_editor.appendTo('#editor-row');
        $("#edit-transfer").detach();
        $("#edit-income").detach();
        $("#edit-envelope-fill").detach();
        $("#edit-account-delete").detach();
        $("#edit-envelope-delete").detach();
        $("#edit-account-adjust").detach()
        $checkbox_input = $('#edit-expense-schedule');
        $("#edit-amount").val(amt.toFixed(2));
        $('#edit-envelope_id').val(envelope_id).formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
        $('#edit-account_id').val(account_id).formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
      } else if (type == ENVELOPE_TRANSFER || type == ACCOUNT_TRANSFER) {
        transfer_editor.appendTo('#editor-row');
        $("#edit-expense").detach();
        $("#edit-income").detach();
        $("#edit-envelope-fill").detach();
        $("#edit-account-delete").detach();
        $("#edit-envelope-delete").detach();
        $("#edit-account-adjust").detach()
        // Fill in the amount field
        $('#edit-transfer_type').val(type).formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
        $("#edit-amount").val(Math.abs(amt).toFixed(2));
        if (type == ENVELOPE_TRANSFER) {
          $('#account-transfer-edit').addClass('hide');
          $('#envelope-transfer-edit').removeClass('hide');
          $('#account-transfer-edit').find('select').removeAttr('required');
          $('#envelope-transfer-edit').find('select').attr('required', true);
          $('#edit-from_envelope').val(from_envelope).formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
          $('#edit-to_envelope').val(to_envelope).formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
        } else if (type == ACCOUNT_TRANSFER) {
          $('#envelope-transfer-edit').addClass('hide');
          $('#account-transfer-edit').removeClass('hide');
          $('#envelope-transfer-edit').find('select').removeAttr('required');
          $('#account-transfer-edit').find('select').attr('required', true);
          $('#edit-to_account').val(to_account).formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
          $('#edit-from_account').val(from_account).formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
        }
        $checkbox_input = $('#edit-transfer-schedule');
      } else if (type == INCOME) {
        income_editor.appendTo('#editor-row');
        $("#edit-expense").detach();
        $("#edit-transfer").detach();
        $("#edit-envelope-fill").detach();
        $("#edit-account-delete").detach();
        $("#edit-envelope-delete").detach();
        $("#edit-account-adjust").detach()
        $('#edit-envelope_id').val(envelope_id).formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
        $('#edit-account_id').val(account_id).formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
        $("#edit-amount").val((-1*amt).toFixed(2));
        $checkbox_input = $('#edit-income-schedule');
      } else if (type == SPLIT_TRANSACTION) {
        expense_editor.appendTo('#editor-row');
        $("#edit-transfer").detach();
        $("#edit-income").detach();
        $("#edit-envelope-fill").detach();
        $("#edit-account-delete").detach();
        $("#edit-envelope-delete").detach();
        $("#edit-account-adjust").detach()
        $("#edit-amount").val(amt.toFixed(2));
        $('#edit-envelope_id').val(envelope_id).formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
        $('#edit-account_id').val(account_id).formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
        for (i=1 ; i<envelope_ids.length ; i++) {
          var $envelope_selector = $('#edit-envelope-selector-row').find('select[name="envelope_id"]').clone();
          $('#edit-envelopes-and-amounts').append(t_editor_new_env_row_html);
          $(".new-envelope-row").last().find("input[name='amount']").attr("value", amounts[i].toFixed(2));
          $(".addedEnvelope").last().prepend($envelope_selector).find("select").last().val(envelope_ids[i]).formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
        }
        $checkbox_input = $('#edit-expense-schedule');
      } else if (type == ENVELOPE_FILL) {
        envelope_fill_editor.appendTo('#editor-row');
        $("#edit-transfer").detach();
        $("#edit-income").detach();
        $("#edit-expense").detach();
        $("#edit-account-delete").detach();
        $("#edit-envelope-delete").detach();
        $("#edit-account-adjust").detach()
        // Fills input fields
        var $inputs = $('#edit-envelope-fill-form .special-fill-input');
        var fill_total = 0;
        $inputs.each(function() {
          $(this).val("");
          var original_balance = parseFloat($(this).data("original-balance"));
          // this code exists so that if you change a value, close the editor,
          // then reopen it, the envelope balances will always be correct
          var $span = $(this).parent().siblings(".envelope-balance-col").find(".balance");
          $span.text(balance_format(original_balance)).negative_check(original_balance);
          // Fills input fields and adds up the fill total
          if (envelope_ids.includes($(this).data("envelope-id"))) {
            var amt = amounts[envelope_ids.indexOf($(this).data("envelope-id"))];
            $(this).val(amt.toFixed(2)).attr("data-prefill-balance", original_balance - amt); //Set the value in the input and update the metadata
            fill_total = fill_total + amt;
          } else {
            $(this).attr("data-prefill-balance", original_balance); //Set the value in the input and update the metadata
          }
        });
        $('#edit-fill-total').text(balance_format(fill_total)).negative_check(parseFloat(fill_total));
        $('#edit-fill-total').data("original-fill-total", fill_total);
        unallocated_balance = parseFloat($('#unallocated-balance').data('amt'));
        $('#edit-unallocated-balance-envelope-filler').text(balance_format(parseFloat(unallocated_balance))).negative_check(unallocated_balance)
        $checkbox_input = $('#edit-envelope-fill-schedule');
      } else if (type == ENVELOPE_DELETE) {
        envelope_restore.appendTo('#editor-row');
        $("#edit-account-delete").detach();
        $("#edit-expense").detach();
        $("#edit-transfer").detach();
        $("#edit-income").detach();
        $("#edit-envelope-fill").detach();
        $("#edit-account-adjust").detach()
        $("#edit-amount").text(balance_format(-1*amt)).negative_check(-1*amt);
        $("#edit-envelope-delete-id").val(envelope_id)
        $("#noneditable-date").val(date);
      } else if (type == ACCOUNT_DELETE) {
        account_restore.appendTo('#editor-row');
        $("#edit-expense").detach();
        $("#edit-income").detach();
        $("#edit-transfer").detach();
        $("#edit-envelope-fill").detach();
        $("#edit-envelope-delete").detach();
        $("#edit-account-adjust").detach()
        $("#edit-amount").text(balance_format(-1*amt)).negative_check(-1*amt);
        $("#edit-account-delete-id").val(account_id)
        $("#noneditable-date").val(date);
      } else if (type == ACCOUNT_ADJUST) {
        account_adjust.appendTo('#editor-row');
        $("#edit-expense").detach();
        $("#edit-income").detach();
        $("#edit-transfer").detach();
        $("#edit-envelope-fill").detach();
        $("#edit-account-delete").detach();
        $("#edit-envelope-delete").detach();
        $("#edit-amount").val((-1*amt).toFixed(2));
        $("#edit-account-adjust-id").val(account_id)
      }

      // Update the rest of the common fields
      $("#edit-date").val(date);
      $('#edit-date').datepicker('setDate', new Date(date));
      $("#edit-name").val(name);
      $("#edit-note").val(note);
      $('#dtid').attr('value', id);
      $('#ttype').attr('value', type);
      $('#edit-id').attr('value', id);
      $('#type').attr('value', type); //Possibly change this to a less confusing ID

      //Logic for whether or not schedule checkbox/info shows or is disabled
      if (type != ENVELOPE_DELETE && type != ACCOUNT_DELETE && type != ACCOUNT_ADJUST) {
        var $checkbox_span = $checkbox_input.siblings();
        if (pending == '0') { // Disable the checkbox, hide schedule content
          if ($checkbox_input.is(':checked')) {
            $checkbox_span.click(); // Uncheck box if it is checked
          }
          $checkbox_input.attr('disabled', 'disabled');
          $('#editor-modal .schedule-content').hide();
        } else { // Ensure checkbox is NOT disabled
          $checkbox_input.removeAttr('disabled');
          if (schedule == 'None') {
            if ($checkbox_input.is(':checked')) {
              $checkbox_span.click(); // Uncheck box if it is checked
            }
            $('#editor-modal .schedule-content').hide();
          } else {
            $('#edit-schedule').val(schedule).formSelect({dropdownOptions: {container: '#fullscreen-wrapper'}});
            update_schedule_msg($('#edit-schedule'));
            if (!($checkbox_input.is(':checked'))) {
              $checkbox_span.click(); //Check the box if it's not already checked
            }
          }
        }
      }

      
      M.updateTextFields();
      $("#editor-modal .special-input").trigger("input"); //Update the amount spans by triggering the "input" event
      $('#editor-modal').modal('open');
    }; // End of t_editor_modal_open

  });
})(jQuery); // end of jQuery name space
