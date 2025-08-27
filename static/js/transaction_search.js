window.Budgeteer = window.Budgeteer || {};
Budgeteer.previous_page = null; // Used to store the previous page before a search
Budgeteer.only_clear_searchfield = true; // Defines the behavior of the "X" icon in the searchfield. If true, it only clears the search field, otherwise it returns to page you were on before the search
Budgeteer.current_search = {}; // Used to store the current search parameters. Set when a valid search is performed.Used in data-reload, load-more functions

$(document).ready(function() {

  $("#transaction-search-form").on("submit", function(e) {
    e.preventDefault();

    // If there are front-end validation errors, display them and don't execute a search
    if (!$(this)[0].checkValidity()) { $(this)[0].reportValidity(); return;}

    // If every field is empty, don't execute a search
    if (isFormCompletelyEmpty($(this))) { return; }

    // Get the form action and method
    var url = $(this).attr('action');
    var method = $(this).attr('method');

    // Execute the search
    $.ajax({
      url: url,
      method: method,
      data: $(this).serialize() + "&timestamp=" + gen_timestamp(),
    }).done(function(o) {
      if (o.error) {M.toast({html: o.error}); return;}
      if (o.field_errors) {displayFieldErrors(o.field_errors); return;}
      
      $('#transactions-bin').replaceWith(o.transactions_html);
      if ($("#transactions-scroller").length !== 0) { new SimpleBar($("#transactions-scroller")[0]); }
      $('#current-page').text(o.current_page);
      $("#page-total").hide();
      $("#separator").hide();
      Budgeteer.showMultiSelectIcons(false);

      //Update the global variables
      Budgeteer.none_checked = true;
      Budgeteer.only_clear_searchfield = false; // Set the behavior of the "X" icon when clicked to return to previous page rather than only clearing the search fields
      Budgeteer.current_search = {
        searchTerm: $("#transaction-search").val().trim(),
        searchAmtMin: $("#search_amt_min").val().trim(),
        searchAmtMax: $("#search_amt_max").val().trim(),
        searchDateMin: $("#search_date_min").val().trim(),
        searchDateMax: $("#search_date_max").val().trim(),
        searchEnvelopeIds: $("#search_envelope_ids").val(),
        searchAccountIds: $("#search_account_ids").val()
      };
      if (Budgeteer.current_page != "Search results") { //Update the previous and current page unless you're entering a new search from a search results page,
        Budgeteer.previous_page = Budgeteer.current_page;
        Budgeteer.current_page = "Search results";
      }
      if (o.toasts) { o.toasts.forEach((toast) => M.toast({html: toast})); }
    });

  });

  $('#transaction-search-form').on('blur', 'input', function(){
    // On blur show syntactic browser validation messages
    var field = this;
    var $f = $(field);
    var $helper = $f.siblings('.helper-text');
    if (!$helper.length) $helper = $f.parent().find('.helper-text').first();
    if (field.checkValidity && !field.checkValidity()) {
      $f.removeClass('valid').addClass('invalid');
    }
  }).on('change', 'input', function(){
    // On change, clear error messages since the user is actively editing
    var $f = $(this);
    var $helper = $f.siblings('.helper-text');
    if (!$helper.length) $helper = $f.parent().find('.helper-text').first();
    $helper.removeAttr('data-server-error');
    if ($f.hasClass('invalid')) $f.removeClass('invalid');

    // If the form is NOT completely empty, show the clear button
    if (isFormCompletelyEmpty($('#transaction-search-form')) && Budgeteer.current_page != "Search results") {
      $('#clear-search').fadeOut(200, function() {
        $(this).css({"pointer-events": "none"}).attr("tabindex", "-1");
      });
    } else {
      $('#clear-search').css({"pointer-events": "auto", "display": "inline-block"}).attr("tabindex", "0");
    }
  }).on('change', 'select', function(){
    if (isFormCompletelyEmpty($('#transaction-search-form')) && Budgeteer.current_page != "Search results") {
      $('#clear-search').fadeOut(200, function() {
        $(this).css({"pointer-events": "none"}).attr("tabindex", "-1");
      });
    } else {
      $('#clear-search').css({"pointer-events": "auto", "display": "inline-block"}).attr("tabindex", "0");
    }
  }).on('input', 'input', function(){
    if (isFormCompletelyEmpty($('#transaction-search-form')) && Budgeteer.current_page != "Search results") {
      $('#clear-search').fadeOut(200, function() {
        $(this).css({"pointer-events": "none"}).attr("tabindex", "-1");
      });
    } else {
      $('#clear-search').css({"pointer-events": "auto", "display": "inline-block"}).attr("tabindex", "0");
    }
  });

  function clearSearch() {
    $("#clear-search").fadeOut(200); // Fade out the close button
    Budgeteer.current_search = {}; // Reset the global variable used to store the current search term

    // Clear all the fields in the advanced search bar
    $("#transaction-search-form").trigger("reset");

    // Reset all envelope/account select checkboxes in search dropdowns to unchecked
    $('#search_envelope_ids, #search_account_ids').each(function() {
      const $select = $(this);
      const $input = $select.siblings('input.select-dropdown');
      const $ul = $('#' + $input.attr('data-target'));
      $ul.find('input[type="checkbox"]').each(function() {
        if ($(this).prop('checked')) {
          $(this).parent().parent().parent().click(); // Click the li element to uncheck/unselect the checkbox
        }
      });
    });

    // Reset the labels
    M.updateTextFields();

    if (Budgeteer.only_clear_searchfield) return;

    // Return to the page you were on before you started the search
    $.ajax({
      type: 'POST',
      url: '/api/reset-search',
      data: JSON.stringify({"previous_page": Budgeteer.previous_page, "timestamp": gen_timestamp()}),
      contentType: 'application/json'
    }).done(function(o) {
      if (o['error']) { M.toast({html: o['error']}); return; }
      $('#transactions-bin').replaceWith(o['transactions_html']);
      if ($("#transactions-scroller").length !== 0) { new SimpleBar($("#transactions-scroller")[0]) } //Re-initialize the transactions-scroller if the envelope has transactions
      $('#current-page').text(o['current_page']);
      $("#separator").show();
      $('#page-total').text(o['page_total']).show();
      refresh_reconcile();
      Budgeteer.none_checked = true;
      Budgeteer.only_clear_searchfield = true;
      Budgeteer.showMultiSelectIcons(false);
    });
  }

  $("#clear-search").on('pointerdown', function(e) {
    if (e.pointerType === 'mouse' && e.button !== 0) return; //Don't trigger on right-click
    e.preventDefault();
    clearSearch();
  }).on('keydown', function(e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      clearSearch();
    }
  });

  // Show/hide the advanced search fields when the advanced search dropdown arrow is clicked
  $("#advanced-search-button").on('click', toggleAdvancedSearch).on('keydown', function(e) {
    if (e.key === "Enter") {
      toggleAdvancedSearch();
    }
  });


}); // End document ready

// Function for toggling the advanced search bar
function toggleAdvancedSearch() {
  if ($("#dashboard-header").hasClass("collapsed")) {
    // If the header is collapsed, expand it
    var currentDashHeight = $('#dashboard-header').height();
    var currentBinHeight = $("#bin").height();
    $('#dashboard-header').css('height', 'auto');
    var newDashHeight = $('#dashboard-header').height();
    $("#bin").css("height", "calc(100% - " + newDashHeight + "px)");
    var newBinHeight = $("#bin").height();
    $('#dashboard-header').height(currentDashHeight);
    $('#bin').height(currentBinHeight);
    $("#dashboard-header").animate({height: newDashHeight}, 200);
    $("#bin").animate({height: newBinHeight}, 200);
    $("#dashboard-header, #advanced-search-button").removeClass("collapsed").addClass("expanded");

    // Adjust the tabselect attribute for all the inputs to make them selectable
    $('#advanced-search-row input, #advanced-search-row button').each(function() {
      $(this).attr('tabindex', '0'); // Make them focusable
    });

  } else {
    // If the header is expanded, collapse it
    var currentBinHeight = $("#bin").height();
    $("#bin").css("height", "calc(100% - 90px)");
    var newBinHeight = $("#bin").height();
    $('#bin').height(currentBinHeight);
    $("#dashboard-header").animate({height: '90px'}, 200);
    $("#bin").animate({height: newBinHeight}, 200);
    $("#dashboard-header, #advanced-search-button").removeClass("expanded").addClass("collapsed");
  
    // Adjust the tabselect attribute for all the inputs to make them non-selectable
    $('#advanced-search-row input, #advanced-search-row button').each(function() {
      $(this).attr('tabindex', '-1'); // Make them non-focusable
    });
  }
}

// Function for initializing the special envelope/account select elements in the advanced-search row
// NOTE: If you ever use more multi-selects across the app, most of the logic in this function is dedicated to keyboard navigation
//       so this will likely need to be broken out into a new generalized function
Budgeteer.initializeSpecialSelects = function() {

  // 1. Initialize the selects (re-init safe)
  $('#search_envelope_ids, #search_account_ids').formSelect({
    dropdownOptions: {
      container: '#dashboard-column',
      onOpenStart: function(triggerEl) {
        // triggerEl is the input that launched the dropdown
        const $trigger = $(triggerEl);
        const ulId = $trigger.attr('data-target');
        const $ul = $('#' + ulId);
        if (!$ul.length) return;

        // Remove any prior key handlers (avoid duplicates if re-opened)
        $ul.off('.advKeys');

        // Get selectable items (exclude optgroup headers & disabled)
        const $items = $ul.find('li:not(.optgroup):not(.disabled)');
        if (!$items.length) return;

        // Make all items focusable (tabindex) so focus() works reliably
        $items.attr('tabindex', 0);

        // Clear previous "active/hovered" classes Materialize may have left
        $items.removeClass('active hovered');

        // Key handling inside dropdown list
        $ul.on('keydown.advKeys', function(e) {
          const $list = $(this);
            const $all = $list.find('li:not(.optgroup):not(.disabled)');
          if (!$all.length) return;

          // Determine current index (by active/hovered/focus)
          let idx = $all.index($all.filter('.active.hovered').first());
          if (idx < 0) idx = $all.index($all.filter('.active').first());
          if (idx < 0) idx = $all.index($all.filter(':focus').first());
          if (idx < 0) idx = 0;

          // Helper to update visual focus
          function setIndex(newIdx) {
            newIdx = Math.max(0, Math.min($all.length - 1, newIdx));
            $all.removeClass('active hovered');
            const $target = $all.eq(newIdx);
            $target.addClass('active hovered').focus();
          }

          // Navigation: Down / Up
          if (e.key === 'ArrowDown') {
            e.preventDefault(); e.stopImmediatePropagation();
            setIndex(idx + 1);
            return;
          } else if (e.key === 'ArrowUp') {
            e.preventDefault(); e.stopImmediatePropagation();
            setIndex(idx - 1);
            return;
          }

          // When enter key is pressed, select the dropdown item
          if (e.key === 'Enter') {
            e.preventDefault(); e.stopImmediatePropagation();
            const $targetLi = $all.eq(idx);
            // Simulate click which Materialize listens for
            $targetLi.trigger('mousedown').trigger('click');
            // Keep focus on same item for multi-select continued navigation
            setTimeout(() => $targetLi.focus(), 0);
            return;
          }

          // When Tab, Shift+Tab, Left, Right keys pressed, close dropdown and move to next/prev input
          if ((e.key === 'Tab' && !e.shiftKey) || e.key === 'ArrowRight') {
            e.preventDefault(); e.stopImmediatePropagation();
            focusSiblingInputFromDropdown($list, 'next');
            return;
          } else if ((e.key === 'Tab' && e.shiftKey) || e.key === 'ArrowLeft') {
            e.preventDefault(); e.stopImmediatePropagation();
            focusSiblingInputFromDropdown($list, 'prev');
            return;
          }

          // When escape key pressed, close dropdown, return focus to trigger element
          if (e.key === 'Escape') {
            closeDropdownReturnTrigger($list);
            return;
          }

        });
      }
    }
  });

  // 2.1 - Add custom style to dropdown to make envelope/account selections thinner/smaller
  // 2.2 - Override the onOpenEnd function for the select dropdown to manually set focus
  $('#search_envelope_ids, #search_account_ids').each(function() {
    const $select = $(this);
    const $input = $select.siblings('input.select-dropdown');
    const $ul = $('#' + $input.attr('data-target'));

    // 2.1 - Add custom styles
    $ul.addClass('custom-dropdown-class');
    $input.attr('tabindex', '-1');

    // NEW: Track how the dropdown was opened
    $input.data('openByKeyboard', false);
    $input.on('keydown', function(e) {
      if (['Enter', 'ArrowDown'].includes(e.key)) {
        // Mark that the imminent open (triggered by this key) is keyboard initiated
        $input.data('openByKeyboard', true);
      }
    }).on('mousedown touchstart', function() {
      // Explicitly mark mouse/touch initiated open
      $input.data('openByKeyboard', false);
    });

    // 2.2 - Override the onOpenEnd dropdown function (conditionally apply custom focus)
    const selectEl = this;
    const fs = M.FormSelect.getInstance(selectEl);
    if (!fs || !fs.dropdown || fs._firstItemFocusPatched) return;

    const dd = fs.dropdown;
    const originalOnOpenEnd = dd.options.onOpenEnd; // Materialize's injected handler

    dd.options.onOpenEnd = function(el) {
      // Run original behavior first
      if (typeof originalOnOpenEnd === 'function') {
        originalOnOpenEnd.call(this, el);
      }

      // Only apply custom focus if opened via keyboard
      const openedByKeyboard = $input.data('openByKeyboard');
      // Reset flag for next time
      $input.data('openByKeyboard', false);
      if (!openedByKeyboard) return;

      // Custom focus logic (was always applied before; now conditional)
      const $ul = $(fs.dropdownOptions);
      const $items = $ul.find('li:not(.optgroup):not(.disabled)');
      if (!$items.length) return;

      $items.attr('tabindex', 0);
      $ul.find('li').removeClass('active hovered');

      const $first = $items.first().addClass('active hovered');
      fs.dropdown.focusedIndex = $first.index();
      $first[0].focus();
    };

    fs._firstItemFocusPatched = true;
  });

  // --- Helper Functions ---

  // Close dropdown & return focus to trigger input
  function closeDropdownReturnTrigger($ul) {
    const ulId = $ul.attr('id');
    const $trigger = $('input.select-dropdown[data-target="' + ulId + '"]');
    const selectEl = $trigger.siblings('select')[0];
    const fs = M.FormSelect.getInstance(selectEl);
    if (fs?.dropdown?.isOpen) fs.dropdown.close();
    $trigger.focus();
  }

  // Move focus to prev/next tabbable in advanced-search row
  function focusSiblingInputFromDropdown($ul, direction /* 'next' | 'prev' */) {
    const ulId = $ul.attr('id');
    const $trigger = $('input.select-dropdown[data-target="' + ulId + '"]');
    const selectEl = $trigger.siblings('select')[0];
    const fs = M.FormSelect.getInstance(selectEl);
    if (fs?.dropdown?.isOpen) fs.dropdown.close();

    focusSiblingInputFromTrigger($trigger, direction);
  }

  function focusSiblingInputFromTrigger($trigger, direction) {
    const $scope = $('#advanced-search-row');
    const $tabbables = $scope
      .find('input, select, button, textarea, a, [tabindex]:not([tabindex="-1"])')
      .filter(':visible:not([disabled])');
    const idx = $tabbables.index($trigger);
    if (idx < 0) return;
    const targetIdx = direction === 'prev'
      ? Math.max(0, idx - 1)
      : Math.min($tabbables.length - 1, idx + 1);
    $tabbables.eq(targetIdx).focus();
  }
};

function isFormCompletelyEmpty($form, opts) {
  opts = opts || {};
  var exclude = opts.excludeSelector || 'input[type="hidden"], input[type="submit"], button, .ignore-empty';

  var empty = true;
  $form.find('input, textarea, select').not(exclude).each(function() {
    var $el = $(this);
    var tag = this.tagName.toLowerCase();
    var type = ($el.attr('type') || '').toLowerCase();

    if (type === 'checkbox' || type === 'radio') {
      if ($el.is(':checked')) { empty = false; return false; }
      return; // next
    }

    if (type === 'file') {
      if (this.files && this.files.length) { empty = false; return false; }
      return;
    }

    if (tag === 'select') {
      var val = $el.val();
      if (Array.isArray(val) ? val.length > 0 : (val !== null && String(val).trim() !== '')) {
        empty = false; return false;
      }
      return;
    }

    // text-like inputs & textarea
    var v = $el.val();
    if (v !== null && String(v).trim() !== '') { empty = false; return false; }
  });

  return empty;
}